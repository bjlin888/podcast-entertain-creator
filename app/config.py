from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "data/podcast.db"
    anthropic_api_key: str = ""
    gemini_api_key: str = ""
    gemini_tts_model: str = "gemini-2.5-flash-preview-tts"
    cors_origins: str = "http://localhost:5173"
    encryption_key: str = ""  # Fernet key for encrypting user API keys

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
