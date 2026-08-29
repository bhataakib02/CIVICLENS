"""Consent management model (prompt §12, §13).

Tracks consent records granted by citizens to agents/CSCs or third-party scopes.
Consent records are auditable and historically preserved:
  - Revoking consent updates `revoked_at` (never deletes or silently overwrites the record).
  - A revoked consent remains historically visible.
  - Queries for active consent check `revoked_at IS NULL`.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, uuid_pk


class ConsentType(str, enum.Enum):
    AGENT_ASSISTANCE = "agent_assistance"
    DATA_SHARING = "data_sharing"
    DOCUMENT_ACCESS = "document_access"
    NOTIFICATION_SUBSCRIPTION = "notification_subscription"


class ConsentRecord(Base):
    __tablename__ = "consent_records"

    id: Mapped[uuid.UUID] = uuid_pk()

    citizen_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("citizen_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )

    consent_type: Mapped[ConsentType] = mapped_column(
        Enum(
            ConsentType,
            name="consent_type",
            native_enum=True,
            validate_strings=True,
            values_callable=lambda enum: [m.value for m in enum],
        ),
        nullable=False,
        index=True,
    )

    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    scope: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    version: Mapped[str] = mapped_column(String(32), nullable=False, default="1.0")

    # The actor (e.g. Agent user ID or Citizen user ID) that recorded/granted the consent
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Agent user ID authorized if this consent delegates authority to an agent/CSC
    agent_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )

    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ConsentRecord id={self.id} type={self.consent_type.value} revoked={self.revoked_at is not None}>"
