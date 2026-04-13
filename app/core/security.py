import hashlib
import hmac
from typing import Dict

from fastapi import Header, HTTPException, status

from app.core.config import get_settings


DEFAULT_ADMIN_PASSWORD = "change-me-admin"


def _settings():
    return get_settings()


def get_admin_api_token() -> str:
    settings = _settings()
    if settings.admin_api_token:
        return settings.admin_api_token
    raw = f"{settings.app_name}:{settings.instance_id}:{settings.admin_username}:{settings.admin_password}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def verify_admin_credentials(username: str, password: str) -> bool:
    settings = _settings()
    return hmac.compare_digest(username or "", settings.admin_username) and hmac.compare_digest(
        password or "", settings.admin_password
    )


def is_default_admin_password() -> bool:
    return _settings().admin_password == DEFAULT_ADMIN_PASSWORD


def get_admin_runtime_meta() -> Dict[str, object]:
    settings = _settings()
    return {
        "instance_name": settings.instance_name,
        "instance_id": settings.instance_id,
        "admin_username": settings.admin_username,
        "uses_default_password": is_default_admin_password(),
    }


async def require_admin_api_key(
    x_admin_token: str = Header(default="", alias="X-Admin-Token"),
) -> str:
    expected_token = get_admin_api_token()
    if not hmac.compare_digest(x_admin_token or "", expected_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin authentication required",
        )
    return x_admin_token
