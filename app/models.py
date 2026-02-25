from __future__ import annotations

from pydantic import BaseModel, Field


class CreateProjectRequest(BaseModel):
    topic: str = Field(default="", max_length=500)
    audience: str = Field(default="", max_length=500)
    duration_min: int = Field(default=30, ge=1, le=180)
    style: str = Field(default="輕鬆閒聊", max_length=100)
    host_count: int = Field(default=1, ge=1, le=5)
    llm_provider: str = "gemini"
    cover_index: int = 0


class UpdateProjectRequest(BaseModel):
    topic: str | None = Field(default=None, max_length=500)
    audience: str | None = Field(default=None, max_length=500)
    duration_min: int | None = Field(default=None, ge=1, le=180)
    style: str | None = Field(default=None, max_length=100)
    host_count: int | None = Field(default=None, ge=1, le=5)
    status: str | None = None
    step: int | None = None
    progress: int | None = None


class TTSRequest(BaseModel):
    voice: str = "female"
    speed: float = 1.0
    pitch: float = 0.0
    style_prompt: str = ""
    tts_provider: str = "gemini"


class TTSMultiSpeakerRequest(BaseModel):
    speakers: list[dict] = [
        {"name": "主持人A", "voice": "Achird"},
        {"name": "主持人B", "voice": "Kore"},
    ]
    style_prompt: str = ""
    tts_provider: str = "gemini"


class FeedbackRequest(BaseModel):
    score_content: int | None = Field(default=None, ge=1, le=5)
    score_engagement: int | None = Field(default=None, ge=1, le=5)
    score_structure: int | None = Field(default=None, ge=1, le=5)
    text_feedback: str | None = Field(default=None, max_length=2000)


class SegmentEditRequest(BaseModel):
    content: str = Field(max_length=10000)


class AiKeyEntry(BaseModel):
    provider: str  # "gemini", "claude"
    api_key: str | None = None  # plaintext; None = don't change key
    model: str | None = None


class SaveAiSettingsRequest(BaseModel):
    providers: list[AiKeyEntry]
