"""TTS provider factory — mirrors app/llm/factory.py pattern."""

from __future__ import annotations

from app.tts.base import TTSProvider

_instances: dict[str, TTSProvider] = {}


def get_tts_provider(name: str) -> TTSProvider:
    """Return a cached TTS provider instance by name."""
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
