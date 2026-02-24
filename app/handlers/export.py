from __future__ import annotations

import json
import logging

from linebot.v3.messaging import (
    AsyncMessagingApi,
    TextMessage,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from app.db import (
    get_current_script,
    get_project,
    get_segments_by_script,
    update_session,
)
from app.models import BotState
from app.reply_utils import safe_reply
from app.state_machine import register

logger = logging.getLogger(__name__)


@register(BotState.EXPORT, MessageEvent)
async def handle_export_message(event, session, db, api: AsyncMessagingApi) -> BotState:
    if not isinstance(event.message, TextMessageContent):
        return BotState.EXPORT

    text = event.message.text.strip()
    user_id = session["user_id"]

    if text == "匯出" or text == "匯出腳本":
        return await _export_script(session, db, event.reply_token, api)

    if text == "匯出音檔":
        return await _export_audio_list(session, db, event.reply_token, api)

    if text == "重新開始":
        await update_session(db, session["session_id"], state=BotState.IDLE.value, context="{}", project_id=None)
        await safe_reply(
            api, event.reply_token,
            [TextMessage(text="已重新開始！輸入任意文字開始新的 Podcast 專案。")],
            user_id=user_id,
        )
        return BotState.IDLE

    await safe_reply(
        api, event.reply_token,
        [TextMessage(
            text="你可以：\n- 輸入「匯出」匯出完整腳本\n- 輸入「匯出音檔」匯出音檔清單\n- 輸入「重新開始」開始新專案"
        )],
        user_id=user_id,
    )
    return BotState.EXPORT


async def _export_script(session: dict, db, reply_token: str, api) -> BotState:
    project_id = session.get("project_id")
    user_id = session["user_id"]

    if not project_id:
        await safe_reply(
            api, reply_token,
            [TextMessage(text="找不到專案，請重新開始。")],
            user_id=user_id,
        )
        return BotState.IDLE

    project = await get_project(db, project_id)
    script = await get_current_script(db, project_id)
    if not script:
        await safe_reply(
            api, reply_token,
            [TextMessage(text="尚無腳本可匯出。")],
            user_id=user_id,
        )
        return BotState.EXPORT

    segments = await get_segments_by_script(db, script["script_id"])

    # Build plain text export
    _type_label = {"opening": "開場", "main": "主題", "closing": "結尾"}
    lines = [
        f"Podcast 腳本 — {project['topic'] if project else ''}",
        f"版本：v{script['version']}",
        "=" * 30,
        "",
    ]
    for i, seg in enumerate(segments, 1):
        label = _type_label.get(seg.get("segment_type", ""), seg.get("segment_type", ""))
        lines.append(f"【段落 {i} — {label}】")
        lines.append(seg["content"])
        lines.append("")

    full_text = "\n".join(lines)

    # LINE has 5000 char limit per message, split if needed
    chunks = [full_text[i : i + 4900] for i in range(0, len(full_text), 4900)]
    messages = [TextMessage(text=chunk) for chunk in chunks[:5]]

    await safe_reply(api, reply_token, messages, user_id=user_id)
    return BotState.EXPORT


async def _export_audio_list(session: dict, db, reply_token: str, api) -> BotState:
    project_id = session.get("project_id")
    user_id = session["user_id"]

    if not project_id:
        await safe_reply(
            api, reply_token,
            [TextMessage(text="找不到專案。")],
            user_id=user_id,
        )
        return BotState.EXPORT

    script = await get_current_script(db, project_id)
    if not script:
        await safe_reply(
            api, reply_token,
            [TextMessage(text="尚無腳本。")],
            user_id=user_id,
        )
        return BotState.EXPORT

    # Get voice samples for this script's segments
    cursor = await db.execute(
        """SELECT ss.segment_order, ss.segment_type, vs.tts_url, vs.tts_voice, vs.host_audio_url
           FROM voice_samples vs
           JOIN script_segments ss ON vs.segment_id = ss.segment_id
           WHERE ss.script_id = ?
           ORDER BY ss.segment_order""",
        (script["script_id"],),
    )
    rows = [dict(r) for r in await cursor.fetchall()]

    if not rows:
        await safe_reply(
            api, reply_token,
            [TextMessage(text="目前沒有已生成的音檔。")],
            user_id=user_id,
        )
        return BotState.EXPORT

    lines = ["音檔清單：", ""]
    _type_label = {"opening": "開場", "main": "主題", "closing": "結尾"}
    for r in rows:
        label = _type_label.get(r.get("segment_type", ""), r.get("segment_type", ""))
        lines.append(f"段落 {r['segment_order'] + 1} ({label})")
        lines.append(f"  TTS: {r['tts_url']} [{r.get('tts_voice', '')}]")
        if r.get("host_audio_url"):
            lines.append(f"  主持人: {r['host_audio_url']}")
        lines.append("")

    await safe_reply(
        api, reply_token,
        [TextMessage(text="\n".join(lines))],
        user_id=user_id,
    )
    return BotState.EXPORT
