from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

import aiosqlite

logger = logging.getLogger(__name__)

_db_path: str = "data/podcast.db"

_TABLES: list[str] = [
    """
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        display_name TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS projects (
        project_id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL REFERENCES users(user_id),
        topic TEXT,
        audience TEXT,
        duration_min INTEGER,
        style TEXT,
        host_count INTEGER DEFAULT 1,
        llm_provider TEXT,
        status TEXT DEFAULT 'draft',
        step INTEGER DEFAULT 1,
        progress INTEGER DEFAULT 0,
        cover_index INTEGER DEFAULT 0,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS titles (
        title_id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL REFERENCES projects(project_id),
        title_zh TEXT NOT NULL,
        title_en TEXT,
        is_selected INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS scripts (
        script_id TEXT PRIMARY KEY,
        project_id TEXT NOT NULL REFERENCES projects(project_id),
        version INTEGER NOT NULL DEFAULT 1,
        is_current INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS script_segments (
        segment_id TEXT PRIMARY KEY,
        script_id TEXT NOT NULL REFERENCES scripts(script_id),
        segment_order INTEGER NOT NULL,
        segment_type TEXT,
        content TEXT NOT NULL,
        cues TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS feedbacks (
        feedback_id TEXT PRIMARY KEY,
        script_id TEXT NOT NULL REFERENCES scripts(script_id),
        score_content INTEGER,
        score_engagement INTEGER,
        score_structure INTEGER,
        text_feedback TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS sessions (
        session_id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL REFERENCES users(user_id),
        project_id TEXT,
        state TEXT NOT NULL DEFAULT 'IDLE',
        llm_provider TEXT,
        context TEXT DEFAULT '{}',
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS voice_samples (
        sample_id TEXT PRIMARY KEY,
        segment_id TEXT NOT NULL REFERENCES script_segments(segment_id),
        tts_url TEXT,
        tts_voice TEXT,
        tts_speed REAL DEFAULT 1.0,
        tts_pitch REAL DEFAULT 0.0,
        tts_provider TEXT DEFAULT 'gemini',
        host_audio_url TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS user_api_keys (
        user_id TEXT NOT NULL REFERENCES users(user_id),
        provider TEXT NOT NULL,
        encrypted_key TEXT NOT NULL,
        model TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now')),
        PRIMARY KEY (user_id, provider)
    )
    """,
]


_MIGRATIONS: list[str] = [
    # Add tts_provider column to voice_samples (for existing databases)
    """ALTER TABLE voice_samples ADD COLUMN tts_provider TEXT DEFAULT 'gemini'""",
]


async def init_db(db_path: str | None = None) -> None:
    global _db_path
    if db_path:
        _db_path = db_path
    parent = Path(_db_path).parent
    if str(parent) not in ("", "."):
        parent.mkdir(parents=True, exist_ok=True)
    async with get_db() as db:
        for ddl in _TABLES:
            await db.execute(ddl)
        for migration in _MIGRATIONS:
            try:
                await db.execute(migration)
            except Exception as e:
                if "duplicate column" not in str(e).lower() and "already exists" not in str(e).lower():
                    logger.warning("Migration skipped: %s", e)


@asynccontextmanager
async def get_db():
    db = await aiosqlite.connect(_db_path)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA foreign_keys=ON")
    try:
        yield db
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    finally:
        await db.close()


# -- User CRUD ---------------------------------------------------------------


async def upsert_user(db: aiosqlite.Connection, user_id: str, display_name: str) -> None:
    await db.execute(
        """INSERT INTO users (user_id, display_name)
           VALUES (?, ?)
           ON CONFLICT(user_id) DO UPDATE SET display_name = excluded.display_name""",
        (user_id, display_name),
    )


async def get_user(db: aiosqlite.Connection, user_id: str) -> dict | None:
    cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = await cursor.fetchone()
    return dict(row) if row else None


