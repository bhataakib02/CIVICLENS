"""Refresh token model — server-side, hashed, rotating, revocable.

DOCUMENTED EXTENSION: not in the data-dictionary. Required by FR-AUTH-3
(rotating, revocable refresh tokens) and the prompt's refresh-token section.
Only a SHA-256 hash of the opaque token is stored (never the raw token).
Supports rotation (rotated_from_id chain) and reuse detection (a presented
token that is already revoked/rotated is treated as compromise).
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, uuid_pk

if TYPE_CHECKING:
    from app.models.user import User


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # SHA-256 hex digest of the opaque token — unique so a token maps to one row.
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    rotated_from_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("refresh_tokens.id", ondelete="SET NULL"), nullable=True
    )

    user: Mapped["User"] = relationship(back_populates="refresh_tokens")

    def is_active(self, now: datetime) -> bool:
        return self.revoked_at is None and self.expires_at > now
