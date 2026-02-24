from __future__ import annotations

import logging

from linebot.v3.messaging import (
    AsyncMessagingApi,
    PushMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import AudioMessageContent, MessageEvent, PostbackEvent, TextMessageContent

from app.db import (
    create_script,
    create_segments,
    get_current_script,
    get_project,
    get_segment,
    get_segments_by_script,
    get_title,
    update_session,
)
from app.line_helpers import build_segment_flex
from app.models import BotState
from app.reply_utils import safe_reply
from app.state_machine import register

logger = logging.getLogger(__name__)


async def generate_script_for_project(session: dict, db, api) -> BotState:
    """Generate a script via LLM and push segment cards. Called on TITLE_REVIEW → SCRIPT_REVIEW transition."""
    from app.llm.factory import get_provider
    from app.llm.prompt_builder import load_prompt

    project_id = session.get("project_id")
    if not project_id:
        return BotState.IDLE

    project = await get_project(db, project_id)
    if not project:
        return BotState.IDLE

    user_id = session["user_id"]
    llm_provider = session.get("llm_provider") or "gemini"

    # Find selected title
    from app.db import get_titles_by_project

    titles = await get_titles_by_project(db, project_id)
    selected = next((t for t in titles if t["is_selected"]), None)
    selected_title = selected["title_zh"] if selected else project["topic"]

    try:
        provider = get_provider(llm_provider)
        system = load_prompt("system")
        user_msg = load_prompt(
            "script_generation",
            selected_title=selected_title,
            topic=project["topic"],
            audience=project["audience"],
            style=project["style"] or "輕鬆閒聊",
            duration_min=str(project["duration_min"] or 30),
            host_count=str(project["host_count"] or 1),
        )
        result = await provider.complete(system, user_msg, task="script_generation")
        segments_data = result.get("segments", [])
    except Exception:
        logger.exception("Script generation failed")
        await api.push_message(
            PushMessageRequest(
                to=user_id,
                messages=[TextMessage(text="腳本生成失敗，請輸入任意文字重試。")],
            )
        )
        return BotState.SCRIPT_REVIEW

    # Determine version
    current = await get_current_script(db, project_id)
    version = (current["version"] + 1) if current else 1

    script_id = await create_script(db, project_id, version=version)
    await create_segments(db, script_id, segments_data)
    db_segments = await get_segments_by_script(db, script_id)

    # Push segments one by one (LINE max 5 messages per push)
    batch: list = []
    for i, seg in enumerate(db_segments):
        batch.append(build_segment_flex(seg, i))
        if len(batch) == 5:
            await api.push_message(PushMessageRequest(to=user_id, messages=batch))
            batch = []
    if batch:
        await api.push_message(PushMessageRequest(to=user_id, messages=batch))

    await api.push_message(
        PushMessageRequest(
            to=user_id,
            messages=[
                TextMessage(
                    text=(
                        f"腳本 v{version} 已生成（共 {len(db_segments)} 段）。\n\n"
                        "你可以：\n"
                        "- 點選「修改這段」修改特定段落\n"
                        "- 點選「生成示範音檔」聽語音預覽\n"
                        "- 輸入「回饋」進入評分回饋\n"
                        "- 輸入「匯出」匯出完整腳本"
                    )
                )
            ],
        )
    )
    return BotState.SCRIPT_REVIEW


@register(BotState.SCRIPT_REVIEW, PostbackEvent)
async def handle_script_postback(event, session, db, api: AsyncMessagingApi) -> BotState:
    data = event.postback.data

    if data.startswith("tts_segment="):
        segment_id = data.split("=", 1)[1]
        import json

        ctx = json.loads(session.get("context") or "{}")
        ctx["tts_segment_id"] = segment_id
        ctx["tts_step"] = "VOICE"
        await update_session(
            db, session["session_id"], context=json.dumps(ctx, ensure_ascii=False)
        )
        from app.line_helpers import build_voice_quick_reply

        await safe_reply(
            api, event.reply_token,
            [TextMessage(text="請選擇語音角色：", quick_reply=build_voice_quick_reply())],
            user_id=session["user_id"],
        )
        return BotState.TTS_CONFIG

    if data.startswith("edit_segment="):
        segment_id = data.split("=", 1)[1]
        segment = await get_segment(db, segment_id)
        if segment:
            import json

            ctx = json.loads(session.get("context") or "{}")
            ctx["editing_segment_id"] = segment_id
            await update_session(
                db, session["session_id"], context=json.dumps(ctx, ensure_ascii=False)
            )
            await safe_reply(
                api, event.reply_token,
                [TextMessage(text=f"目前段落內容：\n\n{segment['content']}\n\n請輸入你的修改建議：")],
                user_id=session["user_id"],
            )
        return BotState.SCRIPT_REVIEW

    return BotState.SCRIPT_REVIEW


@register(BotState.SCRIPT_REVIEW, MessageEvent)
async def handle_script_message(event, session, db, api: AsyncMessagingApi) -> BotState:
    # Handle host audio upload
    if isinstance(event.message, AudioMessageContent):
        return await _handle_host_audio(event, session, db, api)

    if not isinstance(event.message, TextMessageContent):
        return BotState.SCRIPT_REVIEW

    text = event.message.text.strip()
    import json

    ctx = json.loads(session.get("context") or "{}")

    # Handle segment edit feedback
    editing_id = ctx.pop("editing_segment_id", None)
    if editing_id:
        await _handle_segment_edit(editing_id, text, session, db, event.reply_token, api)
        await update_session(
            db, session["session_id"], context=json.dumps(ctx, ensure_ascii=False)
        )
        return BotState.SCRIPT_REVIEW

    if text == "回饋":
        from app.line_helpers import build_scoring_flex

        await safe_reply(
            api, event.reply_token,
            [build_scoring_flex()],
            user_id=session["user_id"],
        )
        return BotState.FEEDBACK_LOOP

    if text == "匯出":
        return BotState.EXPORT

    await safe_reply(
        api, event.reply_token,
        [TextMessage(text="你可以：\n- 點選段落按鈕操作\n- 輸入「回饋」進入評分\n- 輸入「匯出」匯出腳本")],
        user_id=session["user_id"],
    )
    return BotState.SCRIPT_REVIEW


async def _handle_segment_edit(
    segment_id: str, feedback: str, session: dict, db, reply_token: str, api
) -> None:
    from app.llm.factory import get_provider
    from app.llm.prompt_builder import load_prompt

    segment = await get_segment(db, segment_id)
    if not segment:
        return

    user_id = session["user_id"]
    llm_provider = session.get("llm_provider") or "gemini"

    await safe_reply(
        api, reply_token,
        [TextMessage(text="正在根據你的建議修改段落...")],
        user_id=user_id,
    )

    try:
        provider = get_provider(llm_provider)
        system = load_prompt("system")
        user_msg = load_prompt(
            "script_refinement",
            original_content=segment["content"],
            feedback=feedback,
            scores="N/A",
        )
        result = await provider.complete(system, user_msg, task="script_refinement")
    except Exception:
        logger.exception("Segment edit failed")
        await api.push_message(
            PushMessageRequest(
                to=user_id, messages=[TextMessage(text="段落修改失敗，請稍後再試。")]
            )
        )
        return

    new_content = result.get("content", segment["content"])
    await db.execute(
        "UPDATE script_segments SET content = ? WHERE segment_id = ?",
        (new_content, segment_id),
    )

    updated = await get_segment(db, segment_id)
    if updated:
        idx = updated.get("segment_order", 0)
        await api.push_message(
            PushMessageRequest(
                to=user_id, messages=[build_segment_flex(updated, idx)]
            )
        )


async def _handle_host_audio(event, session: dict, db, api) -> BotState:
    """Handle host-uploaded audio: download via LINE Blob API, save locally, link to latest voice_sample."""
    from app.config import settings
    from app.tts.audio_storage import save_audio, get_audio_url
    from app.line_helpers import build_voice_comparison_flex

    user_id = session["user_id"]
    message_id = event.message.id

    try:
        # Download audio from LINE
        import aiohttp

        url = f"https://api-data.line.me/v2/bot/message/{message_id}/content"
        headers = {"Authorization": f"Bearer {settings.line_channel_access_token}"}
        async with aiohttp.ClientSession() as http:
            async with http.get(url, headers=headers) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"LINE Blob API returned {resp.status}")
                audio_bytes = await resp.read()

        filename = save_audio(audio_bytes, extension=".m4a")
        host_url = get_audio_url(filename)

        # Find latest voice_sample for this user's project and update host_audio_url
        project_id = session.get("project_id")
        if project_id:
            cursor = await db.execute(
                """SELECT vs.sample_id, vs.tts_url FROM voice_samples vs
                   JOIN script_segments ss ON vs.segment_id = ss.segment_id
                   JOIN scripts s ON ss.script_id = s.script_id
                   WHERE s.project_id = ?
                   ORDER BY vs.created_at DESC LIMIT 1""",
                (project_id,),
            )
            row = await cursor.fetchone()
            if row:
                await db.execute(
                    "UPDATE voice_samples SET host_audio_url = ? WHERE sample_id = ?",
                    (host_url, row[0]),
                )
                # Send comparison flex
                await safe_reply(
                    api, event.reply_token,
                    [
                        build_voice_comparison_flex(tts_url=row[1], host_url=host_url),
                        TextMessage(text="已收到你的錄音！上方可對照 TTS 與你的版本。"),
                    ],
                    user_id=user_id,
                )
                return BotState.SCRIPT_REVIEW

        await safe_reply(
            api, event.reply_token,
            [TextMessage(text="已收到你的錄音！")],
            user_id=user_id,
        )
    except Exception:
        logger.exception("Host audio upload failed")
        await safe_reply(
            api, event.reply_token,
            [TextMessage(text="錄音上傳處理失敗，請稍後再試。")],
            user_id=user_id,
        )
    return BotState.SCRIPT_REVIEW
