from __future__ import annotations

import json
import logging

from linebot.v3.messaging import (
    AsyncMessagingApi,
    TextMessage,
)
from linebot.v3.webhooks import MessageEvent, PostbackEvent, TextMessageContent

from app.db import (
    create_feedback,
    get_current_script,
    update_session,
)
from app.line_helpers import build_scoring_flex
from app.models import BotState
from app.reply_utils import safe_reply
from app.state_machine import register

logger = logging.getLogger(__name__)


def _ctx(session: dict) -> dict:
    return json.loads(session.get("context") or "{}")


async def _save_ctx(db, session_id: str, ctx: dict) -> None:
    await update_session(db, session_id, context=json.dumps(ctx, ensure_ascii=False))


@register(BotState.FEEDBACK_LOOP, PostbackEvent)
async def handle_feedback_postback(event, session, db, api: AsyncMessagingApi) -> BotState:
    data = event.postback.data
    ctx = _ctx(session)
    user_id = session["user_id"]

    # Handle score postbacks: score_content=3, score_engagement=4, etc.
    for aspect in ("content", "engagement", "structure"):
        prefix = f"score_{aspect}="
        if data.startswith(prefix):
            score = int(data.split("=", 1)[1])
            ctx[f"score_{aspect}"] = score
            await _save_ctx(db, session["session_id"], ctx)

            # Check if all 3 scores collected
            if all(f"score_{a}" in ctx for a in ("content", "engagement", "structure")):
                await safe_reply(
                    api, event.reply_token,
                    [TextMessage(
                        text=(
                            f"評分已收到：內容 {ctx['score_content']}/5、"
                            f"吸引力 {ctx['score_engagement']}/5、"
                            f"結構 {ctx['score_structure']}/5\n\n"
                            "請輸入文字回饋，或輸入「滿意」完成迭代。"
                        )
                    )],
                    user_id=user_id,
                )
            else:
                scored = [a for a in ("content", "engagement", "structure") if f"score_{a}" in ctx]
                remaining = 3 - len(scored)
                await safe_reply(
                    api, event.reply_token,
                    [TextMessage(text=f"已記錄，還有 {remaining} 個面向待評分。")],
                    user_id=user_id,
                )
            return BotState.FEEDBACK_LOOP

    return BotState.FEEDBACK_LOOP


@register(BotState.FEEDBACK_LOOP, MessageEvent)
async def handle_feedback_message(event, session, db, api: AsyncMessagingApi) -> BotState:
    if not isinstance(event.message, TextMessageContent):
        return BotState.FEEDBACK_LOOP

    text = event.message.text.strip()
    ctx = _ctx(session)
    project_id = session.get("project_id")
    user_id = session["user_id"]

    # First entry into FEEDBACK_LOOP: send scoring flex
    if not any(f"score_{a}" in ctx for a in ("content", "engagement", "structure")) and text == "回饋":
        await safe_reply(
            api, event.reply_token,
            [build_scoring_flex()],
            user_id=user_id,
        )
        return BotState.FEEDBACK_LOOP

    if text == "滿意":
        # Save feedback and transition to EXPORT
        if project_id:
            script = await get_current_script(db, project_id)
            if script:
                await create_feedback(
                    db,
                    script_id=script["script_id"],
                    score_content=ctx.get("score_content"),
                    score_engagement=ctx.get("score_engagement"),
                    score_structure=ctx.get("score_structure"),
                    text_feedback=ctx.get("text_feedback"),
                )
        # Clean up feedback context
        for key in ("score_content", "score_engagement", "score_structure", "text_feedback"):
            ctx.pop(key, None)
        await _save_ctx(db, session["session_id"], ctx)
        await safe_reply(
            api, event.reply_token,
            [TextMessage(text="感謝你的回饋！輸入「匯出」匯出完整腳本。")],
            user_id=user_id,
        )
        return BotState.EXPORT

    # Text feedback → save and regenerate script
    ctx["text_feedback"] = text
    await _save_ctx(db, session["session_id"], ctx)

    if not project_id:
        return BotState.IDLE

    script = await get_current_script(db, project_id)
    if not script:
        return BotState.IDLE

    # Save feedback record
    await create_feedback(
        db,
        script_id=script["script_id"],
        score_content=ctx.get("score_content"),
        score_engagement=ctx.get("score_engagement"),
        score_structure=ctx.get("score_structure"),
        text_feedback=text,
    )

    # Reply "processing" and regenerate script
    await safe_reply(
        api, event.reply_token,
        [TextMessage(text="收到回饋，正在為你優化腳本...")],
        user_id=user_id,
    )

    # Clean up scores for next round
    for key in ("score_content", "score_engagement", "score_structure", "text_feedback"):
        ctx.pop(key, None)
    await _save_ctx(db, session["session_id"], ctx)

    # Regenerate script
    from app.handlers.script import generate_script_for_project

    return await generate_script_for_project(session, db, api)
