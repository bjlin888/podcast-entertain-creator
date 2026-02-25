"""Gemini 2.5 Flash TTS provider using google-genai SDK."""

from __future__ import annotations

import asyncio
import logging
import struct
import wave
from io import BytesIO

from google import genai
from google.genai import types

from app.tts.base import TTSError, TTSProvider
from app.tts.text_preprocessor import extract_tone_cues, preprocess_for_gemini

logger = logging.getLogger(__name__)

GEMINI_VOICES = {
    "female": "Kore",
    "male": "Achird",
}

_VOICE_DIRECTION = "用自然的台灣華語播客主持人風格朗讀以下內容：\n\n"


class GeminiTTSProvider(TTSProvider):
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash-preview-tts"):
        self._client = genai.Client(api_key=api_key)
        self._model = model

    async def synthesize(
        self,
        text: str,
        voice: str = "",
        speed: float = 1.0,
        pitch: float = 0.0,
        style_prompt: str = "",
    ) -> bytes:
        voice_name = GEMINI_VOICES.get(voice, voice) if voice else GEMINI_VOICES["female"]
        processed = preprocess_for_gemini(text)

        # Extract tone cues and merge into style prompt
        processed, cue_hint = extract_tone_cues(processed)
        merged_style = "、".join(filter(None, [style_prompt, cue_hint]))

        # Gemini TTS does not support system_instruction — prepend direction to content
        prompt = _VOICE_DIRECTION
        if merged_style:
            prompt += f"風格：{merged_style}\n\n"
        prompt += processed

        try:
            response = await self._client.aio.models.generate_content(
                model=self._model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=voice_name,
                            ),
                        ),
                    ),
                ),
            )
        except Exception as e:
            raise TTSError(f"Gemini TTS error: {e}") from e

        # Extract audio data from response
        try:
            audio_data = response.candidates[0].content.parts[0].inline_data.data
            mime_type = response.candidates[0].content.parts[0].inline_data.mime_type
        except (IndexError, AttributeError) as e:
            raise TTSError(f"Gemini TTS returned no audio data: {e}") from e

        # Gemini returns raw PCM in a WAV-like format; wrap as proper WAV
        wav_data = _ensure_wav(audio_data, mime_type)
        logger.info("Gemini TTS: voice=%s audio_bytes=%d", voice_name, len(wav_data))
        return wav_data

    async def synthesize_multi_speaker(
        self,
        text: str,
        speakers: list[dict],
        style_prompt: str = "",
    ) -> bytes:
        """Synthesize multi-speaker audio using Gemini MultiSpeakerVoiceConfig.

        Text must contain speaker labels like "主持人A: ..." on each line.
        """
        processed = preprocess_for_gemini(text)

        speaker_configs = [
            types.SpeakerVoiceConfig(
                speaker=s["name"],
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=s.get("voice", GEMINI_VOICES["female"]),
                    ),
                ),
            )
            for s in speakers
        ]

        try:
            response = await self._client.aio.models.generate_content(
                model=self._model,
                contents=processed,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                            speaker_voice_configs=speaker_configs,
                        ),
                    ),
                ),
            )
        except Exception as e:
            raise TTSError(f"Gemini multi-speaker TTS error: {e}") from e

        try:
            audio_data = response.candidates[0].content.parts[0].inline_data.data
            mime_type = response.candidates[0].content.parts[0].inline_data.mime_type
        except (IndexError, AttributeError) as e:
            raise TTSError(f"Gemini multi-speaker TTS returned no audio data: {e}") from e

        wav_data = _ensure_wav(audio_data, mime_type)
        logger.info("Gemini TTS multi-speaker: speakers=%d audio_bytes=%d", len(speakers), len(wav_data))
        return wav_data

    def audio_format(self) -> str:
        return ".wav"


def _ensure_wav(data: bytes, mime_type: str) -> bytes:
    """Ensure audio data is a valid WAV file.

    Gemini TTS returns raw PCM with mime_type like 'audio/L16;rate=24000'.
    We wrap it in a proper WAV header.
    """
    if data[:4] == b"RIFF":
        return data

    # Parse sample rate from mime type (e.g. "audio/L16;rate=24000")
    sample_rate = 24000
    if "rate=" in mime_type:
        try:
            rate_str = mime_type.split("rate=")[1].split(";")[0].split(",")[0]
            sample_rate = int(rate_str)
        except (ValueError, IndexError):
            pass

    buf = BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(data)

    return buf.getvalue()
