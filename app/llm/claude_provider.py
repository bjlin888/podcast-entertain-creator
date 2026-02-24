from __future__ import annotations

import json
import re

from anthropic import AsyncAnthropic

from app.llm.base import LLMError, LLMProvider


class ClaudeProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6"):
        self._client = AsyncAnthropic(api_key=api_key)
        self._model = model

    async def complete(self, system_prompt: str, user_message: str, task: str = "") -> dict:
        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=4096,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )
            text = response.content[0].text
            return _parse_json(text)
        except json.JSONDecodeError as e:
            raise LLMError(f"Claude returned invalid JSON: {e}") from e
        except LLMError:
            raise
        except Exception as e:
            raise LLMError(f"Claude API error: {e}") from e


def _parse_json(text: str) -> dict:
    """Remove markdown fences and parse JSON."""
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        text = match.group(1).strip()
    return json.loads(text)
