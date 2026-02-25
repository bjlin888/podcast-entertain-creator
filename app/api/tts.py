from __future__ import annotations

import logging
from pathlib import PurePosixPath
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File

from app.api.deps import get_user_id
from app.api.rate_limit import _limiter
from app.db import get_db, get_current_script, get_segment, get_segments_by_script
from app.models import TTSMultiSpeakerRequest, TTSRequest
from app.tts.audio_storage import get_audio_url, save_audio
from app.tts.tts_service import synthesize, synthesize_multi_speaker

logger = logging.getLogger(__name__)

router = APIRouter(tags=["tts"])

MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {".wav", ".mp3", ".m4a", ".ogg", ".webm"}


@router.post("/scripts/segments/{segment_id}/tts")
async def generate_tts(
    segment_id: str,
    body: TTSRequest,
    user_id: str = Depends(get_user_id),
):
    """Generate TTS audio for a segment."""
    _limiter.check(f"{user_id}:tts", max_calls=20, window_seconds=60)

    logger.info("TTS request: provider=%s, voice=%s, style=%s", body.tts_provider, body.voice, body.style_prompt)
    async with get_db() as db:
        segment = await get_segment(db, segment_id)
        if not segment:
            raise HTTPException(status_code=404, detail="Segment not found")

        # Verify ownership
        cursor = await db.execute(
            """SELECT p.user_id FROM projects p
               JOIN scripts s ON p.project_id = s.project_id
               WHERE s.script_id = ?""",
            (segment["script_id"],),
        )
        row = await cursor.fetchone()
        if not row or row[0] != user_id:
            raise HTTPException(status_code=403, detail="Forbidden")

        try:
            audio_bytes, ext = await synthesize(
                text=segment["content"],
                voice=body.voice,
                speed=body.speed,
                pitch=body.pitch,
                style_prompt=body.style_prompt,
                provider_name=body.tts_provider,
            )
            filename = save_audio(audio_bytes, extension=ext)
            audio_url = get_audio_url(filename)
        except Exception:
            logger.exception("TTS generation failed: segment=%s user=%s", segment_id, user_id)
            raise HTTPException(status_code=502, detail="TTS generation failed")

        # Save to voice_samples table
        sample_id = str(uuid4())
        await db.execute(
            """INSERT INTO voice_samples
               (sample_id, segment_id, tts_url, tts_voice, tts_speed, tts_pitch, tts_provider)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (sample_id, segment_id, audio_url, body.voice, body.speed, body.pitch, body.tts_provider),
        )

    return {
        "sample_id": sample_id,
        "segment_id": segment_id,
        "tts_url": audio_url,
        "voice": body.voice,
        "speed": body.speed,
        "pitch": body.pitch,
        "tts_provider": body.tts_provider,
    }


@router.post("/scripts/{script_id}/tts-multi")
async def generate_multi_speaker_tts(
    script_id: str,
    body: TTSMultiSpeakerRequest,
    user_id: str = Depends(get_user_id),
):
    """Generate multi-speaker TTS audio for an entire script."""
    _limiter.check(f"{user_id}:tts-multi", max_calls=5, window_seconds=60)

    async with get_db() as db:
        # Verify ownership via script -> project -> user
        cursor = await db.execute(
            """SELECT p.user_id, p.project_id FROM projects p
               JOIN scripts s ON p.project_id = s.project_id
               WHERE s.script_id = ?""",
            (script_id,),
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Script not found")
        if row["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Forbidden")

        # Collect all segment content with speaker labels
        segments = await get_segments_by_script(db, script_id)
        if not segments:
            raise HTTPException(status_code=404, detail="No segments found")

        combined_text = "\n".join(seg["content"] for seg in segments)

        try:
            audio_bytes, ext = await synthesize_multi_speaker(
                text=combined_text,
                speakers=body.speakers,
                style_prompt=body.style_prompt,
                provider_name=body.tts_provider,
            )
            filename = save_audio(audio_bytes, extension=ext)
            audio_url = get_audio_url(filename)
        except NotImplementedError:
            raise HTTPException(
                status_code=400,
                detail=f"Provider '{body.tts_provider}' does not support multi-speaker TTS",
            )
        except Exception:
            logger.exception("Multi-speaker TTS failed: script=%s user=%s", script_id, user_id)
            raise HTTPException(status_code=502, detail="Multi-speaker TTS generation failed")

    return {
        "script_id": script_id,
        "tts_url": audio_url,
        "speakers": body.speakers,
        "tts_provider": body.tts_provider,
    }


@router.post("/voice-samples/{sample_id}/host-audio")
async def upload_host_audio(
    sample_id: str,
    user_id: str = Depends(get_user_id),
    file: UploadFile = File(...),
):
    """Upload a host recording (multipart) and link it to a voice sample."""
    # Validate file extension
    ext = ".m4a"
    if file.filename:
        ext = PurePosixPath(file.filename).suffix or ".m4a"
    if ext.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported audio format: {ext}")

    # Validate file size
    audio_bytes = await file.read(MAX_UPLOAD_SIZE + 1)
    if len(audio_bytes) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 50MB)")

    async with get_db() as db:
        # Verify the sample exists and user owns it
        cursor = await db.execute(
            """SELECT vs.sample_id, vs.segment_id, vs.tts_url, p.user_id
               FROM voice_samples vs
               JOIN script_segments ss ON vs.segment_id = ss.segment_id
               JOIN scripts s ON ss.script_id = s.script_id
               JOIN projects p ON s.project_id = p.project_id
               WHERE vs.sample_id = ?""",
            (sample_id,),
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Voice sample not found")
        if row["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Forbidden")

        try:
            filename = save_audio(audio_bytes, extension=ext)
            host_url = get_audio_url(filename)
        except Exception:
            logger.exception("Host audio upload failed: sample=%s user=%s", sample_id, user_id)
            raise HTTPException(status_code=500, detail="Audio upload failed")

        await db.execute(
            "UPDATE voice_samples SET host_audio_url = ? WHERE sample_id = ?",
            (host_url, sample_id),
        )

    return {
        "sample_id": sample_id,
        "host_audio_url": host_url,
        "tts_url": row["tts_url"],
    }
