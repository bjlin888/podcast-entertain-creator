import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.llm.base import LLMError
from app.llm.claude_provider import ClaudeProvider, _parse_json
from app.llm.gemini_provider import GeminiProvider
from app.llm.factory import get_provider, _instances


# ── JSON parser ────────────────────────────────────────────


def test_parse_json_plain():
    assert _parse_json('{"a": 1}') == {"a": 1}


def test_parse_json_with_fences():
    text = '```json\n{"a": 1}\n```'
    assert _parse_json(text) == {"a": 1}


def test_parse_json_with_fences_no_lang():
    text = '```\n{"a": 1}\n```'
    assert _parse_json(text) == {"a": 1}


# ── ClaudeProvider ─────────────────────────────────────────


async def test_claude_complete_success():
    provider = ClaudeProvider(api_key="fake")

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text='{"result": "ok"}')]

    with patch.object(provider._client.messages, "create", new_callable=AsyncMock, return_value=mock_response):
        result = await provider.complete("system", "user msg")

    assert result == {"result": "ok"}


async def test_claude_complete_invalid_json():
    provider = ClaudeProvider(api_key="fake")

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="not json at all")]

    with patch.object(provider._client.messages, "create", new_callable=AsyncMock, return_value=mock_response):
        with pytest.raises(LLMError, match="invalid JSON"):
            await provider.complete("system", "user msg")


async def test_claude_complete_api_error():
    provider = ClaudeProvider(api_key="fake")

    with patch.object(
        provider._client.messages, "create",
        new_callable=AsyncMock, side_effect=RuntimeError("timeout"),
    ):
        with pytest.raises(LLMError, match="Claude API error"):
            await provider.complete("system", "user msg")


# ── GeminiProvider ─────────────────────────────────────────


async def test_gemini_complete_success():
    provider = GeminiProvider(api_key="fake")

    mock_response = MagicMock()
    mock_response.text = '{"result": "ok"}'

    with patch.object(
        provider._client.aio.models, "generate_content",
        new_callable=AsyncMock, return_value=mock_response,
    ):
        result = await provider.complete("system", "user msg")

    assert result == {"result": "ok"}


async def test_gemini_complete_invalid_json():
    provider = GeminiProvider(api_key="fake")

    mock_response = MagicMock()
    mock_response.text = "broken"

    with patch.object(
        provider._client.aio.models, "generate_content",
        new_callable=AsyncMock, return_value=mock_response,
    ):
        with pytest.raises(LLMError, match="invalid JSON"):
            await provider.complete("system", "user msg")


# ── Factory ────────────────────────────────────────────────


def test_factory_unknown_provider():
    with pytest.raises(ValueError, match="Unknown LLM provider"):
        get_provider("openai")


def test_factory_caches_instance():
    _instances.clear()
    with patch("app.config.settings", MagicMock(gemini_api_key="k")):
        p1 = get_provider("gemini")
        p2 = get_provider("gemini")
    assert p1 is p2
    _instances.clear()
