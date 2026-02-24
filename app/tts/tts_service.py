"""Google Cloud Text-to-Speech service wrapper."""

from __future__ import annotations

import logging

from google.cloud import texttospeech_v1 as tts

from app.tts.ssml_builder import text_to_ssml

logger = logging.getLogger(__name__)

# Default voices for Taiwan Chinese
VOICES = {
    "female": "cmn-TW-Wavenet-A",
    "male": "cmn-TW-Wavenet-C",
}


async def synthesize(
    text: str,
    voice: str = "cmn-TW-Wavenet-A",
    speed: float = 1.0,
    pitch: float = 0.0,
) -> bytes:
    """Synthesize speech from text and return MP3 bytes."""
    ssml = text_to_ssml(text)

    client = tts.TextToSpeechAsyncClient()
    synthesis_input = tts.SynthesisInput(ssml=ssml)
    voice_params = tts.VoiceSelectionParams(
        language_code="cmn-TW",
        name=voice,
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