async def get_user_or_create(db: aiosqlite.Connection, user_id: str) -> dict:
    """Get an existing user or auto-create from UUID."""
    user = await get_user(db, user_id)
    if user:
        return user
    await db.execute(
        "INSERT INTO users (user_id, display_name) VALUES (?, ?)",
        (user_id, f"User-{user_id[:8]}"),
    )
    cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = await cursor.fetchone()
    return dict(row)


# -- Session CRUD ------------------------------------------------------------

_SESSION_FIELDS = {"state", "llm_provider", "project_id", "context"}


async def get_or_create_session(db: aiosqlite.Connection, user_id: str) -> dict:
    cursor = await db.execute(
        "SELECT * FROM sessions WHERE user_id = ? ORDER BY updated_at DESC LIMIT 1",
        (user_id,),
    )
    row = await cursor.fetchone()
    if row:
        return dict(row)

    session_id = str(uuid4())
    await db.execute(
        "INSERT INTO sessions (session_id, user_id, state, context) VALUES (?, ?, ?, ?)",
        (session_id, user_id, "IDLE", "{}"),
    )
    return {
        "session_id": session_id,
        "user_id": user_id,
        "project_id": None,
        "state": "IDLE",
        "llm_provider": None,
        "context": "{}",
        "updated_at": None,
    }


# -- Project CRUD -----------------------------------------------------------


