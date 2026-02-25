"""Base class for TTS providers."""

from __future__ import annotations

from abc import ABC, abstractmethod


class TTSError(Exception):
    """Base exception for TTS provider errors."""


class TTSProvider(ABC):
    @abstractmethod
    async def synthesize(
        self,
        text: str,
        voice: str = "",
        speed: float = 1.0,
        pitch: float = 0.0,
        style_prompt: str = "",
    ) -> bytes:
        """Synthesize speech from text and return audio bytes."""
        ...

    async def synthesize_multi_speaker(
        self,
        text: str,
        speakers: list[dict],
        style_prompt: str = "",
    ) -> bytes:
        """Synthesize multi-speaker speech. Override in providers that support it."""
        raise NotImplementedError("Multi-speaker not supported by this provider")

    @abstractmethod
    def audio_format(self) -> str:
        """Return the file extension for the audio format (e.g. '.mp3', '.wav')."""
        ...
