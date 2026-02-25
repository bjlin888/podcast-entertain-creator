"""TTS service facade — delegates to provider implementations."""

from __future__ import annotations

import logging

from app.tts.factory import get_tts_provider

logger = logging.getLogger(__name__)


async def synthesize(
    text: str,
    voice: str = "female",
    speed: float = 1.0,
    pitch: float = 0.0,
    style_prompt: str = "",
    provider_name: str = "gemini",
) -> tuple[bytes, str]:
    """Synthesize speech and return (audio_bytes, file_extension)."""
    provider = get_tts_provider(provider_name)
    audio = await provider.synthesize(text, voice, speed, pitch, style_prompt)
    return audio, provider.audio_format()


async def synthesize_multi_speaker(
    text: str,
    speakers: list[dict],
    style_prompt: str = "",
    provider_name: str = "gemini",
) -> tuple[bytes, str]:
    """Synthesize multi-speaker speech and return (audio_bytes, file_extension)."""
    provider = get_tts_provider(provider_name)
    audio = await provider.synthesize_multi_speaker(text, speakers, style_prompt)
    return audio, provider.audio_format()
