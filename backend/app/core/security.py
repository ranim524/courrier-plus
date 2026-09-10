import secrets
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings
from app.core.exceptions import UnauthorizedError
from app.utils.hashing import sha256_of_text

settings = get_settings()

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _pwd_context.verify(password, password_hash)


def create_admin_jwt(admin_id: str, email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expiration_minutes)
    payload = {"sub": admin_id, "email": email, "exp": expire, "type": "admin"}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_admin_jwt(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise UnauthorizedError("Invalid or expired authentication token") from exc
    if payload.get("type") != "admin":
        raise UnauthorizedError("Invalid authentication token")
    return payload


def generate_secure_token() -> str:
    """Cryptographically secure random token for recipient access links. Never persisted raw."""
    return secrets.token_urlsafe(32)


def hash_token(raw_token: str) -> str:
    return sha256_of_text(raw_token)


def safe_token_preview(raw_token: str) -> str:
    """First chars only, safe for debug logs. Never log the full token."""
    return raw_token[:8] + "..."
