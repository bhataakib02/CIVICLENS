"""Knowledge base models — reuse data-dictionary.md `knowledge_sources` +
`knowledge_chunks`, plus an `ingestion_jobs` table for async processing.

ADR-002: embeddings live in the same PostgreSQL via pgvector, foreign-keyed to
the relational knowledge/scheme schema so every citation joins cleanly back to
its source and scheme_version.

DOCUMENTED EXTENSIONS beyond the flat data-dictionary columns (recorded in the
migration docstring; required by prompt §4/§5/§10/§31):
  knowledge_sources: source_type, trust_level, content_hash, verification_status,
    retrieved_at, scheme_id (nullable link).
  knowledge_chunks: scheme_version_id, section, chunk_hash, created_at,
    content_tsv (generated tsvector for FTS).
  ingestion_jobs: new table (processing state separate from verification).

EMBEDDING_DIM is the single source of truth for the pgvector column width.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    DateTime,
    Computed,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, uuid_pk
from app.models.enums import (
    IngestionJobStatus,
    SourceTrustLevel,
    SourceType,
    VerificationStatus,
)

# Embedding dimension — must match the configured embedding provider and the
# pgvector column. Changing it requires a re-embedding migration (ADR-002).
EMBEDDING_DIM = 1536

if TYPE_CHECKING:
    pass


def _enum_col(py_enum, name):
    return Enum(
        py_enum,
        name=name,
        native_enum=True,
        validate_strings=True,
        values_callable=lambda enum: [m.value for m in enum],
    )


class KnowledgeSource(Base):
    __tablename__ = "knowledge_sources"

    id: Mapped[uuid.UUID] = uuid_pk()
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    publisher: Mapped[str] = mapped_column(String(255), nullable=False)
    published_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Extensions
    scheme_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("schemes.id", ondelete="SET NULL"), nullable=True, index=True
    )
    source_type: Mapped[SourceType | None] = mapped_column(
        _enum_col(SourceType, "source_type"), nullable=True
    )
    trust_level: Mapped[SourceTrustLevel] = mapped_column(
        _enum_col(SourceTrustLevel, "source_trust_level"),
        default=SourceTrustLevel.UNVERIFIED,
        nullable=False,
        index=True,
    )
    verification_status: Mapped[VerificationStatus] = mapped_column(
        _enum_col(VerificationStatus, "source_verification_status"),
        default=VerificationStatus.PENDING,
        nullable=False,
        index=True,
    )
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    retrieved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    chunks: Mapped[list["KnowledgeChunk"]] = relationship(
        back_populates="source", cascade="all, delete-orphan"
    )


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    __table_args__ = (
        UniqueConstraint("knowledge_source_id", "chunk_hash", name="uq_chunk_hash_per_source"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    knowledge_source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("knowledge_sources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scheme_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("scheme_versions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM), nullable=True)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    section: Mapped[str | None] = mapped_column(String(512), nullable=True)
    char_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    char_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    chunk_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    # Generated FTS vector maintained by the DB (Computed => never in INSERT).
    content_tsv: Mapped[str | None] = mapped_column(
        TSVECTOR,
        Computed("to_tsvector('english', content)", persisted=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    source: Mapped["KnowledgeSource"] = relationship(back_populates="chunks")


class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"

    id: Mapped[uuid.UUID] = uuid_pk()
    knowledge_source_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("knowledge_sources.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[IngestionJobStatus] = mapped_column(
        _enum_col(IngestionJobStatus, "ingestion_job_status"),
        default=IngestionJobStatus.PENDING,
        nullable=False,
        index=True,
    )
    url: Mapped[str] = mapped_column(Text, nullable=False)
    scheme_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("schemes.id", ondelete="SET NULL"), nullable=True
    )
    scheme_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("scheme_versions.id", ondelete="SET NULL"), nullable=True
    )
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
