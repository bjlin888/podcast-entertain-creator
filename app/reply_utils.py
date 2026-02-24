from __future__ import annotations

import logging

from linebot.v3.messaging import (
    AsyncMessagingApi,
    PushMessageRequest,
    ReplyMessageRequest,
)
from linebot.v3.messaging.exceptions import ApiException

logger = logging.getLogger(__name__)


async def safe_reply(
    api: AsyncMessagingApi,
    reply_token: str,
    messages: list,
    user_id: str | None = None,
) -> None:
    """Reply with fallback to push_message if reply token is invalid/expired."""
    try:
        await api.reply_message(
            ReplyMessageRequest(reply_token=reply_token, messages=messages)
        )
    except ApiException as e:
        logger.warning("reply_message failed (status=%s), falling back to push_message", e.status)
        if user_id:
            try:
                await api.push_message(
                    PushMessageRequest(to=user_id, messages=messages)
                )
            except ApiException:
                logger.exception("push_message also failed for user %s", user_id)
        else:
            logger.error("Cannot fallback to push_message: no user_id")
