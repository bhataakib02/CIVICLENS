"""Auth application service — the identity/session business logic.

Implements:
- register (email+password, Argon2id, default role CITIZEN, status ACTIVE,
  auto-creates the 1:1 citizen_profile).
- login (constant-ish error on bad credentials, status check, last_login_at).
- refresh with rotation + reuse detection (a presented token that is already
  revoked/rotated => revoke the whole family, treat as compromise).
- logout (revoke current, or all sessions).

Owns the transaction: commits on success, rolls back on failure.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.exceptions import (
    AccountExistsError,
    AccountSuspendedError,
    AuthenticationError,
    InvalidTokenError,
)
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    validate_password_policy,
    verify_password,
)
from app.models.citizen_profile import CitizenProfile
from app.models.enums import UserRole, UserStatus
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.modules.audit.service import AuditAction, AuditService
from app.modules.auth.repository import AuthRepository
from app.schemas.auth import TokenPair


def normalize_email(email: str) -> str:
    """Normalize an email for storage/lookup: trim + lowercase."""
    return email.strip().lower()


class AuthService:
    def __init__(self, session: Session, settings: Settings | None = None) -> None:
        self._session = session
        self._repo = AuthRepository(session)
        self._audit = AuditService(session)
        self._settings = settings or get_settings()

    # ------------------------------------------------------------------ #
    # Registration
    # ------------------------------------------------------------------ #
    def register(self, email: str, password: str, *, ip: str | None = None) -> TokenPair:
        normalized = normalize_email(email)
        validate_password_policy(password, self._settings)

        if self._repo.get_user_by_email(normalized) is not None:
            raise AccountExistsError()

        user = User(
            email=normalized,
            password_hash=hash_password(password),
            role=UserRole.CITIZEN,
            status=UserStatus.ACTIVE,
        )
        # 1:1 citizen profile is required by the data model (FR-PROFILE).
        user.profile = CitizenProfile(current_version_no=0)

        try:
            self._repo.add_user(user)
            self._session.flush()
        except IntegrityError as exc:
            # Unique violation on a concurrent duplicate registration.
            self._session.rollback()
            raise AccountExistsError() from exc

        self._audit.record(
            action=AuditAction.REGISTER,
            entity_type="user",
            entity_id=user.id,
            actor_user_id=user.id,
            ip=ip,
        )
        tokens = self._issue_tokens(user)
        self._session.commit()
        return tokens

    # ------------------------------------------------------------------ #
    # Login
    # ------------------------------------------------------------------ #
    def login(self, email: str, password: str, *, ip: str | None = None) -> TokenPair:
        normalized = normalize_email(email)
        user = self._repo.get_user_by_email(normalized)

        # Uniform failure: do not reveal whether the email exists. Perform a
        # dummy verify to reduce timing signal when the user is absent.
        if user is None or not user.password_hash:
            _dummy_verify()
            self._audit.record(
                action=AuditAction.LOGIN_FAILURE,
                entity_type="user",
                entity_id=None,
                actor_user_id=None,
                ip=ip,
            )
            self._session.commit()
            raise AuthenticationError()

        if not verify_password(password, user.password_hash):
            self._audit.record(
                action=AuditAction.LOGIN_FAILURE,
                entity_type="user",
                entity_id=user.id,
                actor_user_id=user.id,
                ip=ip,
            )
            self._session.commit()
            raise AuthenticationError()

        if user.status is UserStatus.SUSPENDED:
            self._audit.record(
                action=AuditAction.LOGIN_FAILURE,
                entity_type="user",
                entity_id=user.id,
                actor_user_id=user.id,
                diff={"reason": "suspended"},
                ip=ip,
            )
            self._session.commit()
            raise AccountSuspendedError()

        user.last_login_at = datetime.now(timezone.utc)
        self._audit.record(
            action=AuditAction.LOGIN_SUCCESS,
            entity_type="user",
            entity_id=user.id,
            actor_user_id=user.id,
            ip=ip,
        )
        tokens = self._issue_tokens(user)
        self._session.commit()
        return tokens

    # ------------------------------------------------------------------ #
    # Refresh (rotation + reuse detection)
    # ------------------------------------------------------------------ #
    def refresh(self, raw_refresh_token: str, *, ip: str | None = None) -> TokenPair:
        now = datetime.now(timezone.utc)
        token_hash = hash_refresh_token(raw_refresh_token)
        stored = self._repo.get_refresh_token_by_hash(token_hash)

        if stored is None:
            raise InvalidTokenError("Refresh token not recognized.")

        user = self._repo.get_user_by_id(stored.user_id)

        # Reuse detection: a token that exists but is already revoked (i.e.
        # previously rotated out or logged out) being presented again is a
        # strong signal of theft. Revoke the entire active family.
        if stored.revoked_at is not None:
            self._revoke_all(stored.user_id, now)
            self._audit.record(
                action=AuditAction.TOKEN_REUSE_DETECTED,
                entity_type="refresh_token",
                entity_id=stored.id,
                actor_user_id=stored.user_id,
                ip=ip,
            )
            self._session.commit()
            raise InvalidTokenError("Refresh token has already been used.")

        if stored.expires_at <= now:
            raise InvalidTokenError("Refresh token has expired.")

        if user is None or user.status is UserStatus.SUSPENDED:
            # Do not mint tokens for a missing/suspended account.
            self._revoke_all(stored.user_id, now)
            self._session.commit()
            raise InvalidTokenError("Refresh token is no longer valid.")

        # Rotate: revoke the presented token and issue a new one chained to it.
        stored.revoked_at = now
        access_token, expires_in = create_access_token(
            subject=str(user.id), role=user.role.value, settings=self._settings
        )
        new_refresh_raw = self._persist_refresh_token(user.id, now, rotated_from=stored.id)

        self._audit.record(
            action=AuditAction.TOKEN_REFRESH,
            entity_type="refresh_token",
            entity_id=stored.id,
            actor_user_id=user.id,
            ip=ip,
        )
        self._session.commit()
        return TokenPair(
            access_token=access_token,
            refresh_token=new_refresh_raw,
            token_type="bearer",
            expires_in=expires_in,
        )

    # ------------------------------------------------------------------ #
    # Logout
    # ------------------------------------------------------------------ #
    def logout(
        self, raw_refresh_token: str | None, user_id: uuid.UUID, *, all_sessions: bool, ip: str | None = None
    ) -> None:
        now = datetime.now(timezone.utc)
        if all_sessions:
            self._revoke_all(user_id, now)
        elif raw_refresh_token:
            stored = self._repo.get_refresh_token_by_hash(hash_refresh_token(raw_refresh_token))
            if stored is not None and stored.user_id == user_id and stored.revoked_at is None:
                stored.revoked_at = now
        self._audit.record(
            action=AuditAction.LOGOUT,
            entity_type="user",
            entity_id=user_id,
            actor_user_id=user_id,
            diff={"all_sessions": all_sessions},
            ip=ip,
        )
        self._session.commit()

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _issue_tokens(self, user: User) -> TokenPair:
        now = datetime.now(timezone.utc)
        access_token, expires_in = create_access_token(
            subject=str(user.id), role=user.role.value, settings=self._settings
        )
        refresh_raw = self._persist_refresh_token(user.id, now)
        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_raw,
            token_type="bearer",
            expires_in=expires_in,
        )

    def _persist_refresh_token(
        self, user_id: uuid.UUID, now: datetime, rotated_from: uuid.UUID | None = None
    ) -> str:
        raw = generate_refresh_token()
        token = RefreshToken(
            user_id=user_id,
            token_hash=hash_refresh_token(raw),
            expires_at=now + timedelta(days=self._settings.refresh_token_expire_days),
            rotated_from_id=rotated_from,
        )
        self._repo.add_refresh_token(token)
        return raw

    def _revoke_all(self, user_id: uuid.UUID, now: datetime) -> None:
        for token in self._repo.active_refresh_tokens_for_user(user_id, now):
            token.revoked_at = now
        self._session.flush()


# A precomputed Argon2id hash of a random value, used to equalize timing on
# login attempts for non-existent accounts (mitigates user enumeration).
_DUMMY_HASH = hash_password("dummy-password-for-timing-equalization-x9")


def _dummy_verify() -> None:
    verify_password("wrong", _DUMMY_HASH)
