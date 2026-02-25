"""Tests for TTS provider abstraction (mocked — no real API calls)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.tts.text_preprocessor import extract_tone_cues, preprocess_for_gemini
from app.tts.gemini_tts_provider import GEMINI_VOICES, GeminiTTSProvider, _ensure_wav
from app.tts.cloud_tts_provider import VOICES as CLOUD_VOICES, CloudTTSProvider
from app.tts.base import TTSError


# ── text_preprocessor ──


def test_preprocess_strips_bgm():
    result = preprocess_for_gemini("[BGM淡入]大家好[BGM fade out]")
    assert "BGM" not in result
    assert "大家好" in result


def test_preprocess_strips_sfx():
    result = preprocess_for_gemini("[SFX: applause]謝謝[SFX鼓掌]")
    assert "SFX" not in result
    assert "謝謝" in result


def test_preprocess_keeps_tone_cues():
    text = "(輕鬆語氣)大家好(語氣上揚)歡迎收聽"
    result = preprocess_for_gemini(text)
    assert "(輕鬆語氣)" in result
    assert "(語氣上揚)" in result
    assert "大家好" in result


def test_preprocess_cleans_whitespace():
    result = preprocess_for_gemini("a\n\n\n\nb")
    assert result == "a\n\nb"


# ── Voice mapping ──


def test_gemini_voice_mapping():
    assert GEMINI_VOICES["female"] == "Kore"
    assert GEMINI_VOICES["male"] == "Achird"


def test_cloud_voice_mapping():
    assert CLOUD_VOICES["female"] == "cmn-TW-Wavenet-A"
    assert CLOUD_VOICES["male"] == "cmn-TW-Wavenet-C"


# ── _ensure_wav ──


def test_ensure_wav_passthrough():
    """Already-valid WAV data passes through unchanged."""
    wav_data = b"RIFF" + b"\x00" * 100
    result = _ensure_wav(wav_data, "audio/wav")
    assert result == wav_data


def test_ensure_wav_wraps_pcm():
    """Raw PCM data gets wrapped in a WAV header."""
    # 4 samples of silence (16-bit mono)
    pcm = b"\x00\x00" * 4
    result = _ensure_wav(pcm, "audio/L16;rate=24000")
    assert result[:4] == b"RIFF"
    assert b"WAVE" in result[:12]


def test_ensure_wav_custom_rate():
    pcm = b"\x00\x00" * 4
    result = _ensure_wav(pcm, "audio/L16;rate=16000")
    assert result[:4] == b"RIFF"


# ── Factory routing ──


def test_factory_gemini():
    from app.tts import factory
    factory._instances.clear()
    mock_settings = MagicMock()
    mock_settings.gemini_api_key = "test-key"
    mock_settings.gemini_tts_model = "gemini-2.5-flash-preview-tts"
    with patch("app.config.settings", mock_settings):
        from app.tts.factory import get_tts_provider
        provider = get_tts_provider("gemini")
        assert isinstance(provider, GeminiTTSProvider)
    factory._instances.clear()


def test_factory_google():
    from app.tts import factory
    factory._instances.clear()
    from app.tts.factory import get_tts_provider
    provider = get_tts_provider("google")
    assert isinstance(provider, CloudTTSProvider)
    factory._instances.clear()


def test_factory_unknown():
    from app.tts import factory
    factory._instances.clear()
    from app.tts.factory import get_tts_provider
    with pytest.raises(ValueError, match="Unknown TTS provider"):
        get_tts_provider("azure")
    factory._instances.clear()


def test_factory_caches():
    from app.tts import factory
    factory._instances.clear()
    from app.tts.factory import get_tts_provider
    p1 = get_tts_provider("google")
    p2 = get_tts_provider("google")
    assert p1 is p2
    factory._instances.clear()


# ── Provider audio_format ──


def test_cloud_audio_format():
    provider = CloudTTSProvider()
    assert provider.audio_format() == ".mp3"


def test_gemini_audio_format():
    provider = GeminiTTSProvider(api_key="test")
    assert provider.audio_format() == ".wav"


# ── GeminiTTSProvider.synthesize (mocked) ──


@pytest.mark.asyncio
async def test_gemini_synthesize_success():
    provider = GeminiTTSProvider(api_key="test")

    # Build mock response with inline audio data (fake WAV)
    mock_inline = MagicMock()
    mock_inline.data = b"RIFF" + b"\x00" * 100
    mock_inline.mime_type = "audio/wav"

    mock_part = MagicMock()
    mock_part.inline_data = mock_inline

    mock_content = MagicMock()
    mock_content.parts = [mock_part]

    mock_candidate = MagicMock()
    mock_candidate.content = mock_content

    mock_response = MagicMock()
    mock_response.candidates = [mock_candidate]

    provider._client = MagicMock()
    provider._client.aio.models.generate_content = AsyncMock(return_value=mock_response)

    audio = await provider.synthesize("(輕鬆語氣)大家好", voice="female", style_prompt="自然對話")
    assert audio[:4] == b"RIFF"

    # Verify generate_content was called
    provider._client.aio.models.generate_content.assert_awaited_once()


@pytest.mark.asyncio
async def test_gemini_synthesize_api_error():
    provider = GeminiTTSProvider(api_key="test")
    provider._client = MagicMock()
    provider._client.aio.models.generate_content = AsyncMock(side_effect=RuntimeError("API down"))

    with pytest.raises(TTSError, match="Gemini TTS error"):
        await provider.synthesize("test text")


@pytest.mark.asyncio
async def test_gemini_synthesize_no_audio():
    provider = GeminiTTSProvider(api_key="test")

    mock_response = MagicMock()
    mock_response.candidates = []

    provider._client = MagicMock()
    provider._client.aio.models.generate_content = AsyncMock(return_value=mock_response)

    with pytest.raises(TTSError, match="no audio data"):
        await provider.synthesize("test text")


# ── extract_tone_cues ──


def test_extract_tone_cues_basic():
    text = "(輕鬆語氣)大家好(語氣上揚)歡迎收聽"
    cleaned, hint = extract_tone_cues(text)
    assert "輕鬆語氣" not in cleaned
    assert "語氣上揚" not in cleaned
    assert "大家好" in cleaned
    assert "歡迎收聽" in cleaned
    assert "輕鬆語氣" in hint
    assert "語氣上揚" in hint


def test_extract_tone_cues_no_cues():
    text = "大家好歡迎收聽"
    cleaned, hint = extract_tone_cues(text)
    assert cleaned == "大家好歡迎收聽"
    assert hint == ""


def test_extract_tone_cues_max_three():
    text = "(語氣一)(語氣二)(語氣三)(語氣四)內容"
    cleaned, hint = extract_tone_cues(text)
    # Only first 3 cues in hint
    parts = hint.split("、")
    assert len(parts) == 3


def test_extract_tone_cues_english_parens_ignored():
    text = "(hello) 大家好 (語氣)"
    cleaned, hint = extract_tone_cues(text)
    # English-only parens should not be extracted
    assert "(hello)" in cleaned
    assert "語氣" in hint


def test_extract_tone_cues_fullwidth_parens():
    """Full-width parentheses （） should also be extracted."""
    text = "（活潑輕快）哈囉（停頓）再見"
    cleaned, hint = extract_tone_cues(text)
    assert "活潑輕快" not in cleaned
    assert "停頓" not in cleaned
    assert "哈囉" in cleaned
    assert "再見" in cleaned
    assert "活潑輕快" in hint
    assert "停頓" in hint


# ── Multi-speaker config ──


@pytest.mark.asyncio
async def test_gemini_multi_speaker_config():
    """Verify MultiSpeakerVoiceConfig is assembled correctly in the API call."""
    provider = GeminiTTSProvider(api_key="test")

    # Build mock response
    mock_inline = MagicMock()
    mock_inline.data = b"RIFF" + b"\x00" * 100
    mock_inline.mime_type = "audio/wav"
    mock_part = MagicMock()
    mock_part.inline_data = mock_inline
    mock_content = MagicMock()
    mock_content.parts = [mock_part]
    mock_candidate = MagicMock()
    mock_candidate.content = mock_content
    mock_response = MagicMock()
    mock_response.candidates = [mock_candidate]

    provider._client = MagicMock()
    provider._client.aio.models.generate_content = AsyncMock(return_value=mock_response)

    speakers = [
        {"name": "主持人A", "voice": "Charon"},
        {"name": "主持人B", "voice": "Kore"},
    ]
    audio = await provider.synthesize_multi_speaker(
        text="主持人A: 大家好\n主持人B: 歡迎收聽",
        speakers=speakers,
    )
    assert audio[:4] == b"RIFF"

    # Verify generate_content was called with multi-speaker config
    call_kwargs = provider._client.aio.models.generate_content.call_args
    config = call_kwargs.kwargs.get("config") or call_kwargs[1].get("config")
    assert config.speech_config.multi_speaker_voice_config is not None
    speaker_configs = config.speech_config.multi_speaker_voice_config.speaker_voice_configs
    assert len(speaker_configs) == 2
    assert speaker_configs[0].speaker == "主持人A"
    assert speaker_configs[1].speaker == "主持人B"


@pytest.mark.asyncio
async def test_multi_speaker_not_supported_cloud():
    """CloudTTS should raise NotImplementedError for multi-speaker."""
    provider = CloudTTSProvider()
    with pytest.raises(NotImplementedError, match="Multi-speaker not supported"):
        await provider.synthesize_multi_speaker(
            text="test",
            speakers=[{"name": "A", "voice": "x"}],
        )
