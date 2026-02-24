"""Local audio file storage for TTS output."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

_AUDIO_DIR = Path("data/audio")


def init_audio_dir(base: Path | None = None) -> None:
    global _AUDIO_DIR
    if base:
        _AUDIO_DIR = base
    _AUDIO_DIR.mkdir(parents=True, exist_ok=True)


def save_audio(audio_bytes: bytes, extension: str = ".mp3") -> str:
    """Save audio bytes to local storage and return the filename."""
    _AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4()}{extension}"
    path = _AUDIO_DIR / filename
    path.write_bytes(audio_bytes)
    return filename


def get_audio_path(filename: str) -> Path:
    return _AUDIO_DIR / filename


def get_audio_url(filename: str, base_url: str = "") -> str:
    """Return the public URL for an audio file."""
    return f"{base_url}/audio/{filename}"
