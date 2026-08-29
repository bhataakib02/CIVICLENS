"""Knowledge persistence + retrieval queries.

Retrieval runs in SQL: pgvector cosine distance for semantic, PostgreSQL FTS
(ts_rank) for lexical. Version/scheme/trust filters are applied in the query
(one controlled query per retrieval path — never per-chunk).
"""
from __future__ import annotations

import uuid

from sqlalchemy import Float, and_, func, or_, select, text
from sqlalchemy.orm import Session

from app.models.enums import SourceTrustLevel, VerificationStatus
from app.models.knowledge import IngestionJob, KnowledgeChunk, KnowledgeSource

# Trust levels eligible to be surfaced as authoritative evidence (prompt §5).
AUTHORITATIVE_TRUST = (
    SourceTrustLevel.OFFICIAL_GOVERNMENT,
    SourceTrustLevel.OFFICIAL_DOCUMENT,
    SourceTrustLevel.OFFICIAL_PORTAL,
    SourceTrustLevel.VERIFIED_SECONDARY,
)


class KnowledgeRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    # ------------------------------ sources ----------------------------- #
    def add_source(self, source: KnowledgeSource) -> KnowledgeSource:
        self._session.add(source)
        self._session.flush()
        return source

    def get_source(self, source_id: uuid.UUID) -> KnowledgeSource | None:
        return self._session.get(KnowledgeSource, source_id)

    def get_source_by_content_hash(self, content_hash: str) -> KnowledgeSource | None:
        return self._session.scalar(
            select(KnowledgeSource).where(KnowledgeSource.content_hash == content_hash)
        )

    def list_sources(self, *, limit: int, offset: int) -> list[KnowledgeSource]:
        stmt = select(KnowledgeSource).order_by(KnowledgeSource.created_at.desc()).limit(limit).offset(offset)
        return list(self._session.scalars(stmt))

    def count_sources(self) -> int:
        return int(self._session.scalar(select(func.count()).select_from(KnowledgeSource)) or 0)

    # ------------------------------ chunks ------------------------------- #
    def add_chunks(self, chunks: list[KnowledgeChunk]) -> None:
        self._session.add_all(chunks)
        self._session.flush()

    # ------------------------------ jobs --------------------------------- #
    def add_job(self, job: IngestionJob) -> IngestionJob:
        self._session.add(job)
        self._session.flush()
        return job

    def get_job(self, job_id: uuid.UUID) -> IngestionJob | None:
        return self._session.get(IngestionJob, job_id)

    # --------------------------- retrieval ------------------------------- #
    def _base_filters(self, *, scheme_id, scheme_version_id, authoritative_only):
        conds = []
        if authoritative_only:
            conds.append(KnowledgeSource.trust_level.in_([t for t in AUTHORITATIVE_TRUST]))
            conds.append(KnowledgeSource.verification_status == VerificationStatus.VERIFIED)
        if scheme_id is not None:
            conds.append(KnowledgeSource.scheme_id == scheme_id)
        if scheme_version_id is not None:
            conds.append(
                or_(
                    KnowledgeChunk.scheme_version_id == scheme_version_id,
                    KnowledgeChunk.scheme_version_id.is_(None),
                )
            )
        return conds

    def semantic_search(
        self,
        *,
        query_embedding: list[float],
        scheme_id: uuid.UUID | None,
        scheme_version_id: uuid.UUID | None,
        authoritative_only: bool,
        limit: int,
    ) -> list[tuple[KnowledgeChunk, KnowledgeSource, float]]:
        """Cosine-distance nearest neighbors (lower distance = closer)."""
        distance = KnowledgeChunk.embedding.cosine_distance(query_embedding).label("distance")
        stmt = (
            select(KnowledgeChunk, KnowledgeSource, distance)
            .join(KnowledgeSource, KnowledgeChunk.knowledge_source_id == KnowledgeSource.id)
            .where(KnowledgeChunk.embedding.isnot(None))
            .where(and_(*self._base_filters(
                scheme_id=scheme_id, scheme_version_id=scheme_version_id,
                authoritative_only=authoritative_only)))
            .order_by(distance)
            .limit(limit)
        )
        return [(c, s, float(d)) for c, s, d in self._session.execute(stmt).all()]

    def lexical_search(
        self,
        *,
        query: str,
        scheme_id: uuid.UUID | None,
        scheme_version_id: uuid.UUID | None,
        authoritative_only: bool,
        limit: int,
    ) -> list[tuple[KnowledgeChunk, KnowledgeSource, float]]:
        """PostgreSQL full-text search ranked by ts_rank."""
        tsquery = func.plainto_tsquery("english", query)
        rank = func.ts_rank(KnowledgeChunk.content_tsv, tsquery).label("rank")
        stmt = (
            select(KnowledgeChunk, KnowledgeSource, rank)
            .join(KnowledgeSource, KnowledgeChunk.knowledge_source_id == KnowledgeSource.id)
            .where(KnowledgeChunk.content_tsv.op("@@")(tsquery))
            .where(and_(*self._base_filters(
                scheme_id=scheme_id, scheme_version_id=scheme_version_id,
                authoritative_only=authoritative_only)))
            .order_by(rank.desc())
            .limit(limit)
        )
        return [(c, s, float(r)) for c, s, r in self._session.execute(stmt).all()]
