import os

os.environ.setdefault("ANTHROPIC_API_KEY", "test_key")
os.environ.setdefault("GEMINI_API_KEY", "test_key")

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

import app.db as db_module


@pytest_asyncio.fixture
async def test_db(tmp_path):
    path = str(tmp_path / "test.db")
    await db_module.init_db(path)
    yield path


@pytest_asyncio.fixture
async def db(test_db):
    async with db_module.get_db() as conn:
        yield conn


@pytest_asyncio.fixture
async def client(test_db):
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
