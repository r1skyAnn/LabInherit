"""Cross-cutting security primitives (password hashing, JWT).

S0 just exposes the modules; the decorators and helpers get wired in S1.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# bcrypt with safe rounds; passlib reads this lazily
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(
    subject: str | int,
    *,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Issue a signed JWT. `subject` becomes the `sub` claim."""
    now = datetime.now(tz=timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=settings.JWT_EXPIRE_MINUTES))
    payload: dict[str, Any] = {
        "sub": str(subject),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate. Raises `jose.JWTError` on failure."""
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError as e:
        raise JWTError(f"Invalid token: {e}") from e


# ============================================================
# Password-reset tokens (purpose-bound JWTs)
# ============================================================
PASSWORD_RESET_PURPOSE = "password_reset"
PASSWORD_RESET_EXPIRE_MINUTES = 30


def create_password_reset_token(user_id: int) -> str:
    """Issue a one-time token for resetting a password.

    The token carries a `purpose` claim and a 30-minute expiry. The same
    user can request multiple tokens; each is independently valid until
    its own expiry. We rely on short TTL + the password change itself
    to invalidate older tokens.
    """
    now = datetime.now(tz=timezone.utc)
    expire = now + timedelta(minutes=PASSWORD_RESET_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "purpose": PASSWORD_RESET_PURPOSE,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_password_reset_token(token: str) -> dict[str, Any]:
    """Decode and assert the purpose. Raises JWTError on any failure."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError as e:
        raise JWTError(f"Invalid token: {e}") from e
    if payload.get("purpose") != PASSWORD_RESET_PURPOSE:
        raise JWTError("Token purpose mismatch")
    return payload
