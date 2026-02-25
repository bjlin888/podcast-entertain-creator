"""TTS provider factory — mirrors app/llm/factory.py pattern."""

from __future__ import annotations

from app.tts.base import TTSProvider

_instances: dict[str, TTSProvider] = {}


def get_tts_provider(name: str) -> TTSProvider:
    """Return a cached TTS provider instance using server env var keys."""
    if name in _instances:
        return _instances[name]

    if name == "gemini":
        from app.config import settings
        from app.tts.gemini_tts_provider import GeminiTTSProvider

        provider = GeminiTTSProvider(
            api_key=settings.gemini_api_key,
            model=settings.gemini_tts_model,
        )
    elif name == "google":
        from app.tts.cloud_tts_provider import CloudTTSProvider

        provider = CloudTTSProvider()
    else:
        raise ValueError(f"Unknown TTS provider: {name}")

    _instances[name] = provider
    return provider


def _create_tts_provider(name: str, api_key: str) -> TTSProvider:
    """Create a fresh (non-cached) TTS provider with the given API key."""
    if name == "gemini":
        from app.config import settings
        from app.tts.gemini_tts_provider import GeminiTTSProvider

        return GeminiTTSProvider(api_key=api_key, model=settings.gemini_tts_model)
    elif name == "google":
        from app.tts.cloud_tts_provider import CloudTTSProvider

        return CloudTTSProvider()  # Uses ADC, no API key
    else:
        raise ValueError(f"Unknown TTS provider: {name}")


async def get_tts_provider_for_user(user_id: str, name: str) -> TTSProvider:
    """Get a TTS provider using user key if available, else server default."""
    from app.crypto import decrypt_api_key
    from app.db import get_db, get_user_api_key

    # Gemini TTS uses the same API key as Gemini LLM
    key_provider = "gemini" if name == "gemini" else name

    async with get_db() as db:
        row = await get_user_api_key(db, user_id, key_provider)

    if row and row.get("encrypted_key"):
        api_key = decrypt_api_key(row["encrypted_key"])
        return _create_tts_provider(name, api_key)

    return get_tts_provider(name)
