"""knowledge base + RAG (pgvector + FTS)

Creates the knowledge subsystem tables and enables the extensions the RAG
pipeline needs:
  * CREATE EXTENSION vector    (pgvector; ADR-002) — embeddings on
    knowledge_chunks.embedding vector(1536).
  * CREATE EXTENSION pg_trgm   — trigram fuzzy matching for lexical search.
  * knowledge_chunks.content_tsv is a STORED generated tsvector
    (to_tsvector('english', content)) with a GIN index — PostgreSQL FTS
    (ADR-007 hybrid retrieval), no external search engine.

Indexing strategy (prompt §38, indexing-strategy.md): a GIN index on the FTS
column and a GIN trigram index on content are created (bounded, useful at any
size). A pgvector ANN index (IVFFlat/HNSW) is deliberately NOT created here:
at seed/dev scale an exact scan is faster and correct, and IVFFlat needs to be
built after data exists with a tuned list count. Building the ANN index is
documented as a data-scale operation (a follow-up migration once the chunk
count justifies it), not applied blindly.

DOCUMENTED EXTENSIONS beyond data-dictionary.md (recorded here + in the report):
  knowledge_sources: scheme_id, source_type, trust_level, verification_status,
    content_hash, retrieved_at, created_at.
  knowledge_chunks: scheme_version_id, section, chunk_index, chunk_hash,
    content_tsv, created_at, uq(knowledge_source_id, chunk_hash).
  ingestion_jobs: new table (processing state, distinct from verification).

Revision ID: 0003_knowledge_rag_slice
Revises: 0002_scheme_eligibility_slice
Create Date: 2026-08-29
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "0003_knowledge_rag_slice"
down_revision: Union[str, None] = "0002_scheme_eligibility_slice"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EMBEDDING_DIM = 1536


def _try_create_trgm() -> bool:
    """Create pg_trgm if the library is actually installable; else skip.

    Some minimal PostgreSQL builds list pg_trgm as available but cannot load
    it. The trigram index is an enhancement over the required FTS path, so we
    degrade gracefully rather than failing the whole migration.
    """
    conn = op.get_bind()
    try:
        with conn.begin_nested():
            conn.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS pg_trgm")
        return True
    except Exception:
        return False


def upgrade() -> None:
    bind = op.get_bind()
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    # pg_trgm is optional: it may be listed as available but not installable in
    # some minimal builds. Trigram fuzzy matching is an enhancement over the
    # required FTS path, so degrade gracefully if it cannot be created.
    trgm_ok = _try_create_trgm()

    source_type = postgresql.ENUM("html", "pdf", "text", name="source_type", create_type=False)
    trust_level = postgresql.ENUM(
        "official_government", "official_document", "official_portal",
        "verified_secondary", "unverified", name="source_trust_level", create_type=False,
    )
    verification_status = postgresql.ENUM(
        "pending", "verified", "rejected", "stale",
        name="source_verification_status", create_type=False,
    )
    job_status = postgresql.ENUM(
        "pending", "processing", "completed", "failed",
        name="ingestion_job_status", create_type=False,
    )
    postgresql.ENUM("html", "pdf", "text", name="source_type").create(bind, checkfirst=True)
    postgresql.ENUM(
        "official_government", "official_document", "official_portal",
        "verified_secondary", "unverified", name="source_trust_level",
    ).create(bind, checkfirst=True)
    postgresql.ENUM(
        "pending", "verified", "rejected", "stale", name="source_verification_status",
    ).create(bind, checkfirst=True)
    postgresql.ENUM(
        "pending", "processing", "completed", "failed", name="ingestion_job_status",
    ).create(bind, checkfirst=True)

    # --- knowledge_sources ---
    op.create_table(
        "knowledge_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("publisher", sa.String(length=255), nullable=False),
        sa.Column("published_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scheme_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source_type", source_type, nullable=True),
        sa.Column("trust_level", trust_level, nullable=False, server_default="unverified"),
        sa.Column("verification_status", verification_status, nullable=False, server_default="pending"),
        sa.Column("content_hash", sa.String(length=64), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["scheme_id"], ["schemes.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_knowledge_sources_scheme_id", "knowledge_sources", ["scheme_id"])
    op.create_index("ix_knowledge_sources_trust_level", "knowledge_sources", ["trust_level"])
    op.create_index("ix_knowledge_sources_verification_status", "knowledge_sources", ["verification_status"])
    op.create_index("ix_knowledge_sources_content_hash", "knowledge_sources", ["content_hash"])

    # --- knowledge_chunks ---
    op.create_table(
        "knowledge_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("knowledge_source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scheme_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=True),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("section", sa.String(length=512), nullable=True),
        sa.Column("char_start", sa.Integer(), nullable=True),
        sa.Column("char_end", sa.Integer(), nullable=True),
        sa.Column("chunk_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("chunk_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "content_tsv",
            postgresql.TSVECTOR(),
            sa.Computed("to_tsvector('english', content)", persisted=True),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["knowledge_source_id"], ["knowledge_sources.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["scheme_version_id"], ["scheme_versions.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("knowledge_source_id", "chunk_hash", name="uq_chunk_hash_per_source"),
    )
    op.create_index("ix_knowledge_chunks_source_id", "knowledge_chunks", ["knowledge_source_id"])
    op.create_index("ix_knowledge_chunks_scheme_version_id", "knowledge_chunks", ["scheme_version_id"])
    op.create_index("ix_knowledge_chunks_chunk_hash", "knowledge_chunks", ["chunk_hash"])
    # FTS + trigram indexes for lexical retrieval (ADR-007).
    op.create_index(
        "ix_knowledge_chunks_content_tsv", "knowledge_chunks", ["content_tsv"],
        postgresql_using="gin",
    )
    if trgm_ok:
        op.create_index(
            "ix_knowledge_chunks_content_trgm", "knowledge_chunks", ["content"],
            postgresql_using="gin", postgresql_ops={"content": "gin_trgm_ops"},
        )

    # --- ingestion_jobs ---
    op.create_table(
        "ingestion_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("knowledge_source_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", job_status, nullable=False, server_default="pending"),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("scheme_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("scheme_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("result", postgresql.JSONB(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["knowledge_source_id"], ["knowledge_sources.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["scheme_id"], ["schemes.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["scheme_version_id"], ["scheme_versions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_ingestion_jobs_status", "ingestion_jobs", ["status"])
    op.create_index("ix_ingestion_jobs_source_id", "ingestion_jobs", ["knowledge_source_id"])


def downgrade() -> None:
    op.drop_table("ingestion_jobs")
    op.execute("DROP INDEX IF EXISTS ix_knowledge_chunks_content_trgm")
    op.drop_index("ix_knowledge_chunks_content_tsv", table_name="knowledge_chunks")
    op.drop_table("knowledge_chunks")
    op.drop_table("knowledge_sources")
    bind = op.get_bind()
    for name in ("ingestion_job_status", "source_verification_status", "source_trust_level", "source_type"):
        postgresql.ENUM(name=name).drop(bind, checkfirst=True)
