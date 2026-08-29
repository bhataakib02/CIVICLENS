"""OTP application service — phone-based citizen authentication.

Implements the canonical v1.0 citizen auth flow (openapi.yaml):
  POST /auth/otp/request  → OTPService.request_otp
  POST /auth/otp/verify   → OTPService.verify_otp

Security guarantees:
  - OTP plaintext is NEVER logged or stored (only Argon2id hash).
  - Rate limiting: max OTP_MAX_ATTEMPTS_PER_HOUR requests per phone per hour.
  - Attempt limits: max OTP_MAX_ATTEMPTS failed verifies per OTP before lock.
  - Expiry: OTP expires after OTP_EXPIRY_SECONDS (default 300 = 5 minutes).
  - Single-use: once verified, the OTP is marked used and cannot be reused.
  - Replay prevention: used OTPs are rejected even if not expired.
  - Audit events on every request and verify attempt.
  - Phone number normalization before any lookup.

Auto-registration: if a citizen with the given phone number does not exist,
  one is created automatically on successful OTP verify (seamless UX).
  A CitizenProfile is auto-created (1:1 invariant).
"""
from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.exceptions import (
    AppError,
    AuthenticationError,
    ValidationError,
)
from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.models.citizen_profile import CitizenProfile
from app.models.enums import UserRole, UserStatus
from app.models.otp import OTPRequest
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.modules.audit.service import AuditAction, AuditService
from app.modules.auth.otp_provider import OTPProvider, get_otp_provider
from app.modules.auth.repository import AuthRepository
from app.schemas.auth import TokenPair

logger = get_logger("civiclens.auth.otp")

_OTP_LENGTH = 6
_OTP_CHARS = "0123456789"


class OTPRateLimitError(AppError):
    status_code = 429
    code = "OTP_RATE_LIMITED"
    message = "Too many OTP requests. Please wait before requesting another."


class OTPExpiredError(AppError):
    status_code = 401
    code = "OTP_EXPIRED"
    message = "The OTP has expired. Please request a new one."


class OTPInvalidError(AppError):
    status_code = 401
    code = "OTP_INVALID"
    message = "Invalid or already-used OTP."


class OTPMaxAttemptsError(AppError):
    status_code = 401
    code = "OTP_MAX_ATTEMPTS"
    message = "Too many failed attempts. Please request a new OTP."


def _normalize_phone(phone: str) -> str:
    """Normalize a phone number: strip whitespace and non-digit chars except leading +."""
    phone = phone.strip()
    if phone.startswith("+"):
        return "+" + "".join(c for c in phone[1:] if c.isdigit())
    return "".join(c for c in phone if c.isdigit())


def _generate_otp_code(settings: Settings) -> str:
    """Generate a cryptographically secure OTP code.

    In non-production environment with OTP_TEST_FIXED_CODE=true, returns '000000'
    for deterministic test/demo assertions. NEVER fixed in production.
    """
    if not getattr(settings, "is_production", False) and getattr(
        settings, "otp_test_fixed_code", True
    ):
        return "000000"
    return "".join(secrets.choice(_OTP_CHARS) for _ in range(_OTP_LENGTH))


