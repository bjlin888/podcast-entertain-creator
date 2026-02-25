"""Google Cloud TTS provider wrapping existing SSML + gRPC logic."""

from __future__ import annotations

import logging

from google.cloud import texttospeech_v1 as tts

from app.tts.base import TTSError, TTSProvider
from app.tts.ssml_builder import text_to_ssml

logger = logging.getLogger(__name__)

VOICES = {
    "female": "cmn-TW-Wavenet-A",
    "male": "cmn-TW-Wavenet-C",
}


class CloudTTSProvider(TTSProvider):
    async def synthesize(
        self,
        text: str,
        voice: str = "",
        speed: float = 1.0,
        pitch: float = 0.0,
        style_prompt: str = "",
    ) -> bytes:
        voice_name = VOICES.get(voice, voice) if voice else VOICES["female"]
        ssml = text_to_ssml(text)

        try:
            client = tts.TextToSpeechAsyncClient()
            synthesis_input = tts.SynthesisInput(ssml=ssml)
            voice_params = tts.VoiceSelectionParams(
                language_code="cmn-TW",
                name=voice_name,
            )
            audio_config = tts.AudioConfig(
                audio_encoding=tts.AudioEncoding.MP3,
                speaking_rate=speed,
                pitch=pitch,
            )
            response = await client.synthesize_speech(
                input=synthesis_input,
                voice=voice_params,
                audio_config=audio_config,
            )
            return response.audio_content
        except Exception as e:
            raise TTSError(f"Cloud TTS error: {e}") from e

    def audio_format(self) -> str:
        return ".mp3"
