import base64
import datetime
import hashlib
import hmac
import json
import os
import time
import secrets
from typing import Dict, Optional, Tuple

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.api.dependencies import get_db_session
from app.models.admin_session import AdminSession
from app.models.admin_user import AdminUser


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


def issue_admin_session_token(actor: str, source: str, session_id: str, expires_at: int) -> str:
    payload = {
        "sub": actor,
        "src": source,
        "jti": session_id,
        "iat": int(time.time()),
        "exp": expires_at,
    }
    payload_text = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    encoded_payload = _b64encode(payload_text.encode("utf-8"))
    signature = _sign_session_payload(payload_text)
    return f"session.{encoded_payload}.{signature}"


def verify_admin_session_token(token: str) -> Optional[Dict[str, object]]:
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
        expires_at = int(payload.get("exp") or 0)
        if expires_at <= int(time.time()):
            return None
        return {
            "actor": str(payload.get("sub") or ""),
            "source": str(payload.get("src") or "session"),
            "session_id": str(payload.get("jti") or ""),
            "expires_at": expires_at,
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
        return (str(payload["actor"]), str(payload.get("source", "session")))
    return None


async def create_admin_session(
    db: AsyncSession,
    actor: str,
    source: str,
    ttl_minutes: Optional[int] = None,
) -> Dict[str, object]:
    ttl = ttl_minutes or _settings().admin_session_ttl_minutes
    session_id = secrets.token_hex(16)
    expires_at = datetime.datetime.utcnow() + datetime.timedelta(minutes=ttl)
    db.add(
        AdminSession(
            id=session_id,
            actor_username=actor,
            source=source,
            expires_at=expires_at,
        )
    )
    await db.commit()
    token = issue_admin_session_token(
        actor=actor,
        source=source,
        session_id=session_id,
        expires_at=int(expires_at.timestamp()),
    )
    return {
        "token": token,
        "actor": actor,
        "source": source,
        "expires_at": expires_at,
        "session_id": session_id,
    }


async def revoke_admin_session(db: AsyncSession, token: str) -> bool:
    payload = verify_admin_session_token(token)
    if not payload or not payload.get("session_id"):
        return False
    result = await db.execute(select(AdminSession).where(AdminSession.id == payload["session_id"]))
    session = result.scalar_one_or_none()
    if not session:
        return False
    if session.revoked_at is None:
        session.revoked_at = datetime.datetime.utcnow()
        db.add(session)
        await db.commit()
    return True


async def revoke_admin_sessions_for_actor(db: AsyncSession, actor: str) -> None:
    result = await db.execute(select(AdminSession).where(AdminSession.actor_username == actor, AdminSession.revoked_at.is_(None)))
    sessions = result.scalars().all()
    now = datetime.datetime.utcnow()
    for session in sessions:
        session.revoked_at = now
        db.add(session)
    if sessions:
        await db.commit()


async def purge_expired_admin_sessions(db: AsyncSession) -> None:
    await db.execute(
        delete(AdminSession).where(
            AdminSession.expires_at < datetime.datetime.utcnow(),
        )
    )
    await db.commit()


async def resolve_admin_token(db: AsyncSession, token: str) -> Optional[Tuple[str, str]]:
    if not token:
        return None
    if hmac.compare_digest(token, get_admin_api_token()):
        return (_settings().admin_username, "bootstrap_token")

    payload = verify_admin_session_token(token)
    if not payload:
        return None

    session_id = str(payload.get("session_id") or "")
    actor = str(payload.get("actor") or "")
    source = str(payload.get("source") or "session")
    if not session_id or not actor:
        return None

    result = await db.execute(select(AdminSession).where(AdminSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        return None
    if session.revoked_at is not None:
        return None
    if session.expires_at < datetime.datetime.utcnow():
        return None
    if session.actor_username != actor:
        return None

    if source == "db_user":
        user_result = await db.execute(select(AdminUser).where(AdminUser.username == actor))
        user = user_result.scalar_one_or_none()
        if not user or not user.is_active:
            return None

    return (actor, source)


async def require_admin_api_key(
    x_admin_token: str = Header(default="", alias="X-Admin-Token"),
    db: AsyncSession = Depends(get_db_session),
) -> str:
    actor = await resolve_admin_token(db, x_admin_token)
    if not actor:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin authentication required",
        )
    return actor[0]
