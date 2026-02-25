import pytest

import app.db as db_module


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
    assert session["state"] == "IDLE"
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
        state="SELECT_LLM",
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


async def test_get_user_or_create(db):
    """get_user_or_create should auto-create a user from UUID."""
    user = await db_module.get_user_or_create(db, "test-uuid-1234")
    assert user is not None
    assert user["user_id"] == "test-uuid-1234"
    assert "User-" in user["display_name"]

    # Second call should return same user
    user2 = await db_module.get_user_or_create(db, "test-uuid-1234")
    assert user2["user_id"] == user["user_id"]


async def test_create_and_get_projects_by_user(db):
    """create_project + get_projects_by_user should work."""
    await db_module.upsert_user(db, "U001", "Alice")
    pid = await db_module.create_project(
        db, "U001", topic="AI", audience="devs",
        duration_min=30, style="輕鬆閒聊", host_count=1, llm_provider="gemini",
    )
    projects = await db_module.get_projects_by_user(db, "U001")
    assert len(projects) == 1
    assert projects[0]["project_id"] == pid
    assert projects[0]["status"] == "draft"
    assert projects[0]["step"] == 1
    assert projects[0]["progress"] == 0


async def test_update_project(db):
    """update_project should partially update fields."""
    await db_module.upsert_user(db, "U001", "Alice")
    pid = await db_module.create_project(
        db, "U001", topic="AI", audience="devs",
        duration_min=30, style="輕鬆閒聊", host_count=1, llm_provider="gemini",
    )
    await db_module.update_project(db, pid, status="in_progress", step=3)
    project = await db_module.get_project(db, pid)
    assert project["status"] == "in_progress"
    assert project["step"] == 3
    assert project["topic"] == "AI"  # unchanged


async def test_update_project_rejects_bad_fields(db):
    """update_project should reject unknown fields."""
    with pytest.raises(ValueError, match="Invalid project fields"):
        await db_module.update_project(db, "fake_id", bad_field="x")


async def test_delete_project_cascade(db):
    """delete_project_cascade should remove project and all related data."""
    await db_module.upsert_user(db, "U001", "Alice")
    pid = await db_module.create_project(
        db, "U001", topic="AI", audience="devs",
        duration_min=30, style="輕鬆閒聊", host_count=1, llm_provider="gemini",
    )
    await db_module.create_titles(db, pid, [{"title_zh": "Test Title"}])
    sid = await db_module.create_script(db, pid, version=1)
    await db_module.create_segments(db, sid, [{"content": "Hello", "segment_type": "opening"}])

    await db_module.delete_project_cascade(db, pid)

    assert await db_module.get_project(db, pid) is None
    assert await db_module.get_titles_by_project(db, pid) == []
    assert await db_module.get_current_script(db, pid) is None


async def test_update_segment(db):
    """update_segment should update segment content."""
    await db_module.upsert_user(db, "U001", "Alice")
    pid = await db_module.create_project(
        db, "U001", topic="AI", audience="devs",
        duration_min=30, style="輕鬆閒聊", host_count=1, llm_provider="gemini",
    )
    sid = await db_module.create_script(db, pid, version=1)
    seg_ids = await db_module.create_segments(db, sid, [{"content": "Original"}])
    seg_id = seg_ids[0]

    await db_module.update_segment(db, seg_id, "Updated content")
    segment = await db_module.get_segment(db, seg_id)
    assert segment["content"] == "Updated content"
