from unittest.mock import patch, AsyncMock, MagicMock

import pytest
from httpx import AsyncClient, ASGITransport


@pytest.fixture
def _init_db_noop():
    """Prevent lifespan from touching the real DB."""
    with patch("app.main.init_db", new_callable=AsyncMock):
        yield


async def test_health(_init_db_noop):
    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_callback_invalid_signature(_init_db_noop):
    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/callback",
            content='{"events":[]}',
            headers={"X-Line-Signature": "bad_sig"},
        )
    assert resp.status_code == 400


async def test_callback_valid_signature(_init_db_noop, test_db):
    """Valid signature should process events and return OK."""
    from app.main import app

    mock_event = MagicMock()
    mock_event.source.user_id = "U_TEST"
    mock_event.reply_token = "token"

    with patch("app.main.parser") as mock_parser, \
         patch("app.main._handle_event", new_callable=AsyncMock) as mock_handle:
        mock_parser.parse.return_value = [mock_event]

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/callback",
                content='{"events":[]}',
                headers={"X-Line-Signature": "valid"},
            )

    assert resp.status_code == 200
    mock_handle.assert_awaited_once_with(mock_event)
