from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_user_id
from app.db import (
    get_current_script,
    get_db,
    get_project,
    get_segments_by_script,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["export"])

_TYPE_LABEL = {"opening": "開場", "main": "主題", "closing": "結尾"}


@router.get("/projects/{project_id}/export/script")
async def export_script(
    project_id: str,
    user_id: str = Depends(get_user_id),
):
    """Return full script as structured text."""
    async with get_db() as db:
        project = await get_project(db, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        if project["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Forbidden")

        script = await get_current_script(db, project_id)
        if not script:
            raise HTTPException(status_code=404, detail="No script found")

        segments = await get_segments_by_script(db, script["script_id"])

    # Build plain text export
    lines = [
        f"Podcast 腳本 — {project['topic'] or ''}",
        f"版本：v{script['version']}",
        "=" * 30,
        "",
    ]
    for i, seg in enumerate(segments, 1):
        label = _TYPE_LABEL.get(seg.get("segment_type", ""), seg.get("segment_type", ""))
        lines.append(f"【段落 {i} — {label}】")
        lines.append(seg["content"])
        lines.append("")

    full_text = "\n".join(lines)

    return {
        "project_id": project_id,
        "script_id": script["script_id"],
        "version": script["version"],
        "text": full_text,
        "segment_count": len(segments),
    }


@router.get("/projects/{project_id}/export/audio")
async def export_audio(
    project_id: str,
    user_id: str = Depends(get_user_id),
):
    """Return list of audio files for the current script."""
    async with get_db() as db:
        project = await get_project(db, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        if project["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Forbidden")

        script = await get_current_script(db, project_id)
        if not script:
            raise HTTPException(status_code=404, detail="No script found")

        # Get voice samples for this script's segments
        cursor = await db.execute(
            """SELECT ss.segment_order, ss.segment_type,
                      vs.sample_id, vs.tts_url, vs.tts_voice, vs.host_audio_url
               FROM voice_samples vs
               JOIN script_segments ss ON vs.segment_id = ss.segment_id
               WHERE ss.script_id = ?
               ORDER BY ss.segment_order""",
            (script["script_id"],),
        )
        rows = [dict(r) for r in await cursor.fetchall()]

    audio_files = []
    for r in rows:
        label = _TYPE_LABEL.get(r.get("segment_type", ""), r.get("segment_type", ""))
        audio_files.append({
            "sample_id": r["sample_id"],
            "segment_order": r["segment_order"],
            "segment_type": r.get("segment_type", ""),
            "label": label,
            "tts_url": r["tts_url"],
            "tts_voice": r.get("tts_voice", ""),
            "host_audio_url": r.get("host_audio_url"),
        })

    return {
        "project_id": project_id,
        "script_id": script["script_id"],
        "audio_files": audio_files,
    }
