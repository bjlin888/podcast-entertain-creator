from __future__ import annotations

import logging
from typing import Any, Callable

from app.models import BotState

logger = logging.getLogger(__name__)

_handlers: dict[tuple[BotState, type | None], Callable] = {}


def register(state: BotState, event_type: type | None = None):
    """Register a handler for (state, event_type). event_type=None is catch-all."""

    def decorator(func: Callable) -> Callable:
        _handlers[(state, event_type)] = func
        logger.debug("Registered handler: (%s, %s) → %s", state.name, event_type.__name__ if event_type else None, func.__qualname__)
        return func

    return decorator


async def process_event(event: Any, session: dict, db: Any, api: Any) -> BotState:
    """Dispatch event to the registered handler, return next state."""
    state = BotState(session["state"])
    event_type = type(event)

    handler = _handlers.get((state, event_type))
    if handler is None:
        handler = _handlers.get((state, None))
    if handler is None:
        logger.warning("No handler for state=%s, event=%s — staying in current state", state.name, event_type.__name__)
        return state

    logger.info("Dispatching: state=%s, event=%s → %s", state.name, event_type.__name__, handler.__qualname__)
    try:
        result = await handler(event, session, db, api)
        logger.info("Handler %s returned state=%s", handler.__qualname__, result.value)
        return result
    except Exception:
        logger.exception("Handler %s raised exception", handler.__qualname__)
        raise
