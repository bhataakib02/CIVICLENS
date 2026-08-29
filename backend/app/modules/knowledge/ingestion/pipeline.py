"""Ingestion pipeline orchestrator (prompt §6).

Given a fetched-or-provided document, runs:
    parse -> normalize -> content_hash -> dedup -> chunk -> metadata ->
    embed(batch) -> persist.

Idempotent by content_hash: if a source with the same content_hash already
exists, ingestion is a no-op (no duplicate chunks). Chunk hashes are stable,
so re-ingesting identical content is safe.

The pipeline itself performs NO network fetch (the SafeFetcher does that, and
the async worker wires them together) — so it is a pure, testable transform
over raw bytes + metadata that persists via the repository.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.models.enums import VerificationStatus
from app.models.knowledge import KnowledgeChunk, KnowledgeSource
from app.modules.knowledge.embeddings.provider import EmbeddingProvider, get_embedding_provider
from app.modules.knowledge.ingestion.chunker import chunk_document
from app.modules.knowledge.ingestion.metadata import (
    content_hash,
    detect_source_type,
    infer_trust_level,
)
from app.modules.knowledge.ingestion.normalizer import normalize
from app.modules.knowledge.ingestion.parser import parse

logger = get_logger("civiclens.knowledge.pipeline")


class IngestionError(Exception):
    pass


class EmptyContentError(IngestionError):
    """Extraction produced no usable content -> source REJECTED."""


@dataclass
class IngestionOutcome:
    source_id: uuid.UUID
    chunk_count: int
    content_hash: str
    duplicate: bool
    verification_status: VerificationStatus


class IngestionPipeline:
    def __init__(
        self,
        session: Session,
        *,
        embedder: EmbeddingProvider | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._session = session
        self._s = settings or get_settings()
        self._embedder = embedder or get_embedding_provider(self._s)

    def ingest(
        self,
        *,
        title: str,
        url: str,
        publisher: str,
        content: bytes,
        content_type: str,
        scheme_id: uuid.UUID | None = None,
        scheme_version_id: uuid.UUID | None = None,
        retrieved_at: float | None = None,
    ) -> IngestionOutcome:
        from app.modules.knowledge.repository import KnowledgeRepository

        repo = KnowledgeRepository(self._session)
        chash = content_hash(content)

        # Idempotency: identical content already ingested -> no-op.
        existing = repo.get_source_by_content_hash(chash)
        if existing is not None:
            logger.info("ingestion_duplicate", extra={"content_hash": chash})
            return IngestionOutcome(
                source_id=existing.id,
                chunk_count=len(existing.chunks),
                content_hash=chash,
                duplicate=True,
                verification_status=existing.verification_status,
            )

        source_type = detect_source_type(content_type)
        parsed = parse(content, content_type)
        normalized = normalize(parsed)

        source = KnowledgeSource(
            title=title.strip(),
            url=url,
            publisher=publisher.strip(),
            scheme_id=scheme_id,
            source_type=source_type,
            trust_level=infer_trust_level(url, source_type),
            content_hash=chash,
            retrieved_at=datetime.fromtimestamp(retrieved_at, tz=timezone.utc)
            if retrieved_at
            else datetime.now(timezone.utc),
        )

        if normalized.is_empty:
            # Do not silently store empty content — reject the source.
            source.verification_status = VerificationStatus.REJECTED
            repo.add_source(source)
            self._session.flush()
            logger.warning("ingestion_rejected_empty", extra={"url_host": url})
            raise EmptyContentError("No extractable content; source marked REJECTED.")

        source.verification_status = VerificationStatus.PENDING
        repo.add_source(source)
        self._session.flush()

        chunks = chunk_document(normalized)
        texts = [c.content for c in chunks]
        embeddings = self._embed_in_batches(texts)

        rows = [
            KnowledgeChunk(
                knowledge_source_id=source.id,
                scheme_version_id=scheme_version_id,
                content=c.content,
                embedding=emb,
                page_number=c.page_number,
                section=c.section,
                char_start=c.char_start,
                char_end=c.char_end,
                chunk_index=c.chunk_index,
                chunk_hash=c.chunk_hash,
            )
            for c, emb in zip(chunks, embeddings)
        ]
        repo.add_chunks(rows)
        self._session.flush()

        logger.info(
            "ingestion_completed",
            extra={"source_id": str(source.id), "chunk_count": len(rows), "content_hash": chash},
        )
        return IngestionOutcome(
            source_id=source.id,
            chunk_count=len(rows),
            content_hash=chash,
            duplicate=False,
            verification_status=source.verification_status,
        )

    def _embed_in_batches(self, texts: list[str]) -> list[list[float]]:
        batch_size = self._s.embedding_batch_size
        out: list[list[float]] = []
        for i in range(0, len(texts), batch_size):
            out.extend(self._embedder.embed_batch(texts[i : i + batch_size]))
        return out