async def create_project(
    db: aiosqlite.Connection,
    user_id: str,
    topic: str,
    audience: str,
    duration_min: int,
    style: str,
    host_count: int,
    llm_provider: str,
    cover_index: int = 0,
) -> str:
    project_id = str(uuid4())
    await db.execute(
        """INSERT INTO projects
           (project_id, user_id, topic, audience, duration_min, style, host_count, llm_provider, cover_index)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (project_id, user_id, topic, audience, duration_min, style, host_count, llm_provider, cover_index),
    )
    return project_id


async def get_project(db: aiosqlite.Connection, project_id: str) -> dict | None:
    cursor = await db.execute("SELECT * FROM projects WHERE project_id = ?", (project_id,))
    row = await cursor.fetchone()
    return dict(row) if row else None


async def get_projects_by_user(db: aiosqlite.Connection, user_id: str) -> list[dict]:
    """List all projects for a user with all fields."""
    cursor = await db.execute(
        "SELECT * FROM projects WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,),
    )
    return [dict(row) for row in await cursor.fetchall()]


async def update_project(db: aiosqlite.Connection, project_id: str, **fields) -> None:
    """Partial update: only set the provided fields."""
    if not fields:
        return
    allowed = {
        "topic", "audience", "duration_min", "style", "host_count",
        "llm_provider", "status", "step", "progress", "cover_index",
    }
    invalid = set(fields) - allowed
    if invalid:
        raise ValueError(f"Invalid project fields: {invalid}")
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values())
    values.append(project_id)
    await db.execute(
        f"UPDATE projects SET {set_clause} WHERE project_id = ?",
        values,
    )


async def delete_project_cascade(db: aiosqlite.Connection, project_id: str) -> None:
    """Delete a project and all related data (titles, scripts, segments, feedbacks, voice_samples)."""
    # Get all script_ids for this project
    cursor = await db.execute(
        "SELECT script_id FROM scripts WHERE project_id = ?", (project_id,)
    )
    script_ids = [row[0] for row in await cursor.fetchall()]

    for script_id in script_ids:
        # Get segment_ids for this script
        seg_cursor = await db.execute(
            "SELECT segment_id FROM script_segments WHERE script_id = ?", (script_id,)
        )
        segment_ids = [row[0] for row in await seg_cursor.fetchall()]

        # Delete voice_samples for each segment
        for segment_id in segment_ids:
            await db.execute("DELETE FROM voice_samples WHERE segment_id = ?", (segment_id,))

        # Delete segments
        await db.execute("DELETE FROM script_segments WHERE script_id = ?", (script_id,))
        # Delete feedbacks
        await db.execute("DELETE FROM feedbacks WHERE script_id = ?", (script_id,))

    # Delete scripts
    await db.execute("DELETE FROM scripts WHERE project_id = ?", (project_id,))
    # Delete titles
    await db.execute("DELETE FROM titles WHERE project_id = ?", (project_id,))
    # Delete sessions referencing this project
    await db.execute("DELETE FROM sessions WHERE project_id = ?", (project_id,))
    # Delete the project itself
    await db.execute("DELETE FROM projects WHERE project_id = ?", (project_id,))


# -- Title CRUD -------------------------------------------------------------


async def create_titles(db: aiosqlite.Connection, project_id: str, titles: list[dict]) -> list[str]:
    title_ids: list[str] = []
    for t in titles:
        title_id = str(uuid4())
        await db.execute(
            "INSERT INTO titles (title_id, project_id, title_zh, title_en) VALUES (?, ?, ?, ?)",
            (title_id, project_id, t["title_zh"], t.get("title_en", "")),
        )
        title_ids.append(title_id)
    return title_ids


async def get_titles_by_project(db: aiosqlite.Connection, project_id: str) -> list[dict]:
    cursor = await db.execute("SELECT * FROM titles WHERE project_id = ?", (project_id,))
    return [dict(row) for row in await cursor.fetchall()]


async def get_title(db: aiosqlite.Connection, title_id: str) -> dict | None:
    cursor = await db.execute("SELECT * FROM titles WHERE title_id = ?", (title_id,))
    row = await cursor.fetchone()
    return dict(row) if row else None


async def select_title(db: aiosqlite.Connection, title_id: str) -> None:
    cursor = await db.execute("SELECT project_id FROM titles WHERE title_id = ?", (title_id,))
    row = await cursor.fetchone()
    if row:
        await db.execute("UPDATE titles SET is_selected = 0 WHERE project_id = ?", (row[0],))
    await db.execute("UPDATE titles SET is_selected = 1 WHERE title_id = ?", (title_id,))


async def delete_titles_by_project(db: aiosqlite.Connection, project_id: str) -> None:
    await db.execute("DELETE FROM titles WHERE project_id = ?", (project_id,))


# -- Script CRUD ------------------------------------------------------------


async def create_script(db: aiosqlite.Connection, project_id: str, version: int = 1) -> str:
    script_id = str(uuid4())
    # Mark previous versions as not current
    await db.execute(
        "UPDATE scripts SET is_current = 0 WHERE project_id = ?", (project_id,)
    )
    await db.execute(
        "INSERT INTO scripts (script_id, project_id, version, is_current) VALUES (?, ?, ?, 1)",
        (script_id, project_id, version),
    )
    return script_id


async def get_current_script(db: aiosqlite.Connection, project_id: str) -> dict | None:
    cursor = await db.execute(
        "SELECT * FROM scripts WHERE project_id = ? AND is_current = 1", (project_id,)
    )
    row = await cursor.fetchone()
    return dict(row) if row else None


async def create_segments(
    db: aiosqlite.Connection, script_id: str, segments: list[dict]
) -> list[str]:
    import json as _json

    segment_ids: list[str] = []
    for i, seg in enumerate(segments):
        segment_id = str(uuid4())
        await db.execute(
            """INSERT INTO script_segments
               (segment_id, script_id, segment_order, segment_type, content, cues)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                segment_id,
                script_id,
                i,
                seg.get("segment_type", "main"),
                seg["content"],
                _json.dumps(seg.get("cues", []), ensure_ascii=False),
            ),
        )
        segment_ids.append(segment_id)
    return segment_ids


async def get_segments_by_script(db: aiosqlite.Connection, script_id: str) -> list[dict]:
    cursor = await db.execute(
        "SELECT * FROM script_segments WHERE script_id = ? ORDER BY segment_order",
        (script_id,),
    )
    return [dict(row) for row in await cursor.fetchall()]


