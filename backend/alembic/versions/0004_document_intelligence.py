"""document intelligence + secure evidence pipeline

Creates the document subsystem tables (prompt §39):
  documents, document_processing_jobs, document_extractions,
  document_extracted_fields, document_verifications
plus their enum types.

Document-level status (documents.status) is SEPARATE from processing-job status
(document_processing_jobs.status) per prompt §41.

DOCUMENTED EXTENSIONS beyond docs/database/data-dictionary.md (recorded in the
implementation report):
  documents: uploaded_by, filename, mime_type, size_bytes, sha256, processed_at,
    verified_at, deleted_at, created_at, updated_at, and a richer status enum
    (the original uploaded/processing/verified/rejected values are retained).
  document_extractions: classified_type, classification_confidence, ocr_provider,
    extraction_provider, model_version, page_count, identity_match, conflicts.
  document_extracted_fields: new table (full provenance/confidence/normalization).
  document_verifications: new table (reviewer + outcome + correction audit).

Revision ID: 0004_document_intelligence
Revises: 0003_knowledge_rag_slice
Create Date: 2026-08-29
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_document_intelligence"
down_revision: Union[str, None] = "0003_knowledge_rag_slice"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_DOC_TYPE = (
    "aadhaar", "identity_document", "income_certificate", "residence_proof",
    "caste_certificate", "disability_certificate", "education_certificate",
    "employment_certificate", "land_record", "bank_document", "other",
)
_DOC_STATUS = (
    "uploading", "uploaded", "validating", "processing", "extracted",
    "verification_required", "verified", "validation_failed",
    "processing_failed", "rejected",
)
_JOB_STATUS = ("pending", "processing", "completed", "failed")
_CONF_LEVEL = ("high", "medium", "low")
_FACT_SOURCE = ("user_provided", "document_extracted", "official_source", "system_derived")
_VALUE_TYPE = ("string", "number", "integer", "date", "boolean")
_FIELD_VERIF = ("auto_accepted", "verification_required", "confirmed", "corrected", "rejected")


def _mkenum(bind, name, values):
    postgresql.ENUM(*values, name=name).create(bind, checkfirst=True)
    return postgresql.ENUM(*values, name=name, create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    doc_type = _mkenum(bind, "document_type", _DOC_TYPE)
    doc_status = _mkenum(bind, "document_status", _DOC_STATUS)
    job_status = _mkenum(bind, "processing_job_status", _JOB_STATUS)
    conf_level = _mkenum(bind, "confidence_level", _CONF_LEVEL)
    fact_source = _mkenum(bind, "fact_source", _FACT_SOURCE)
    value_type = _mkenum(bind, "field_value_type", _VALUE_TYPE)
    field_verif = _mkenum(bind, "field_verification_status", _FIELD_VERIF)

    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("citizen_profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("document_type", doc_type, nullable=False),
        sa.Column("status", doc_status, nullable=False, server_default="uploading"),
        sa.Column("storage_key", sa.String(length=512), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=True),
        sa.Column("mime_type", sa.String(length=128), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("sha256", sa.String(length=64), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["citizen_profile_id"], ["citizen_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_documents_citizen_profile_id", "documents", ["citizen_profile_id"])
    op.create_index("ix_documents_status", "documents", ["status"])
    op.create_index("ix_documents_sha256", "documents", ["sha256"])

    op.create_table(
        "document_processing_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", job_status, nullable=False, server_default="pending"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_detail", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_document_processing_jobs_document_id", "document_processing_jobs", ["document_id"])
    op.create_index("ix_document_processing_jobs_status", "document_processing_jobs", ["status"])

    op.create_table(
        "document_extractions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("extracted_fields", postgresql.JSONB(), nullable=False),
        sa.Column("confidence", sa.Numeric(3, 2), nullable=True),
        sa.Column("verified_by_citizen", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("classified_type", doc_type, nullable=True),
        sa.Column("classification_confidence", sa.Numeric(3, 2), nullable=True),
        sa.Column("ocr_provider", sa.String(length=64), nullable=True),
        sa.Column("extraction_provider", sa.String(length=64), nullable=True),
        sa.Column("model_version", sa.String(length=64), nullable=True),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("identity_match", sa.Boolean(), nullable=True),
        sa.Column("conflicts", postgresql.JSONB(), nullable=True),
        sa.Column("extracted_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_document_extractions_document_id", "document_extractions", ["document_id"])

    op.create_table(
        "document_extracted_fields",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("extraction_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("field_name", sa.String(length=64), nullable=False),
        sa.Column("value_type", value_type, nullable=False),
        sa.Column("raw_value", sa.Text(), nullable=True),
        sa.Column("normalized_value", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Numeric(4, 3), nullable=False),
        sa.Column("confidence_level", conf_level, nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("text_span", sa.Text(), nullable=True),
        sa.Column("bounding_box", postgresql.JSONB(), nullable=True),
        sa.Column("source", fact_source, nullable=False, server_default="document_extracted"),
        sa.Column("verification_status", field_verif, nullable=False, server_default="auto_accepted"),
        sa.Column("verified_value", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["extraction_id"], ["document_extractions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_document_extracted_fields_extraction_id", "document_extracted_fields", ["extraction_id"])
    op.create_index("ix_document_extracted_fields_document_id", "document_extracted_fields", ["document_id"])

    op.create_table(
        "document_verifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("verified_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("outcome", field_verif, nullable=False),
        sa.Column("correction_reason", sa.Text(), nullable=True),
        sa.Column("corrected_fields", postgresql.JSONB(), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["verified_by"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_document_verifications_document_id", "document_verifications", ["document_id"])


def downgrade() -> None:
    op.drop_table("document_verifications")
    op.drop_table("document_extracted_fields")
    op.drop_table("document_extractions")
    op.drop_table("document_processing_jobs")
    op.drop_table("documents")
    bind = op.get_bind()
    for name in (
        "field_verification_status", "field_value_type", "fact_source",
        "confidence_level", "processing_job_status", "document_status", "document_type",
    ):
        postgresql.ENUM(name=name).drop(bind, checkfirst=True)
