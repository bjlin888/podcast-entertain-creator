from abc import ABC, abstractmethod


class LLMError(Exception):
    """Base exception for LLM provider errors."""


class LLMProvider(ABC):
    @abstractmethod
    async def complete(self, system_prompt: str, user_message: str, task: str = "") -> dict:
        """Send a prompt and return parsed JSON dict."""
        ...
