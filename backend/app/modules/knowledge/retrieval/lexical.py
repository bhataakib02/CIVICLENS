"""Lexical retriever — PostgreSQL full-text search (ADR-007)."""
from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.modules.knowledge.repository import KnowledgeRepository
from app.modules.knowledge.retrieval.semantic import RetrievedChunk


class LexicalRetriever:
    def __init__(self, session: Session) -> None:
        self._repo = KnowledgeRepository(session)

    def retrieve(
        self,
        *,
        query: str,
        scheme_id: uuid.UUID | None,
        scheme_version_id: uuid.UUID | None,
        authoritative_only: bool,
        limit: int,
    ) -> list[RetrievedChunk]:
        rows = self._repo.lexical_search(
            query=query,
            scheme_id=scheme_id,
            scheme_version_id=scheme_version_id,
            authoritative_only=authoritative_only,
            limit=limit,
        )
        out = []
        for chunk, source, rank in rows:
            rc = RetrievedChunk.from_row(chunk, source, rank)
            rc.lexical_score = rank
            out.append(rc)
        return out
