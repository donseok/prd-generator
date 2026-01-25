from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Settings
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-20250514"

    # Validation
    auto_approve_threshold: float = 0.8
    enable_pm_review: bool = False  # PM 검토 워크플로우 활성화 여부
    enable_conflict_detection: bool = False  # 요구사항 충돌 감지 활성화

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
