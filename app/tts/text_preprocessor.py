"""Text preprocessing for Gemini TTS.

Gemini natively understands tone/mood cues like (輕鬆語氣) as performance
directions, so we only strip non-speech annotations like [BGM...] and [SFX...].
"""

from __future__ import annotations

import re


def preprocess_for_gemini(text: str) -> str:
    """Strip BGM/SFX cues but keep tone/mood cues for Gemini to interpret."""
    text = re.sub(r"\[BGM[^\]]*\]", "", text)
    text = re.sub(r"\[SFX[^\]]*\]", "", text)
    # Clean up extra whitespace
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


# Match Chinese cues in both half-width () and full-width （） parentheses
_CUE_PATTERN = re.compile(r"[(\uff08][^()\uff08\uff09]*[\u4e00-\u9fff][^()\uff08\uff09]*[)\uff09]")


def extract_tone_cues(text: str) -> tuple[str, str]:
    """Extract tone cues from text. Returns (cleaned_text, style_hint).

    Finds parenthesized Chinese cues like (輕鬆語氣) or （活潑輕快）,
    removes them from text, and returns them as a comma-joined style hint string.
    Handles both half-width () and full-width （） parentheses.
    """
    cues = _CUE_PATTERN.findall(text)
    cleaned = _CUE_PATTERN.sub("", text)
    style_hint = "、".join(c.strip("()（）") for c in cues[:3]) if cues else ""
    return cleaned.strip(), style_hint
