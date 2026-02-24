import pytest

import app.db as db_module
from app.models import BotState


async def test_tables_created(test_db):
    """All 8 tables should exist after init."""
    expected = {
        "users", "projects", "titles", "scripts",
        "script_segments", "feedbacks", "sessions", "voice_samples",
    }
    async with db_module.get_db() as db:
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        tables = {row[0] for row in await cursor.fetchall()}
    assert expected.issubset(tables)


async def test_upsert_user_create(db):
    """upsert_user should insert a new user."""
    await db_module.upsert_user(db, "U001", "Alice")
    user = await db_module.get_user(db, "U001")
    assert user is not None
    assert user["display_name"] == "Alice"


async def test_upsert_user_update(db):
    """upsert_user should update display_name on conflict."""
    await db_module.upsert_user(db, "U001", "Alice")
    await db_module.upsert_user(db, "U001", "Alice2")
    user = await db_module.get_user(db, "U001")
    assert user["display_name"] == "Alice2"


async def test_get_user_not_found(db):
    """get_user returns None for missing user."""
    user = await db_module.get_user(db, "MISSING")
    assert user is None


async def test_get_or_create_session_creates(db):
    """Should create a new IDLE session for a user."""
    await db_module.upsert_user(db, "U001", "Alice")
    session = await db_module.get_or_create_session(db, "U001")
    assert session["state"] == BotState.IDLE.value
    assert session["user_id"] == "U001"


async def test_get_or_create_session_returns_existing(db):
    """Should return the same session on second call."""
    await db_module.upsert_user(db, "U001", "Alice")
    s1 = await db_module.get_or_create_session(db, "U001")
    await db.commit()
    s2 = await db_module.get_or_create_session(db, "U001")
    assert s1["session_id"] == s2["session_id"]


async def test_update_session(db):
    """update_session should change specified fields."""
    await db_module.upsert_user(db, "U001", "Alice")
    session = await db_module.get_or_create_session(db, "U001")
    await db_module.update_session(
        db, session["session_id"],
        state=BotState.SELECT_LLM.value,
        llm_provider="claude",
    )
    await db.commit()
    cursor = await db.execute(
        "SELECT state, llm_provider FROM sessions WHERE session_id = ?",
        (session["session_id"],),
    )
    row = await cursor.fetchone()
    assert row[0] == "SELECT_LLM"
    assert row[1] == "claude"


async def test_update_session_rejects_bad_fields(db):
    """update_session should reject unknown fields."""
    with pytest.raises(ValueError, match="Invalid session fields"):
        await db_module.update_session(db, "fake_id", bad_field="x")
