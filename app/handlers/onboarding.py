from __future__ import annotations

import json
import logging

from linebot.v3.messaging import (
    AsyncMessagingApi,
    PushMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import (
    FollowEvent,
    MessageEvent,
    PostbackEvent,
    TextMessageContent,
)

from app.db import create_project, create_titles, get_titles_by_project, update_session
from app.line_helpers import (
    build_duration_quick_reply,
    build_llm_select_quick_reply,
    build_style_quick_reply,
    build_title_flex_message,
    build_welcome_message,
)
from app.models import BotState
from app.reply_utils import safe_reply
from app.state_machine import register

logger = logging.getLogger(__name__)


# ── Helpers ────────────────────────────────────────────────


def _ctx(session: dict) -> dict:
    return json.loads(session.get("context") or "{}")


async def _save_ctx(db, session_id: str, ctx: dict) -> None:
    await update_session(db, session_id, context=json.dumps(ctx, ensure_ascii=False))


# ── IDLE ───────────────────────────────────────────────────


@register(BotState.IDLE, FollowEvent)
async def handle_idle_follow(event, session, db, api: AsyncMessagingApi) -> BotState:
    await safe_reply(api, event.reply_token, [build_welcome_message()], user_id=session["user_id"])
    return BotState.SELECT_LLM


@register(BotState.IDLE, MessageEvent)
async def handle_idle_message(event, session, db, api: AsyncMessagingApi) -> BotState:
    if isinstance(event.message, TextMessageContent):
        text = event.message.text.strip()
        if text == "歷史":
            return await _show_history(session, db, event.reply_token, api)

    await safe_reply(api, event.reply_token, [build_welcome_message()], user_id=session["user_id"])
    return BotState.SELECT_LLM


async def _show_history(session: dict, db, reply_token: str, api) -> BotState:
    """List past projects for the user."""
    user_id = session["user_id"]
    cursor = await db.execute(
        "SELECT project_id, topic, llm_provider, created_at FROM projects WHERE user_id = ? ORDER BY created_at DESC LIMIT 10",
        (user_id,),
    )
    rows = [dict(r) for r in await cursor.fetchall()]
    if not rows:
        await safe_reply(
            api, reply_token,
            [TextMessage(text="目前沒有歷史專案。\n\n輸入任意文字開始新專案。")],
            user_id=user_id,
        )
        return BotState.IDLE

    lines = ["你的歷史專案：", ""]
    for i, r in enumerate(rows, 1):
        lines.append(f"{i}. {r['topic']} ({r['llm_provider'] or 'N/A'}) — {r['created_at']}")
    lines.append("\n輸入任意文字開始新專案。")

    await safe_reply(
        api, reply_token,
        [TextMessage(text="\n".join(lines))],
        user_id=user_id,
    )
    return BotState.IDLE


# ── SELECT_LLM ────────────────────────────────────────────


async def _enter_collect_info(db, session, provider: str, reply_token, api):
    ctx = {"collect_step": "TOPIC"}
    await update_session(db, session["session_id"], llm_provider=provider, context=json.dumps(ctx))
    await safe_reply(
        api, reply_token,
        [TextMessage(text=f"已選擇 {provider.title()} 作為 AI 模型。\n\n請輸入你的 Podcast 主題：")],
        user_id=session["user_id"],
    )


@register(BotState.SELECT_LLM, PostbackEvent)
async def handle_select_llm_postback(event, session, db, api: AsyncMessagingApi) -> BotState:
    data = event.postback.data
    if data.startswith("llm="):
        provider = data.split("=", 1)[1]
        if provider in ("claude", "gemini"):
            await _enter_collect_info(db, session, provider, event.reply_token, api)
            return BotState.COLLECT_INFO
    await safe_reply(
        api, event.reply_token,
        [TextMessage(text="請選擇 AI 模型：", quick_reply=build_llm_select_quick_reply())],
        user_id=session["user_id"],
    )
    return BotState.SELECT_LLM


@register(BotState.SELECT_LLM, MessageEvent)
async def handle_select_llm_message(event, session, db, api: AsyncMessagingApi) -> BotState:
    if isinstance(event.message, TextMessageContent):
        text = event.message.text.strip().lower()
        if text in ("claude", "gemini"):
            await _enter_collect_info(db, session, text, event.reply_token, api)
            return BotState.COLLECT_INFO
    await safe_reply(
        api, event.reply_token,
        [TextMessage(text="請選擇 AI 模型：", quick_reply=build_llm_select_quick_reply())],
        user_id=session["user_id"],
    )
    return BotState.SELECT_LLM


# ── COLLECT_INFO (text input steps: TOPIC, AUDIENCE, HOST_COUNT) ──


_STEP_PROMPTS = {
    "AUDIENCE": "請描述你的目標聽眾（例如：上班族、大學生、創業者）：",
    "HOST_COUNT": "請輸入主持人人數（預設 1）：",
}


@register(BotState.COLLECT_INFO, MessageEvent)
async def handle_collect_info_message(event, session, db, api: AsyncMessagingApi) -> BotState:
    if not isinstance(event.message, TextMessageContent):
        return BotState.COLLECT_INFO

    text = event.message.text.strip()
    ctx = _ctx(session)
    step = ctx.get("collect_step", "TOPIC")
    user_id = session["user_id"]

    if step == "TOPIC":
        ctx["topic"] = text
        ctx["collect_step"] = "AUDIENCE"
        await _save_ctx(db, session["session_id"], ctx)
        await safe_reply(
            api, event.reply_token,
            [TextMessage(text=_STEP_PROMPTS["AUDIENCE"])],
            user_id=user_id,
        )
        return BotState.COLLECT_INFO

    if step == "AUDIENCE":
        ctx["audience"] = text
        ctx["collect_step"] = "DURATION"
        await _save_ctx(db, session["session_id"], ctx)
        await safe_reply(
            api, event.reply_token,
            [TextMessage(text="請選擇預計時長：", quick_reply=build_duration_quick_reply())],
            user_id=user_id,
        )
        return BotState.COLLECT_INFO

    if step == "HOST_COUNT":
        try:
            host_count = int(text)
        except ValueError:
            host_count = 1
        ctx["host_count"] = host_count
        return await _finish_collect(ctx, session, db, event.reply_token, api)

    return BotState.COLLECT_INFO


# ── COLLECT_INFO (quick-reply steps: DURATION, STYLE) ─────


@register(BotState.COLLECT_INFO, PostbackEvent)
async def handle_collect_info_postback(event, session, db, api: AsyncMessagingApi) -> BotState:
    data = event.postback.data
    ctx = _ctx(session)
    step = ctx.get("collect_step", "TOPIC")
    user_id = session["user_id"]

    if step == "DURATION" and data.startswith("duration="):
        ctx["duration_min"] = int(data.split("=", 1)[1])
        ctx["collect_step"] = "STYLE"
        await _save_ctx(db, session["session_id"], ctx)
        await safe_reply(
            api, event.reply_token,
            [TextMessage(text="請選擇節目風格：", quick_reply=build_style_quick_reply())],
            user_id=user_id,
        )
        return BotState.COLLECT_INFO

    if step == "STYLE" and data.startswith("style="):
        ctx["style"] = data.split("=", 1)[1]
        ctx["collect_step"] = "HOST_COUNT"
        await _save_ctx(db, session["session_id"], ctx)
        await safe_reply(
            api, event.reply_token,
            [TextMessage(text=_STEP_PROMPTS["HOST_COUNT"])],
            user_id=user_id,
        )
        return BotState.COLLECT_INFO

    return BotState.COLLECT_INFO


# ── Finish collection → generate titles ───────────────────


async def _finish_collect(ctx: dict, session: dict, db, reply_token: str, api) -> BotState:
    from app.llm.factory import get_provider
    from app.llm.prompt_builder import load_prompt

    user_id = session["user_id"]
    llm_provider = session.get("llm_provider") or "gemini"

    # Create project
    project_id = await create_project(
        db,
        user_id=user_id,
        topic=ctx["topic"],
        audience=ctx["audience"],
        duration_min=ctx.get("duration_min", 30),
        style=ctx.get("style", "輕鬆閒聊"),
        host_count=ctx.get("host_count", 1),
        llm_provider=llm_provider,
    )

    # Link session to project
    await update_session(db, session["session_id"], project_id=project_id)

    # Reply "processing" immediately
    await safe_reply(
        api, reply_token,
        [TextMessage(text="收到！正在為你生成候選標題...")],
        user_id=user_id,
    )

    # Call LLM
    try:
        provider = get_provider(llm_provider)
        system = load_prompt("system")
        user_msg = load_prompt(
            "title_generation",
            topic=ctx["topic"],
            audience=ctx["audience"],
            style=ctx.get("style", "輕鬆閒聊"),
        )
        result = await provider.complete(system, user_msg, task="title_generation")
        titles_data = result.get("titles", [])[:5]
    except Exception:
        logger.exception("Title generation failed")
        await api.push_message(
            PushMessageRequest(to=user_id, messages=[TextMessage(text="標題生成失敗，請稍後再試。輸入任意文字重新開始。")])
        )
        return BotState.IDLE

    # Save titles
    await create_titles(db, project_id, titles_data)
    db_titles = await get_titles_by_project(db, project_id)

    # Push title cards
    await api.push_message(
        PushMessageRequest(
            to=user_id,
            messages=[
                build_title_flex_message(db_titles),
                TextMessage(text="請點選一個標題，或輸入「重新生成」重新產生標題。"),
            ],
        )
    )
    return BotState.TITLE_REVIEW
