"""Auth persistence layer.

Repositories isolate persistence only — no policy decisions, no HTTP concerns
(docs/backend/repository-pattern.md). No commits here; the service owns the
transaction boundary.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken
from app.models.user import User


class AuthRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    # --- users ---
    def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        return self._session.get(User, user_id)

    def get_user_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        return self._session.scalar(stmt)

    def add_user(self, user: User) -> User:
        self._session.add(user)
        self._session.flush()
        return user

    # --- refresh tokens ---
    def add_refresh_token(self, token: RefreshToken) -> RefreshToken:
        self._session.add(token)
        self._session.flush()
        return token

    def get_refresh_token_by_hash(self, token_hash: str) -> RefreshToken | None:
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        return self._session.scalar(stmt)

    def active_refresh_tokens_for_user(
        self, user_id: uuid.UUID, now: datetime
    ) -> list[RefreshToken]:
        stmt = select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > now,
        )
        return list(self._session.scalars(stmt))
