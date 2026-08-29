"""Document intelligence models.

Reuses data-dictionary.md `documents` + `document_extractions`, and adds
`document_processing_jobs`, `document_extracted_fields`, `document_verifications`
(prompt §39). Ownership is via citizen_profile_id (data-dictionary). File bytes
live in object storage (ADR-005); only a non-guessable storage_key + metadata
are stored here.

DOCUMENTED EXTENSIONS beyond the flat data-dictionary columns (recorded in the
migration docstring; required by prompt §12, §40, §41):
  documents: filename, mime_type, size_bytes, sha256, uploaded_by, processed_at,
    verified_at, created_at, updated_at, deleted_at (soft-delete), richer status.
  document_extractions: document_type, model_version, status, page_count,
    identity_match, created_at.
  document_extracted_fields: full provenance/confidence/normalization model.
  document_verifications: reviewer + outcome + correction audit.

Document-level status (documents.status) is kept SEPARATE from processing-job
status (document_processing_jobs.status) per prompt §41.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, uuid_pk
from app.models.enums import (
    ConfidenceLevel,
    DocumentStatus,
    DocumentType,
    FactSource,
    FieldValueType,
    FieldVerificationStatus,
    ProcessingJobStatus,
)

if TYPE_CHECKING:
    from app.models.citizen_profile import CitizenProfile


def _enum_col(py_enum, name):
    return Enum(
        py_enum,
        name=name,
        native_enum=True,
        validate_strings=True,
        values_callable=lambda enum: [m.value for m in enum],
    )


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = uuid_pk()
    citizen_profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("citizen_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    document_type: Mapped[DocumentType] = mapped_column(
        _enum_col(DocumentType, "document_type"), nullable=False
    )
    status: Mapped[DocumentStatus] = mapped_column(
        _enum_col(DocumentStatus, "document_status"),
        default=DocumentStatus.UPLOADING,
        nullable=False,
        index=True,
    )
    # Object-storage key — NEVER a public URL, never exposed to clients.
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sha256: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    uploaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    profile: Mapped["CitizenProfile"] = relationship()
    jobs: Mapped[list["DocumentProcessingJob"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
    extractions: Mapped[list["DocumentExtraction"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
    verifications: Mapped[list["DocumentVerification"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class DocumentProcessingJob(Base):
    __tablename__ = "document_processing_jobs"

    id: Mapped[uuid.UUID] = uuid_pk()
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[ProcessingJobStatus] = mapped_column(
        _enum_col(ProcessingJobStatus, "processing_job_status"),
        default=ProcessingJobStatus.PENDING,
        nullable=False,
        index=True,
    )
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_detail: Mapped[str | None] = mapped_column(Text, nullable=True)  # PII-safe only
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    document: Mapped["Document"] = relationship(back_populates="jobs")


class DocumentExtraction(Base):
    __tablename__ = "document_extractions"

    id: Mapped[uuid.UUID] = uuid_pk()
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # data-dictionary columns
    extracted_fields: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)  # PII
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    verified_by_citizen: Mapped[bool] = mapped_column(nullable=False, default=False)
    # extensions
    classified_type: Mapped[DocumentType | None] = mapped_column(
        _enum_col(DocumentType, "document_type"), nullable=True
    )
    classification_confidence: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    ocr_provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    extraction_provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    identity_match: Mapped[bool | None] = mapped_column(nullable=True)
    conflicts: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    extracted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    document: Mapped["Document"] = relationship(back_populates="extractions")
    fields: Mapped[list["DocumentExtractedField"]] = relationship(
        back_populates="extraction", cascade="all, delete-orphan"
    )


class DocumentExtractedField(Base):
    __tablename__ = "document_extracted_fields"

    id: Mapped[uuid.UUID] = uuid_pk()
    extraction_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("document_extractions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    field_name: Mapped[str] = mapped_column(String(64), nullable=False)
    value_type: Mapped[FieldValueType] = mapped_column(
        _enum_col(FieldValueType, "field_value_type"), nullable=False
    )
    raw_value: Mapped[str | None] = mapped_column(Text, nullable=True)  # PII, original OCR text
    normalized_value: Mapped[str | None] = mapped_column(Text, nullable=True)  # PII
    confidence: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)
    confidence_level: Mapped[ConfidenceLevel] = mapped_column(
        _enum_col(ConfidenceLevel, "confidence_level"), nullable=False
    )
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    text_span: Mapped[str | None] = mapped_column(Text, nullable=True)  # PII
    bounding_box: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # null if unavailable
    source: Mapped[FactSource] = mapped_column(
        _enum_col(FactSource, "fact_source"), default=FactSource.DOCUMENT_EXTRACTED, nullable=False
    )
    verification_status: Mapped[FieldVerificationStatus] = mapped_column(
        _enum_col(FieldVerificationStatus, "field_verification_status"),
        default=FieldVerificationStatus.AUTO_ACCEPTED,
        nullable=False,
    )
    # user correction NEVER overwrites raw_value/normalized_value (prompt §31).
    verified_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    extraction: Mapped["DocumentExtraction"] = relationship(back_populates="fields")


class DocumentVerification(Base):
    __tablename__ = "document_verifications"

    id: Mapped[uuid.UUID] = uuid_pk()
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    verified_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    outcome: Mapped[FieldVerificationStatus] = mapped_column(
        _enum_col(FieldVerificationStatus, "field_verification_status"), nullable=False
    )
    correction_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    corrected_fields: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    verified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    document: Mapped["Document"] = relationship(back_populates="verifications")
