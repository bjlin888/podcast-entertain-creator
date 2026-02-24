from app.models import BotState
from app.state_machine import register, process_event, _handlers


async def test_register_and_dispatch():
    """Registered handler should be dispatched correctly."""

    class FakeEvent:
        pass

    @register(BotState.IDLE, FakeEvent)
    async def fake_handler(event, session, db, api):
        return BotState.SELECT_LLM

    session = {"state": "IDLE"}
    result = await process_event(FakeEvent(), session, db=None, api=None)
    assert result == BotState.SELECT_LLM

    # cleanup
    _handlers.pop((BotState.IDLE, FakeEvent), None)


async def test_fallback_returns_current_state():
    """If no handler matches, current state should be returned."""

    class UnknownEvent:
        pass

    session = {"state": "IDLE"}
    result = await process_event(UnknownEvent(), session, db=None, api=None)
    assert result == BotState.IDLE


async def test_catchall_handler():
    """Handler registered with event_type=None should catch all."""

    class AnyEvent:
        pass

    @register(BotState.EXPORT, None)
    async def catchall(event, session, db, api):
        return BotState.IDLE

    session = {"state": "EXPORT"}
    result = await process_event(AnyEvent(), session, db=None, api=None)
    assert result == BotState.IDLE

    # cleanup
    _handlers.pop((BotState.EXPORT, None), None)
