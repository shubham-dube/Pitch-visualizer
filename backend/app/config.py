"""
Application configuration using Pydantic Settings.
All values are read from environment variables or .env file.
"""
from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ───────────────────────────────────────────────────────
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    app_title: str = "Pitch Visualizer API"
    app_version: str = "2.0.0"
    app_description: str = "AI-powered storyboard generation from narrative text"

    # ── CORS ──────────────────────────────────────────────────────
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    # ── AI API Keys ───────────────────────────────────────────────
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    google_api_key: str = ""

    # ── Claude ────────────────────────────────────────────────────
    claude_model: str = "claude-opus-4-5"

    # ── DALL-E ────────────────────────────────────────────────────
    dalle_model: str = "dall-e-3"
    dalle_image_size: str = "1792x1024"
    dalle_quality: str = "hd"

    # ── Gemini Imagen ─────────────────────────────────────────────
    gemini_image_model: str = "imagen-3.0-generate-002"

    # ── Generation Defaults ───────────────────────────────────────
    default_image_model: str = "dalle3"
    default_style: str = "cinematic"
    default_panels: int = 5
    min_panels: int = 3
    max_panels: int = 8

    # ── Storage ───────────────────────────────────────────────────
    storage_path: str = "./storage/images"
    static_url_prefix: str = "/static/images"

    # ── Input Limits ──────────────────────────────────────────────
    max_input_text_length: int = 5000
    min_input_text_length: int = 50

    # ── Timeouts ─────────────────────────────────────────────────
    request_timeout_seconds: int = 120
    image_generation_timeout: int = 60

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in valid:
            raise ValueError(f"log_level must be one of {valid}")
        return upper

    @property
    def is_development(self) -> bool:
        return self.environment.lower() == "development"

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance. Use as FastAPI dependency."""
    return Settings()