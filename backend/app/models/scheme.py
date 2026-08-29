"""Scheme catalog models — matches data-dictionary.md `schemes` + `scheme_versions`.

ADR-004: scheme_versions are the unit of truth. A published version is
immutable; a policy change creates a NEW version, never an in-place edit.
Each version carries an effective_from/effective_to date range.

DOCUMENTED EXTENSION beyond the data-dictionary: schemes.code — a stable,
human-readable scheme code (e.g. "CIVIC-DEMO-001") used for seed data and
admin reference. Nullable + unique. Recorded in the migration docstring.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, uuid_pk
from app.models.enums import SchemeScope, SchemeVersionStatus

if TYPE_CHECKING:
    from app.models.eligibility import EligibilityRule


def _enum_col(py_enum, name):
    return Enum(
        py_enum,
        name=name,
        native_enum=True,
        validate_strings=True,
        values_callable=lambda enum: [m.value for m in enum],
    )


class Scheme(Base):
    __tablename__ = "schemes"

    id: Mapped[uuid.UUID] = uuid_pk()
    canonical_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    # Extension: stable human-readable code.
    code: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    administering_dept: Mapped[str | None] = mapped_column(String(255), nullable=True)
    scope: Mapped[SchemeScope] = mapped_column(_enum_col(SchemeScope, "scheme_scope"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    versions: Mapped[list["SchemeVersion"]] = relationship(
        back_populates="scheme", cascade="all, delete-orphan"
    )


class SchemeVersion(Base):
    __tablename__ = "scheme_versions"

    id: Mapped[uuid.UUID] = uuid_pk()
    scheme_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[SchemeVersionStatus] = mapped_column(
        _enum_col(SchemeVersionStatus, "scheme_version_status"),
        default=SchemeVersionStatus.DRAFT,
        nullable=False,
        index=True,
    )
    benefits_summary: Mapped[str] = mapped_column(Text, nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    # provenance; nullable until the knowledge module (later phase) exists.
    knowledge_source_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # four-eyes: who authored vs who published (FR-ADMIN-2).
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    published_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    scheme: Mapped["Scheme"] = relationship(back_populates="versions")
    rules: Mapped[list["EligibilityRule"]] = relationship(
        back_populates="scheme_version", cascade="all, delete-orphan"
    )
