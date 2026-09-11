"""Password hashing + JWT tokens. Never log secrets."""
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
import secrets

from backend.app.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
settings = get_settings()


def hash_password(password: str) -> str:
    # bcrypt max 72 bytes
    pw = password[:72]
    return pwd_context.hash(pw)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(plain[:72], hashed)
    except Exception:
        return False


def create_access_token(sub: str, role: str, extra: dict | None = None) -> str:
    payload = {"sub": sub, "role": role, "type": "access"}
    if extra:
        payload.update(extra)
    payload["exp"] = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload["iat"] = datetime.now(timezone.utc)
    payload["jti"] = secrets.token_hex(8)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(sub: str) -> str:
    payload = {"sub": sub, "type": "refresh"}
    payload["exp"] = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    payload["iat"] = datetime.now(timezone.utc)
    payload["jti"] = secrets.token_hex(8)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


def generate_token(length: int = 32) -> str:
    return secrets.token_urlsafe(length)
