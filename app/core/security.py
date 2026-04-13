import base64
import hashlib
import hmac
import json
import os
import time
from typing import Dict, Optional, Tuple

from fastapi import Header, HTTPException, status

from app.core.config import get_settings


DEFAULT_ADMIN_PASSWORD = "change-me-admin"
PASSWORD_ITERATIONS = 120000


def _settings():
    return get_settings()


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def _b64decode(raw: str) -> bytes:
    padding = "=" * (-len(raw) % 4)
    return base64.urlsafe_b64decode((raw + padding).encode("utf-8"))


def get_admin_api_token() -> str:
    settings = _settings()
    if settings.admin_api_token:
        return settings.admin_api_token
    raw = f"{settings.app_name}:{settings.instance_id}:{settings.admin_username}:{settings.admin_password}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _session_signing_secret() -> str:
    settings = _settings()
    raw = f"{settings.app_name}:{settings.instance_id}:{get_admin_api_token()}:{settings.admin_password}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _sign_session_payload(payload_text: str) -> str:
    return hmac.new(
        _session_signing_secret().encode("utf-8"),
        payload_text.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def issue_admin_session_token(actor: str, source: str) -> str:
    payload = {
        "sub": actor,
        "src": source,
        "iat": int(time.time()),
    }
    payload_text = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    encoded_payload = _b64encode(payload_text.encode("utf-8"))
    signature = _sign_session_payload(payload_text)
    return f"session.{encoded_payload}.{signature}"


def verify_admin_session_token(token: str) -> Optional[Dict[str, str]]:
    if not token or not token.startswith("session."):
        return None
    parts = token.split(".", 2)
    if len(parts) != 3:
        return None
    _, encoded_payload, provided_signature = parts
    try:
        payload_text = _b64decode(encoded_payload).decode("utf-8")
        expected_signature = _sign_session_payload(payload_text)
        if not hmac.compare_digest(provided_signature, expected_signature):
            return None
        payload = json.loads(payload_text)
        if not isinstance(payload, dict):
            return None
        return {
            "actor": str(payload.get("sub") or ""),
            "source": str(payload.get("src") or "session"),
        }
    except Exception:
        return None


def hash_password(password: str, salt: Optional[str] = None) -> str:
    salt_bytes = bytes.fromhex(salt) if salt else os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        (password or "").encode("utf-8"),
        salt_bytes,
        PASSWORD_ITERATIONS,
    )
    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${salt_bytes.hex()}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        scheme, iterations, salt_hex, digest_hex = stored_hash.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        computed = hashlib.pbkdf2_hmac(
            "sha256",
            (password or "").encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iterations),
        ).hex()
        return hmac.compare_digest(computed, digest_hex)
    except Exception:
        return False


def verify_bootstrap_admin_credentials(username: str, password: str) -> bool:
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


def parse_admin_auth_header(token: str) -> Optional[Tuple[str, str]]:
    if not token:
        return None
    if hmac.compare_digest(token, get_admin_api_token()):
        return (_settings().admin_username, "bootstrap_token")
    payload = verify_admin_session_token(token)
    if payload and payload.get("actor"):
        return (payload["actor"], payload.get("source", "session"))
    return None


async def require_admin_api_key(
    x_admin_token: str = Header(default="", alias="X-Admin-Token"),
) -> str:
    actor = parse_admin_auth_header(x_admin_token)
    if not actor:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin authentication required",
        )
    return actor[0]
