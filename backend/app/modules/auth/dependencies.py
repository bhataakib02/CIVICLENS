"""Reusable authentication/authorization dependencies.

Every module derives the authenticated principal from these — routers must
NOT re-implement token parsing. Ownership (object-level) checks live in the
service layer (docs/security/authorization-model.md), these dependencies
establish the *identity* and *role*.
"""
from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import (
    AccountSuspendedError,
    InvalidTokenError,
    PermissionDeniedError,
)
from app.core.security import decode_access_token
from app.db.session import db_session
from app.models.enums import UserStatus
from app.models.user import User
from app.modules.auth.repository import AuthRepository

# auto_error=False so we raise our own contract-shaped 401 instead of Starlette's.
_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    """Lightweight authenticated principal passed to routers/services."""

    id: uuid.UUID
    role: str
    status: UserStatus


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    session: Session = Depends(db_session),
) -> CurrentUser:
    """Validate the bearer access token and load the live account.

    Raises InvalidTokenError (401) for missing/invalid/expired tokens and for
    a subject that no longer exists; AccountSuspendedError (403) for suspended
    accounts (a valid token must not outlive a suspension).
    """
    if credentials is None or not credentials.credentials:
        raise InvalidTokenError("Missing bearer token.")

    claims = decode_access_token(credentials.credentials)
    try:
        user_id = uuid.UUID(str(claims["sub"]))
    except (KeyError, ValueError) as exc:
        raise InvalidTokenError("Malformed token subject.") from exc

    user: User | None = AuthRepository(session).get_user_by_id(user_id)
    if user is None:
        raise InvalidTokenError("Account no longer exists.")
    if user.status is UserStatus.SUSPENDED:
        raise AccountSuspendedError()

    return CurrentUser(id=user.id, role=user.role.value, status=user.status)


# Alias with an intention-revealing name (prompt §9).
def require_authenticated_user(
    current: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    return current


def require_role(*allowed_roles: str) -> Callable[..., CurrentUser]:
    """Dependency factory enforcing RBAC (role membership)."""

    allowed = set(allowed_roles)

    def _dependency(current: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current.role not in allowed:
            raise PermissionDeniedError()
        return current

    return _dependency
