from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_env: str = "local"
    app_name: str = "feedback-agent-mvp"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    streamlit_port: int = 8501
    database_url: str = "sqlite+aiosqlite:///./data/feedback_agent.db"

    default_llm_provider: str = "ollama"
    default_llm_model: str = "llama3.1:8b"
    fallback_llm_provider: str = "gemini"
    fallback_llm_model: str = "gemini-2.5-flash-lite"
    ollama_base_url: str = "http://localhost:11434"
    gemini_api_key: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

@lru_cache
def get_settings() -> Settings:
    return Settings()
