"""Security primitives: password hashing, JWT, refresh-token material.

- Passwords: Argon2id (argon2-cffi). Never SHA256, never plaintext.
- Access tokens: short-lived signed JWTs with sub/role/iat/exp/jti/iss/type.
- Refresh tokens: opaque high-entropy secrets; only a SHA-256 hash is stored
  server-side (never the raw token) — see docs/security/authentication-security.md.
"""
from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2 import exceptions as argon2_exceptions

from app.core.config import Settings, get_settings
from app.core.exceptions import InvalidTokenError, ValidationError

# Argon2id is the default variant for argon2-cffi's PasswordHasher.
_password_hasher = PasswordHasher()

ACCESS_TOKEN_TYPE = "access"


# --------------------------------------------------------------------------- #
# Password hashing
# --------------------------------------------------------------------------- #
def hash_password(password: str) -> str:
    """Hash a plaintext password with Argon2id. Returns the encoded hash."""
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a stored Argon2id hash."""
    try:
        return _password_hasher.verify(password_hash, password)
    except (
        argon2_exceptions.VerifyMismatchError,
        argon2_exceptions.VerificationError,
        argon2_exceptions.InvalidHashError,
    ):
        return False


def password_needs_rehash(password_hash: str) -> bool:
    """True if the stored hash uses outdated parameters and should be upgraded."""
    try:
        return _password_hasher.check_needs_rehash(password_hash)
    except argon2_exceptions.InvalidHashError:
        return True


# --------------------------------------------------------------------------- #
# Password policy
# --------------------------------------------------------------------------- #
def validate_password_policy(password: str, settings: Settings | None = None) -> None:
    """Reject obviously weak passwords. Raises ValidationError on failure."""
    settings = settings or get_settings()
    errors: list[dict] = []
    min_len = settings.password_min_length

    if not isinstance(password, str) or len(password) < min_len:
        errors.append(
            {"field": "password", "message": f"Password must be at least {min_len} characters."}
        )
    else:
        classes = [
            any(c.islower() for c in password),
            any(c.isupper() for c in password),
            any(c.isdigit() for c in password),
            any(not c.isalnum() for c in password),
        ]
        if sum(classes) < 3:
            errors.append(
                {
                    "field": "password",
                    "message": (
                        "Password must include at least three of: lowercase, uppercase, "
                        "digit, symbol."
                    ),
                }
            )
        if password.lower() in _COMMON_WEAK_PASSWORDS:
            errors.append({"field": "password", "message": "Password is too common."})

    if errors:
        raise ValidationError("Password does not meet the security policy.", field_errors=errors)


_COMMON_WEAK_PASSWORDS = frozenset(
    {
        "password123456",
        "123456789012",
        "qwertyuiop12",
        "changeme1234",
        "administrator",
    }
)


# --------------------------------------------------------------------------- #
# JWT access tokens
# --------------------------------------------------------------------------- #
def create_access_token(
    *,
    subject: str,
    role: str,
    settings: Settings | None = None,
    expires_delta: timedelta | None = None,
) -> tuple[str, int]:
    """Create a signed access JWT.

    Returns (token, expires_in_seconds). Claims: sub, role, iat, exp, jti, iss, type.
    """
    settings = settings or get_settings()
    now = datetime.now(timezone.utc)
    delta = expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    expire = now + delta
    claims: dict[str, Any] = {
        "sub": str(subject),
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "jti": uuid.uuid4().hex,
        "iss": settings.jwt_issuer,
        "type": ACCESS_TOKEN_TYPE,
    }
    token = jwt.encode(claims, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, int(delta.total_seconds())


def decode_access_token(token: str, settings: Settings | None = None) -> dict[str, Any]:
    """Validate signature, issuer, expiry, subject and token type.

    Raises InvalidTokenError on any failure.
    """
    settings = settings or get_settings()
    try:
        claims = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            issuer=settings.jwt_issuer,
            options={"require": ["exp", "iat", "sub", "iss"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise InvalidTokenError("Access token has expired.") from exc
    except jwt.InvalidTokenError as exc:
        raise InvalidTokenError() from exc

    if claims.get("type") != ACCESS_TOKEN_TYPE:
        raise InvalidTokenError("Wrong token type.")
    if not claims.get("sub"):
        raise InvalidTokenError("Token missing subject.")
    return claims


# --------------------------------------------------------------------------- #
# Opaque refresh tokens
# --------------------------------------------------------------------------- #
def generate_refresh_token() -> str:
    """Generate a high-entropy opaque refresh token (never a JWT)."""
    return secrets.token_urlsafe(48)


def hash_refresh_token(raw_token: str) -> str:
    """Deterministic SHA-256 hash for server-side storage/lookup of refresh tokens.

    Deterministic (unlike Argon2) so the token can be looked up by hash; the
    raw token is high-entropy (48 bytes) so a fast hash is acceptable here.
    """
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def hash_ip(ip: str | None, settings: Settings | None = None) -> str | None:
    """Hash an IP for audit metadata (avoid storing raw IPs; see audit-logging.md)."""
    if not ip:
        return None
    settings = settings or get_settings()
    salted = f"{settings.jwt_secret_key}:{ip}".encode("utf-8")
    return hashlib.sha256(salted).hexdigest()[:32]
