from __future__ import annotations

from fastapi import Header, HTTPException

from app.db import get_db, get_user_or_create


async def get_user_id(x_user_id: str = Header(...)) -> str:
    """Extract user ID from X-User-Id header."""
    if not x_user_id:
        raise HTTPException(status_code=401, detail="X-User-Id header required")
    async with get_db() as db:
        await get_user_or_create(db, x_user_id)
    return x_user_id
