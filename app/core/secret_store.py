import base64
import hashlib
import hmac
import secrets
from typing import Optional

from app.core.config import get_settings
from app.core.security import get_admin_api_token


SECRET_PREFIX = "sealed:v1:"


def _secret_material() -> bytes:
    settings = get_settings()
    raw = settings.settings_encryption_secret.strip() if settings.settings_encryption_secret else ""
    if not raw:
        raw = f"{settings.app_name}:{settings.instance_id}:{get_admin_api_token()}"
    return hashlib.sha256(raw.encode("utf-8")).digest()


def is_secret_sealed(value: Optional[str]) -> bool:
    return bool(value and value.startswith(SECRET_PREFIX))


def seal_secret(plaintext: str) -> str:
    if not plaintext:
        return ""
    if is_secret_sealed(plaintext):
        return plaintext

    data = plaintext.encode("utf-8")
    salt = secrets.token_bytes(16)
    key_stream = hashlib.pbkdf2_hmac("sha256", _secret_material(), salt, 120000, dklen=len(data))
    ciphertext = bytes(left ^ right for left, right in zip(data, key_stream))
    digest = hmac.new(_secret_material(), salt + ciphertext, hashlib.sha256).digest()
    payload = base64.urlsafe_b64encode(salt + ciphertext + digest).decode("utf-8")
    return f"{SECRET_PREFIX}{payload}"


def unseal_secret(value: Optional[str]) -> str:
    if not value:
        return ""
    if not is_secret_sealed(value):
        return value

    payload = value[len(SECRET_PREFIX) :]
    raw = base64.urlsafe_b64decode(payload.encode("utf-8"))
    if len(raw) < 48:
        raise ValueError("Invalid sealed secret payload")

    salt = raw[:16]
    digest = raw[-32:]
    ciphertext = raw[16:-32]
    expected = hmac.new(_secret_material(), salt + ciphertext, hashlib.sha256).digest()
    if not hmac.compare_digest(digest, expected):
        raise ValueError("Invalid sealed secret signature")

    key_stream = hashlib.pbkdf2_hmac("sha256", _secret_material(), salt, 120000, dklen=len(ciphertext))
    plaintext = bytes(left ^ right for left, right in zip(ciphertext, key_stream))
    return plaintext.decode("utf-8")
