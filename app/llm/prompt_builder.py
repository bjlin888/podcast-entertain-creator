from __future__ import annotations

from pathlib import Path

_PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"


def load_prompt(name: str, **kwargs: str) -> str:
    """Load a prompt template from prompts/<name>.txt and format it."""
    path = _PROMPTS_DIR / f"{name}.txt"
    template = path.read_text(encoding="utf-8")
    if kwargs:
        template = template.format(**kwargs)
    return template
