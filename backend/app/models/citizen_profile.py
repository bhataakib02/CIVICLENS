"""Citizen profile + profile version history.

Matches data-dictionary.md `citizen_profiles` and `citizen_profile_versions`.
Profile edits are versioned (FR-PROFILE-5): each edit writes an immutable
snapshot row and advances current_version_no.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, uuid_pk

if TYPE_CHECKING:
    from app.models.address import Address
    from app.models.user import User


class CitizenProfile(Base):
    __tablename__ = "citizen_profiles"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )

    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)  # PII
    gender: Mapped[str | None] = mapped_column(String(32), nullable=True)
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    occupation: Mapped[str | None] = mapped_column(String(128), nullable=True)
    declared_annual_income: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2), nullable=True
    )  # PII
    disability_status: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    family_size: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Preferred notification/UI language (prompt §26, §27). Single source of the
    # user's language; default 'en'. Prepared for 'bn'/'hi'.
    preferred_language: Mapped[str] = mapped_column(String(8), nullable=False, default="en")

    current_version_no: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="profile")
    addresses: Mapped[list["Address"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )
    versions: Mapped[list["CitizenProfileVersion"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )


class CitizenProfileVersion(Base):
    __tablename__ = "citizen_profile_versions"

    id: Mapped[uuid.UUID] = uuid_pk()
    citizen_profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("citizen_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)  # PII, immutable
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    profile: Mapped["CitizenProfile"] = relationship(back_populates="versions")
