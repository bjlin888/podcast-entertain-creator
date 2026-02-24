import os

# Set test env vars BEFORE any app imports
os.environ.setdefault("LINE_CHANNEL_ACCESS_TOKEN", "test_token")
os.environ.setdefault("LINE_CHANNEL_SECRET", "test_secret")
os.environ.setdefault("LINE_CHANNEL_ID", "test_id")

import pytest_asyncio
from unittest.mock import AsyncMock

import app.db as db_module


@pytest_asyncio.fixture
async def test_db(tmp_path):
    """Initialise a temporary database and set it as active."""
    path = str(tmp_path / "test.db")
    await db_module.init_db(path)
    yield path


@pytest_asyncio.fixture
async def db(test_db):
    """Provide an open database connection for a single test."""
    async with db_module.get_db() as conn:
        yield conn


@pytest_asyncio.fixture
def mock_line_api():
    """Mock LINE Messaging API."""
    api = AsyncMock()
    api.reply_message = AsyncMock()
    api.push_message = AsyncMock()
    return api
