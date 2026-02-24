from __future__ import annotations

from app.llm.base import LLMProvider

_instances: dict[str, LLMProvider] = {}


def get_provider(name: str) -> LLMProvider:
    """Return a cached LLM provider instance by name."""
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
