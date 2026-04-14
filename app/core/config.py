from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "local"
    app_name: str = "feedback-agent-mvp"
    instance_name: str = "local-instance"
    instance_id: str = "local-default"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    streamlit_port: int = 8501
    database_url: str = "sqlite+aiosqlite:///./data/feedback_agent.db"
    api_base_url: str = "http://localhost:8000"
    admin_base_url: str = "http://localhost:8501"
    public_base_url: str = "http://localhost:8000"
    cors_allowed_origins: str = ""
    admin_username: str = "admin"
    admin_password: str = "change-me-admin"
    admin_api_token: str = ""
    admin_session_ttl_minutes: int = 480

    default_llm_provider: str = "gemini"
    default_llm_model: str = "gemini-2.5-flash"
    fallback_llm_provider: str = "anthropic"
    fallback_llm_model: str = "claude-3-5-haiku-20241022"
    gemini_api_key: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        raw = (value or "").strip()
        if raw.startswith("postgres://"):
            return raw.replace("postgres://", "postgresql+asyncpg://", 1)
        if raw.startswith("postgresql://") and "+asyncpg" not in raw:
            return raw.replace("postgresql://", "postgresql+asyncpg://", 1)
        return raw

    @property
    def api_base_url_clean(self) -> str:
        return self.api_base_url.rstrip("/")

    @property
    def admin_base_url_clean(self) -> str:
        return self.admin_base_url.rstrip("/")

    @property
    def public_base_url_clean(self) -> str:
        return self.public_base_url.rstrip("/")

    @property
    def cors_origins(self) -> List[str]:
        configured = [item.strip() for item in self.cors_allowed_origins.split(",") if item.strip()]
        defaults = [
            self.admin_base_url_clean,
            self.api_base_url_clean,
            "http://localhost:8501",
            "http://localhost:8000",
            "http://127.0.0.1:8501",
            "http://127.0.0.1:8000",
        ]
        seen = []
        for origin in configured + defaults:
            if origin and origin not in seen:
                seen.append(origin)
        return seen


@lru_cache
def get_settings() -> Settings:
    return Settings()
