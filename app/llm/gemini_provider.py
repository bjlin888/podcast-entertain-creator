from __future__ import annotations

import asyncio
import json
import logging

from google import genai
from google.genai import types

from app.llm.base import LLMError, LLMProvider

logger = logging.getLogger(__name__)


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        self._client = genai.Client(api_key=api_key)
        self._model = model

    async def complete(self, system_prompt: str, user_message: str, task: str = "") -> dict:
        last_err = None
        for attempt in range(3):
            try:
                response = await self._client.aio.models.generate_content(
                    model=self._model,
                    contents=user_message,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        response_mime_type="application/json",
                        max_output_tokens=16384,
                    ),
                )
                usage = getattr(response, "usage_metadata", None)
                logger.info(
                    "Gemini LLM: task=%s model=%s in_tokens=%s out_tokens=%s",
                    task,
                    self._model,
                    getattr(usage, "prompt_token_count", "?"),
                    getattr(usage, "candidates_token_count", "?"),
                )
                return json.loads(response.text)
            except json.JSONDecodeError as e:
                last_err = LLMError(f"Gemini returned invalid JSON: {e}")
                logger.warning("Gemini invalid JSON (attempt %d/3): %s", attempt + 1, e)
                if attempt < 2:
                    await asyncio.sleep(1)
                    continue
                raise last_err from e
            except LLMError:
                raise
            except Exception as e:
                last_err = e
                if ("503" in str(e) or "500" in str(e)) and attempt < 2:
                    wait = (attempt + 1) * 3
                    logger.warning("Gemini %s, retrying in %ds (attempt %d/3)", e, wait, attempt + 1)
                    await asyncio.sleep(wait)
                    continue
                raise LLMError(f"Gemini API error: {e}") from e
        raise LLMError(f"Gemini API error after retries: {last_err}") from last_err
