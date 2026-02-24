from __future__ import annotations

import json
import logging

from linebot.v3.messaging import (
    AsyncMessagingApi,
    PushMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import MessageEvent, PostbackEvent

from app.db import get_segment, update_session
from app.line_helpers import build_speed_quick_reply, build_voice_quick_reply
from app.models import BotState
from app.reply_utils import safe_reply
from app.state_machine import register

logger = logging.getLogger(__name__)


def _ctx(session: dict) -> dict:
    return json.loads(session.get("context") or "{}")


async def _save_ctx(db, session_id: str, ctx: dict) -> None:
    await update_session(db, session_id, context=json.dumps(ctx, ensure_ascii=False))


# ── TTS_CONFIG ─────────────────────────────────────────────


@register(BotState.TTS_CONFIG, PostbackEvent)
async def handle_tts_config_postback(event, session, db, api: AsyncMessagingApi) -> BotState:
    data = event.postback.data
    ctx = _ctx(session)
    tts_step = ctx.get("tts_step", "VOICE")
    user_id = session["user_id"]

    if tts_step == "VOICE" and data.startswith("voice="):
        ctx["tts_voice"] = data.split("=", 1)[1]
        ctx["tts_step"] = "SPEED"
        await _save_ctx(db, session["session_id"], ctx)
        await safe_reply(
            api, event.reply_token,
            [TextMessage(text="請選擇語速：", quick_reply=build_speed_quick_reply())],
            user_id=user_id,
        )
        return BotState.TTS_CONFIG

    if tts_step == "SPEED" and data.startswith("speed="):
        ctx["tts_speed"] = float(data.split("=", 1)[1])
        # Proceed to generate
        return await _start_tts_generation(ctx, session, db, event.reply_token, api)

    return BotState.TTS_CONFIG


@register(BotState.TTS_CONFIG, MessageEvent)
async def handle_tts_config_message(event, session, db, api: AsyncMessagingApi) -> BotState:
    await safe_reply(
        api, event.reply_token,
        [TextMessage(text="請使用下方選項選擇語音設定。")],
        user_id=session["user_id"],
    )
    return BotState.TTS_CONFIG


async def _start_tts_generation(ctx: dict, session: dict, db, reply_token: str, api) -> BotState:
    from app.tts.audio_storage import get_audio_url, save_audio
    from app.tts.tts_service import synthesize

    segment_id = ctx.get("tts_segment_id")
    if not segment_id:
        return BotState.SCRIPT_REVIEW

    segment = await get_segment(db, segment_id)
    if not segment:
        return BotState.SCRIPT_REVIEW

    user_id = session["user_id"]
    voice = ctx.get("tts_voice", "cmn-TW-Wavenet-A")
    speed = ctx.get("tts_speed", 1.0)
    pitch = ctx.get("tts_pitch", 0.0)

    await safe_reply(
        api, reply_token,
        [TextMessage(text="正在生成語音示範...")],
        user_id=user_id,
    )

    try:
        audio_bytes = await synthesize(
            text=segment["content"], voice=voice, speed=speed, pitch=pitch
        )
        filename = save_audio(audio_bytes, extension=".mp3")
        audio_url = get_audio_url(filename)

        # Save to voice_samples table
        from uuid import uuid4

        sample_id = str(uuid4())
        await db.execute(
            """INSERT INTO voice_samples
               (sample_id, segment_id, tts_url, tts_voice, tts_speed, tts_pitch)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (sample_id, segment_id, audio_url, voice, speed, pitch),
        )

        # Send audio message
        from linebot.v3.messaging import AudioMessage

        await api.push_message(
            PushMessageRequest(
                to=user_id,
                messages=[
                    AudioMessage(
                        original_content_url=audio_url,
                        duration=60000,  # placeholder duration
                    ),
                    TextMessage(
                        text="語音示範已生成！你可以上傳自己的錄音來對照比較。\n回到腳本檢視中。"
                    ),
                ],
            )
        )
    except Exception:
        logger.exception("TTS generation failed")
        await api.push_message(
            PushMessageRequest(
                to=user_id,
                messages=[TextMessage(text="語音生成失敗，請稍後再試。")],
            )
        )

    # Clean up TTS context and return to SCRIPT_REVIEW
    for key in ("tts_step", "tts_segment_id", "tts_voice", "tts_speed", "tts_pitch"):
        ctx.pop(key, None)
    await _save_ctx(db, session["session_id"], ctx)
    return BotState.SCRIPT_REVIEW