class OTPService:
    def __init__(
        self,
        session: Session,
        settings: Settings | None = None,
        provider: OTPProvider | None = None,
    ) -> None:
        self._session = session
        self._s = settings or get_settings()
        self._repo = AuthRepository(session)
        self._audit = AuditService(session)
        self._provider = provider or get_otp_provider(self._s)

    @property
    def _expiry_seconds(self) -> int:
        return getattr(self._s, "otp_expiry_seconds", 300)

    @property
    def _max_attempts(self) -> int:
        return getattr(self._s, "otp_max_attempts", 5)

    @property
    def _rate_limit_per_hour(self) -> int:
        return getattr(self._s, "otp_rate_limit_per_hour", 5)

    # ------------------------------------------------------------------ #
    # Request OTP
    # ------------------------------------------------------------------ #
    def request_otp(self, phone_number: str, *, ip: str | None = None) -> None:
        """Generate and deliver an OTP for the given phone number.

        Rate-limited per phone number. Does not reveal whether the number is
        registered (consistent behavior for new and existing numbers).
        Returns None — the response is always 202 Accepted.
        """
        normalized = _normalize_phone(phone_number)
        if not normalized or len(normalized) < 7 or len(normalized) > 20:
            raise ValidationError(
                "Invalid phone number format.",
                field_errors=[{"field": "phone_number", "message": "Must be 7–20 digits."}],
            )

        self._check_rate_limit(normalized)

        # Generate + hash OTP — plaintext code goes ONLY to provider delivery.
        code = _generate_otp_code(self._s)
        code_hash = hash_password(code)  # Argon2id — same hasher as passwords

        now = datetime.now(timezone.utc)
        otp_row = OTPRequest(
            phone_number=normalized,
            code_hash=code_hash,
            expires_at=now + timedelta(seconds=self._expiry_seconds),
            ip_address=ip,
        )
        self._session.add(otp_row)
        self._session.flush()

        # Audit before delivery attempt (so we have a record even if delivery fails).
        self._audit.record(
            action=AuditAction.OTP_REQUEST,
            entity_type="otp_request",
            entity_id=otp_row.id,
            actor_user_id=None,
            ip=ip,
        )

        try:
            # Deliver via provider — provider MUST NOT log the code.
            self._provider.deliver(phone_number=normalized, code=code)
        except Exception:
            logger.error(
                "otp_delivery_failed",
                extra={"phone_suffix": normalized[-4:], "provider": self._provider.name},
                exc_info=True,
            )
            # Still commit the OTP row (user may retry delivery via same endpoint).
            # Do not reveal provider failure details to the caller.

        self._session.commit()
        logger.info(
            "otp_requested",
            extra={"phone_suffix": normalized[-4:], "provider": self._provider.name},
        )

    # ------------------------------------------------------------------ #
    # Verify OTP
    # ------------------------------------------------------------------ #
    def verify_otp(self, phone_number: str, code: str, *, ip: str | None = None) -> TokenPair:
        """Verify an OTP code. On success: auto-register if new number, issue tokens.

        On failure: increment attempt count, raise appropriate error.
        """
        normalized = _normalize_phone(phone_number)
        now = datetime.now(timezone.utc)

        # Find the most recent non-expired, non-used OTP for this number.
        otp_row = self._find_valid_otp(normalized, now)

        if otp_row is None:
            self._audit.record(
                action=AuditAction.OTP_VERIFY_FAILURE,
                entity_type="otp_request",
                entity_id=None,
                actor_user_id=None,
                diff={"reason": "no_valid_otp"},
                ip=ip,
            )
            self._session.commit()
            raise OTPExpiredError()

        # Check attempt limit BEFORE verifying (brute-force protection).
        if otp_row.attempt_count >= self._max_attempts:
            self._audit.record(
                action=AuditAction.OTP_VERIFY_FAILURE,
                entity_type="otp_request",
                entity_id=otp_row.id,
                actor_user_id=None,
                diff={"reason": "max_attempts"},
                ip=ip,
            )
            self._session.commit()
            raise OTPMaxAttemptsError()

        # Verify the code hash (constant-time via Argon2).
        if not verify_password(code, otp_row.code_hash):
            otp_row.attempt_count += 1
            self._audit.record(
                action=AuditAction.OTP_VERIFY_FAILURE,
                entity_type="otp_request",
                entity_id=otp_row.id,
                actor_user_id=None,
                diff={"reason": "wrong_code", "attempt": otp_row.attempt_count},
                ip=ip,
            )
            self._session.commit()
            raise OTPInvalidError()

        # Mark OTP as used immediately (replay prevention).
        otp_row.used_at = now

        # Resolve or auto-create the citizen user.
        user = self._resolve_or_create_citizen(normalized, now, ip=ip)

        self._audit.record(
            action=AuditAction.OTP_VERIFY_SUCCESS,
            entity_type="otp_request",
            entity_id=otp_row.id,
            actor_user_id=user.id,
            ip=ip,
        )
        user.last_login_at = now
        tokens = self._issue_tokens(user, now)
        self._session.commit()
        logger.info("otp_verified", extra={"phone_suffix": normalized[-4:]})
        return tokens

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _check_rate_limit(self, normalized_phone: str) -> None:
        """Raise OTPRateLimitError if too many OTPs requested in the last hour."""
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        count = self._session.scalar(
            select(func.count(OTPRequest.id)).where(
                OTPRequest.phone_number == normalized_phone,
                OTPRequest.created_at >= one_hour_ago,
            )
        ) or 0
        if count >= self._rate_limit_per_hour:
            raise OTPRateLimitError()

    def _find_valid_otp(self, phone: str, now: datetime) -> OTPRequest | None:
        """Find the most recent non-expired, non-used OTP for the phone number."""
        stmt = (
            select(OTPRequest)
            .where(
                OTPRequest.phone_number == phone,
                OTPRequest.expires_at > now,
                OTPRequest.used_at.is_(None),
            )
            .order_by(OTPRequest.created_at.desc())
            .limit(1)
        )
        return self._session.scalar(stmt)

    def _resolve_or_create_citizen(
        self, phone: str, now: datetime, *, ip: str | None
    ) -> User:
        """Return existing citizen user or auto-create a new one."""
        user = self._repo.get_user_by_phone(phone)
        if user is not None:
            if user.status is UserStatus.SUSPENDED:
                raise AuthenticationError("Account is suspended.")
            return user

        # Auto-registration: new citizen account with phone number.
        user = User(
            phone_number=phone,
            role=UserRole.CITIZEN,
            status=UserStatus.ACTIVE,
        )
        user.profile = CitizenProfile(current_version_no=0)
        try:
            self._session.add(user)
            self._session.flush()
        except IntegrityError:
            # Race: another concurrent OTP verify created the account.
            self._session.rollback()
            user = self._repo.get_user_by_phone(phone)
            if user is None:
                raise
        self._audit.record(
            action=AuditAction.REGISTER,
            entity_type="user",
            entity_id=user.id,
            actor_user_id=user.id,
            diff={"method": "otp_phone"},
            ip=ip,
        )
        return user

    def _issue_tokens(self, user: User, now: datetime) -> TokenPair:
        access_token, expires_in = create_access_token(
            subject=str(user.id), role=user.role.value, settings=self._s
        )
        raw_refresh = generate_refresh_token()
        token = RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(raw_refresh),
            expires_at=now + timedelta(days=self._s.refresh_token_expire_days),
        )
        self._session.add(token)
        return TokenPair(
            access_token=access_token,
            refresh_token=raw_refresh,
            token_type="bearer",
            expires_in=expires_in,
        )
