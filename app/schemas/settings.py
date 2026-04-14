from datetime import datetime
from typing import List, Optional

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
    openai_api_key: Optional[str] = None
    clear_gemini_api_key: bool = False
    clear_anthropic_api_key: bool = False
    clear_openai_api_key: bool = False


class AISettingsResponse(AISettingsBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_gemini_key_configured: bool
    customer_anthropic_key_configured: bool
    customer_openai_key_configured: bool
    platform_gemini_key_configured: bool
    platform_anthropic_key_configured: bool
    platform_openai_key_configured: bool
    gemini_key_configured: bool
    anthropic_key_configured: bool
    openai_key_configured: bool
    gemini_key_masked: str
    anthropic_key_masked: str
    openai_key_masked: str
    effective_gemini_credential_source: str
    effective_anthropic_credential_source: str
    effective_openai_credential_source: str
    credential_policy_label: str
    gemini_key_updated_at: Optional[datetime] = None
    anthropic_key_updated_at: Optional[datetime] = None
    openai_key_updated_at: Optional[datetime] = None
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


class SettingsAuditLogResponse(BaseModel):
    id: int
    area: str
    action: str
    actor: str
    instance_id: str
    details: str
    created_at: datetime


class SettingsSecurityMetaResponse(BaseModel):
    instance_name: str
    instance_id: str
    admin_username: str
    uses_default_password: bool


class SettingsAuditListResponse(BaseModel):
    items: List[SettingsAuditLogResponse]
