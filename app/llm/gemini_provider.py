from __future__ import annotations

import json

from google import genai
from google.genai import types

from app.llm.base import LLMError, LLMProvider


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self._client = genai.Client(api_key=api_key)
        self._model = model

    async def complete(self, system_prompt: str, user_message: str, task: str = "") -> dict:
        try:
            response = await self._client.aio.models.generate_content(
                model=self._model,
                contents=user_message,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                ),
            )
            return json.loads(response.text)
        except json.JSONDecodeError as e:
            raise LLMError(f"Gemini returned invalid JSON: {e}") from e
        except LLMError:
            raise
        except Exception as e:
            raise LLMError(f"Gemini API error: {e}") from e
