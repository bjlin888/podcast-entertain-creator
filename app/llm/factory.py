from __future__ import annotations

from app.llm.base import LLMProvider

_instances: dict[str, LLMProvider] = {}


def get_provider(name: str) -> LLMProvider:
    """Return a cached LLM provider instance using server env var keys."""
    if name in _instances:
        return _instances[name]

    from app.config import settings

    if name == "claude":
        from app.llm.claude_provider import ClaudeProvider

        provider = ClaudeProvider(api_key=settings.anthropic_api_key)
    elif name == "gemini":
        from app.llm.gemini_provider import GeminiProvider

        provider = GeminiProvider(api_key=settings.gemini_api_key)
    else:
        raise ValueError(f"Unknown LLM provider: {name}")

    _instances[name] = provider
    return provider


def _create_provider(name: str, api_key: str, model: str | None = None) -> LLMProvider:
    """Create a fresh (non-cached) LLM provider with the given API key."""
    if name == "claude":
        from app.llm.claude_provider import ClaudeProvider

        return ClaudeProvider(api_key=api_key, model=model or "claude-sonnet-4-6")
    elif name == "gemini":
        from app.llm.gemini_provider import GeminiProvider

        return GeminiProvider(api_key=api_key, model=model or "gemini-2.5-flash")
    else:
        raise ValueError(f"Unknown LLM provider: {name}")


async def get_provider_for_user(user_id: str, name: str) -> LLMProvider:
    """Get an LLM provider using the user's key if available, else server default."""
    from app.crypto import decrypt_api_key
    from app.db import get_db, get_user_api_key

    async with get_db() as db:
        row = await get_user_api_key(db, user_id, name)

    if row and row.get("encrypted_key"):
        api_key = decrypt_api_key(row["encrypted_key"])
        return _create_provider(name, api_key, row.get("model"))

    return get_provider(name)
