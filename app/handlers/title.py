from __future__ import annotations

import logging

from linebot.v3.messaging import (
    AsyncMessagingApi,
    PushMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import MessageEvent, PostbackEvent, TextMessageContent

from app.db import (
    delete_titles_by_project,
    create_titles,
    get_project,
    get_title,
    get_titles_by_project,
    select_title,
)
from app.line_helpers import build_title_flex_message
from app.models import BotState
from app.reply_utils import safe_reply
from app.state_machine import register

logger = logging.getLogger(__name__)


@register(BotState.TITLE_REVIEW, PostbackEvent)
async def handle_title_postback(event, session, db, api: AsyncMessagingApi) -> BotState:
    data = event.postback.data
    if data.startswith("select_title="):
        title_id = data.split("=", 1)[1]
        await select_title(db, title_id)
        title = await get_title(db, title_id)
        title_text = title["title_zh"] if title else "（未知標題）"
        await safe_reply(
            api, event.reply_token,
            [TextMessage(text=f"已選擇標題：{title_text}\n\n正在生成腳本，請稍候...")],
            user_id=session["user_id"],
        )
        from app.handlers.script import generate_script_for_project

        return await generate_script_for_project(session, db, api)
    return BotState.TITLE_REVIEW


@register(BotState.TITLE_REVIEW, MessageEvent)
async def handle_title_message(event, session, db, api: AsyncMessagingApi) -> BotState:
    if not isinstance(event.message, TextMessageContent):
        return BotState.TITLE_REVIEW

    text = event.message.text.strip()
    if text == "重新生成":
        return await _regenerate_titles(session, db, event.reply_token, api)

    await safe_reply(
        api, event.reply_token,
        [TextMessage(text="請點選一個標題，或輸入「重新生成」重新產生標題。")],
        user_id=session["user_id"],
    )
    return BotState.TITLE_REVIEW


async def _regenerate_titles(session: dict, db, reply_token: str, api) -> BotState:
    from app.llm.factory import get_provider
    from app.llm.prompt_builder import load_prompt

    project_id = session.get("project_id")
    if not project_id:
        await safe_reply(
            api, reply_token,
            [TextMessage(text="找不到專案資訊，請重新開始。")],
            user_id=session["user_id"],
        )
        return BotState.IDLE

    project = await get_project(db, project_id)
    if not project:
        return BotState.IDLE

    user_id = session["user_id"]
    llm_provider = session.get("llm_provider") or "gemini"

    await safe_reply(
        api, reply_token,
        [TextMessage(text="正在重新生成候選標題...")],
        user_id=user_id,
    )

    try:
        provider = get_provider(llm_provider)
        system = load_prompt("system")
        user_msg = load_prompt(
            "title_generation",
            topic=project["topic"],
            audience=project["audience"],
            style=project["style"] or "輕鬆閒聊",
        )
        result = await provider.complete(system, user_msg, task="title_generation")
        titles_data = result.get("titles", [])[:5]
    except Exception:
        logger.exception("Title regeneration failed")
        await api.push_message(
            PushMessageRequest(to=user_id, messages=[TextMessage(text="標題生成失敗，請稍後再試。")])
        )
        return BotState.TITLE_REVIEW

    await delete_titles_by_project(db, project_id)
    await create_titles(db, project_id, titles_data)
    db_titles = await get_titles_by_project(db, project_id)

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
