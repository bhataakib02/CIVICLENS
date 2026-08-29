"""Application workflow + case-management models.

Reuses data-dictionary.md `applications`, `application_documents` (join),
`application_status_history`; adds `application_submissions`,
`application_assignments`, `application_actions` (prompt §40).

CORE PRINCIPLE (prompt §2, §4, §10, §32): an application is a HISTORICAL
record. It pins the exact `scheme_version_id` and an immutable
`eligibility_snapshot` (JSONB copy of the decision + engine_version +
rule_results + evaluated_facts + timestamp) referencing the `eligibility_checks`
row. A later scheme version never mutates a submitted application.

DOCUMENTED EXTENSIONS beyond the flat data-dictionary columns (recorded in the
migration docstring): applications.application_number (human ref),
eligibility_check_id, eligibility_snapshot, assigned_case_worker_id, updated_at,
completed_at, deadline_at; status_history.metadata; the submissions/assignments/
actions tables.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, uuid_pk
from app.models.enums import (
    ActionRequiredStatus,
    ApplicationStatus,
    AssignmentAction,
    ReviewAction,
    SubmissionMethod,
    SubmissionStatus,
)

if TYPE_CHECKING:
    from app.models.document import Document


def _enum_col(py_enum, name):
    return Enum(
        py_enum,
        name=name,
        native_enum=True,
        validate_strings=True,
        values_callable=lambda enum: [m.value for m in enum],
    )


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint("application_number", name="uq_application_number"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    # Human-readable, non-sensitive reference (prompt §28): CL-YYYY-NNNNNNNN.
    application_number: Mapped[str] = mapped_column(String(32), nullable=False)
    citizen_profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("citizen_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Pinned scheme version — never changes after creation (immutability).
    scheme_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("scheme_versions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    # Reference + immutable snapshot of the eligibility evaluation used.
    eligibility_check_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("eligibility_checks.id", ondelete="SET NULL"), nullable=True
    )
    eligibility_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    status: Mapped[ApplicationStatus] = mapped_column(
        _enum_col(ApplicationStatus, "application_status"),
        default=ApplicationStatus.DRAFT,
        nullable=False,
        index=True,
    )
    scheme_specific_answers: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    assigned_case_worker_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    deadline_at: Mapped[date | None] = mapped_column(Date, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    documents: Mapped[list["ApplicationDocument"]] = relationship(
        back_populates="application", cascade="all, delete-orphan"
    )
    history: Mapped[list["ApplicationStatusHistory"]] = relationship(
        back_populates="application", cascade="all, delete-orphan"
    )
    submissions: Mapped[list["ApplicationSubmission"]] = relationship(
        back_populates="application", cascade="all, delete-orphan"
    )
    assignments: Mapped[list["ApplicationAssignment"]] = relationship(
        back_populates="application", cascade="all, delete-orphan"
    )
    actions: Mapped[list["ApplicationAction"]] = relationship(
        back_populates="application", cascade="all, delete-orphan"
    )


class ApplicationDocument(Base):
    """Join table (data-dictionary): which document instances back an application.

    A document (owned by a citizen) may be reused across applications (prompt §13);
    only a reference is stored, never a copy of the binary object.
    """

    __tablename__ = "application_documents"
    __table_args__ = (
        UniqueConstraint("application_id", "document_id", name="pk_application_documents"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    application_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_type: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    application: Mapped["Application"] = relationship(back_populates="documents")
    document: Mapped["Document"] = relationship()


class ApplicationStatusHistory(Base):
    """Append-only status history (data-dictionary; immutable — prompt §26)."""

    __tablename__ = "application_status_history"

    id: Mapped[uuid.UUID] = uuid_pk()
    application_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    from_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    to_status: Mapped[str] = mapped_column(String(32), nullable=False)
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    application: Mapped["Application"] = relationship(back_populates="history")


class ApplicationSubmission(Base):
    """Submission record (prompt §19). One active submission per application
    (enforced by a partial unique index in the migration) — idempotency +
    concurrency safety.
    """

    __tablename__ = "application_submissions"

    id: Mapped[uuid.UUID] = uuid_pk()
    application_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[SubmissionStatus] = mapped_column(
        _enum_col(SubmissionStatus, "submission_status"),
        default=SubmissionStatus.PENDING,
        nullable=False,
    )
    submission_method: Mapped[SubmissionMethod] = mapped_column(
        _enum_col(SubmissionMethod, "submission_method"), nullable=False
    )
    external_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    submitted_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    request_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    response_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # no secrets
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    application: Mapped["Application"] = relationship(back_populates="submissions")


class ApplicationAssignment(Base):
    """Case-worker assignment history (prompt §23)."""

    __tablename__ = "application_assignments"

    id: Mapped[uuid.UUID] = uuid_pk()
    application_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    action: Mapped[AssignmentAction] = mapped_column(
        _enum_col(AssignmentAction, "assignment_action"), nullable=False
    )
    case_worker_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    previous_case_worker_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    assigned_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    application: Mapped["Application"] = relationship(back_populates="assignments")


class ApplicationAction(Base):
    """Reviewer 'action required' items for the citizen (prompt §25)."""

    __tablename__ = "application_actions"

    id: Mapped[uuid.UUID] = uuid_pk()
    application_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    required_items: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[ActionRequiredStatus] = mapped_column(
        _enum_col(ActionRequiredStatus, "action_required_status"),
        default=ActionRequiredStatus.OPEN,
        nullable=False,
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    application: Mapped["Application"] = relationship(back_populates="actions")
