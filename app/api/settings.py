from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_user_id
from app.crypto import encrypt_api_key
from app.db import (
    delete_user_api_key,
    get_db,
    get_user_api_keys,
    upsert_user_api_key,
)
from app.models import SaveAiSettingsRequest

router = APIRouter(tags=["settings"])

_VALID_PROVIDERS = {"gemini", "claude"}


@router.get("/settings/ai")
async def get_ai_settings(user_id: str = Depends(get_user_id)):
    """Return configured AI providers for the user (never returns actual keys)."""
    async with get_db() as db:
        keys = await get_user_api_keys(db, user_id)
    return {
        "providers": [
            {
                "provider": k["provider"],
                "model": k["model"],
                "has_key": True,
                "updated_at": k["updated_at"],
            }
            for k in keys
        ]
    }


@router.put("/settings/ai")
async def save_ai_settings(
    body: SaveAiSettingsRequest,
    user_id: str = Depends(get_user_id),
):
    """Save AI provider settings (encrypts API keys at rest)."""
    async with get_db() as db:
        for entry in body.providers:
            if entry.provider not in _VALID_PROVIDERS:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid provider: {entry.provider}",
                )
            if entry.api_key:
                encrypted = encrypt_api_key(entry.api_key)
                await upsert_user_api_key(
                    db, user_id, entry.provider, encrypted, entry.model
                )
            elif entry.model is not None:
                # Update model only if key already exists
                existing = await get_db_key(db, user_id, entry.provider)
                if existing:
                    await upsert_user_api_key(
                        db,
                        user_id,
                        entry.provider,
                        existing["encrypted_key"],
                        entry.model,
                    )
    return {"status": "ok"}


@router.delete("/settings/ai/{provider}")
async def remove_ai_key(
    provider: str,
    user_id: str = Depends(get_user_id),
):
    """Remove a user's API key for a specific provider."""
    if provider not in _VALID_PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Invalid provider: {provider}")
    async with get_db() as db:
        await delete_user_api_key(db, user_id, provider)
    return {"status": "ok"}


async def get_db_key(db, user_id: str, provider: str):
    """Helper to get existing key row."""
    from app.db import get_user_api_key

    return await get_user_api_key(db, user_id, provider)
