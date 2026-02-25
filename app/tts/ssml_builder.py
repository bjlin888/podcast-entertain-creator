"""Convert script cues to SSML for Google Cloud TTS."""

from __future__ import annotations

import re


def text_to_ssml(text: str) -> str:
    """Convert script text with cues into SSML."""
    # Strip non-speech cues
    text = re.sub(r"\[BGM[^\]]*\]", "", text)
    text = re.sub(r"\[SFX[^\]]*\]", "", text)

    # Convert speech cues to SSML tags
    text = text.replace("(停頓)", '<break time="800ms"/>')
    text = text.replace("(pause)", '<break time="800ms"/>')
    text = text.replace("(長停頓)", '<break time="1500ms"/>')
    text = text.replace("(long pause)", '<break time="1500ms"/>')

    # Emphasis
    text = re.sub(
        r"\(強調\)(.*?)\(/強調\)",
        r'<emphasis level="strong">\1</emphasis>',
        text,
    )
    text = re.sub(
        r"\(emphasis\)(.*?)\(/emphasis\)",
        r'<emphasis level="strong">\1</emphasis>',
        text,
    )

    # Soft voice
    text = re.sub(
        r"\(輕聲\)(.*?)\(/輕聲\)",
        r'<prosody volume="soft">\1</prosody>',
        text,
    )
    text = re.sub(
        r"\(soft voice\)(.*?)\(/soft voice\)",
        r'<prosody volume="soft">\1</prosody>',
        text,
    )

    # Catch-all: strip remaining (中文cue) patterns not handled above
    text = re.sub(r"\([^()]*[\u4e00-\u9fff][^()]*\)", "", text)

    # Clean up extra whitespace
    text = re.sub(r"\n{3,}", "\n\n", text).strip()

    return f"<speak>{text}</speak>"
