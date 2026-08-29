"""Shared retrieval types + semantic retriever (pgvector)."""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.knowledge import KnowledgeChunk, KnowledgeSource
from app.modules.knowledge.embeddings.provider import EmbeddingProvider
from app.modules.knowledge.repository import KnowledgeRepository


@dataclass
class RetrievedChunk:
    chunk_id: uuid.UUID
    source_id: uuid.UUID
    content: str
    source_url: str
    page_number: int | None
    section: str | None
    scheme_version_id: uuid.UUID | None
    trust_level: str
    score: float
    semantic_score: float = 0.0
    lexical_score: float = 0.0

    @classmethod
    def from_row(cls, chunk: KnowledgeChunk, source: KnowledgeSource, score: float) -> "RetrievedChunk":
        return cls(
            chunk_id=chunk.id,
            source_id=source.id,
            content=chunk.content,
            source_url=source.url,
            page_number=chunk.page_number,
            section=chunk.section,
            scheme_version_id=chunk.scheme_version_id,
            trust_level=source.trust_level.value,
            score=score,
        )


class SemanticRetriever:
    def __init__(self, session: Session, embedder: EmbeddingProvider) -> None:
        self._repo = KnowledgeRepository(session)
        self._embedder = embedder

    def retrieve(
        self,
        *,
        query: str,
        scheme_id: uuid.UUID | None,
        scheme_version_id: uuid.UUID | None,
        authoritative_only: bool,
        limit: int,
    ) -> list[RetrievedChunk]:
        query_vec = self._embedder.embed_text(query)
        rows = self._repo.semantic_search(
            query_embedding=query_vec,
            scheme_id=scheme_id,
            scheme_version_id=scheme_version_id,
            authoritative_only=authoritative_only,
            limit=limit,
        )
        out = []
        for chunk, source, distance in rows:
            # cosine distance in [0,2]; convert to similarity in [0,1].
            sim = max(0.0, 1.0 - distance / 2.0)
            rc = RetrievedChunk.from_row(chunk, source, sim)
            rc.semantic_score = sim
            out.append(rc)
        return out
