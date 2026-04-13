from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class AISettingsBase(BaseModel):
    credential_mode: str = "platform"
    customer_name: str = ""
    default_provider: str = "gemini"
    default_model: str = "gemini-2.5-flash"
    fallback_provider: str = "anthropic"
    fallback_model: str = "claude-3-5-haiku-20241022"
    enable_platform_fallback: bool = True
    notes: str = ""


class AISettingsUpdate(AISettingsBase):
    gemini_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None


class AISettingsResponse(AISettingsBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    gemini_key_configured: bool
    anthropic_key_configured: bool
    gemini_key_masked: str
    anthropic_key_masked: str
    created_at: datetime
    updated_at: datetime


class AISettingsTestRequest(BaseModel):
    provider: str
    model: Optional[str] = None


class AISettingsTestResponse(BaseModel):
    success: bool
    provider: str
    model: str
    credential_source: str
    message: str
