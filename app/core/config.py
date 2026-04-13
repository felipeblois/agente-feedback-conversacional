from functools import lru_cache

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
    admin_username: str = "admin"
    admin_password: str = "change-me-admin"
    admin_api_token: str = ""

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


@lru_cache
def get_settings() -> Settings:
    return Settings()