async def get_segment(db: aiosqlite.Connection, segment_id: str) -> dict | None:
    cursor = await db.execute(
        "SELECT * FROM script_segments WHERE segment_id = ?", (segment_id,)
    )
    row = await cursor.fetchone()
    return dict(row) if row else None


async def update_segment(db: aiosqlite.Connection, segment_id: str, content: str) -> None:
    """Update segment content."""
    await db.execute(
        "UPDATE script_segments SET content = ? WHERE segment_id = ?",
        (content, segment_id),
    )


# -- Feedback CRUD ----------------------------------------------------------


async def create_feedback(
    db: aiosqlite.Connection,
    script_id: str,
    score_content: int | None = None,
    score_engagement: int | None = None,
    score_structure: int | None = None,
    text_feedback: str | None = None,
) -> str:
    feedback_id = str(uuid4())
    await db.execute(
        """INSERT INTO feedbacks
           (feedback_id, script_id, score_content, score_engagement, score_structure, text_feedback)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (feedback_id, script_id, score_content, score_engagement, score_structure, text_feedback),
    )
    return feedback_id


async def get_feedbacks_by_script(db: aiosqlite.Connection, script_id: str) -> list[dict]:
    cursor = await db.execute(
        "SELECT * FROM feedbacks WHERE script_id = ? ORDER BY created_at", (script_id,)
    )
    return [dict(row) for row in await cursor.fetchall()]


async def get_script_version_count(db: aiosqlite.Connection, project_id: str) -> int:
    cursor = await db.execute(
        "SELECT COUNT(*) FROM scripts WHERE project_id = ?", (project_id,)
    )
    row = await cursor.fetchone()
    return row[0] if row else 0


async def update_session(db: aiosqlite.Connection, session_id: str, **kwargs) -> None:
    if not kwargs:
        return
    invalid = set(kwargs) - _SESSION_FIELDS
    if invalid:
        raise ValueError(f"Invalid session fields: {invalid}")
    set_clause = ", ".join(f"{k} = ?" for k in kwargs)
    values = list(kwargs.values())
    values.append(session_id)
    await db.execute(
        f"UPDATE sessions SET {set_clause}, updated_at = datetime('now') WHERE session_id = ?",
        values,
    )


# -- User API Keys CRUD ----------------------------------------------------


async def upsert_user_api_key(
    db: aiosqlite.Connection,
    user_id: str,
    provider: str,
    encrypted_key: str,
    model: str | None = None,
) -> None:
    await db.execute(
        """INSERT INTO user_api_keys (user_id, provider, encrypted_key, model)
           VALUES (?, ?, ?, ?)
           ON CONFLICT(user_id, provider) DO UPDATE SET
               encrypted_key = excluded.encrypted_key,
               model = COALESCE(excluded.model, user_api_keys.model),
               updated_at = datetime('now')""",
        (user_id, provider, encrypted_key, model),
    )


async def get_user_api_key(
    db: aiosqlite.Connection, user_id: str, provider: str
) -> dict | None:
    cursor = await db.execute(
        "SELECT * FROM user_api_keys WHERE user_id = ? AND provider = ?",
        (user_id, provider),
    )
    row = await cursor.fetchone()
    return dict(row) if row else None


async def get_user_api_keys(
    db: aiosqlite.Connection, user_id: str
) -> list[dict]:
    cursor = await db.execute(
        "SELECT user_id, provider, model, created_at, updated_at FROM user_api_keys WHERE user_id = ?",
        (user_id,),
    )
    return [dict(row) for row in await cursor.fetchall()]


async def delete_user_api_key(
    db: aiosqlite.Connection, user_id: str, provider: str
) -> None:
    await db.execute(
        "DELETE FROM user_api_keys WHERE user_id = ? AND provider = ?",
        (user_id, provider),
    )
