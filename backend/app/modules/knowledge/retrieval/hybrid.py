"""Hybrid retrieval (ADR-007, prompt §14, §15).

Combines semantic (pgvector) and lexical (FTS) candidates, then fuses their
scores. Fusion is DOCUMENTED and normalized (not a blind average):

    hybrid = w_sem * norm(semantic) + w_lex * norm(lexical)
             + w_trust * trust_weight(source)
             + w_version * version_match_bonus

where:
- norm(x) is min-max normalization within each candidate list, so the two
  score scales (cosine similarity vs. ts_rank) are comparable before mixing;
- trust_weight maps trust levels to [0,1] (official government highest);
- version_match_bonus rewards a chunk explicitly tagged with the requested
  scheme_version_id (temporal relevance), so version-X questions prefer
  version-X evidence and don't silently mix policy years.

Weights are fixed constants (documented below) — tune deliberately, not per
request. Returns a single ranked, de-duplicated list of RetrievedChunk.
"""
from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.modules.knowledge.embeddings.provider import EmbeddingProvider
from app.modules.knowledge.retrieval.lexical import LexicalRetriever
from app.modules.knowledge.retrieval.semantic import RetrievedChunk, SemanticRetriever

# Fusion weights (documented; sum of the retrieval weights = 1.0, with small
# additive trust/version boosts).
W_SEMANTIC = 0.55
W_LEXICAL = 0.45
W_TRUST = 0.10
W_VERSION = 0.15

_TRUST_WEIGHT = {
    "official_government": 1.0,
    "official_document": 0.95,
    "official_portal": 0.85,
    "verified_secondary": 0.5,
    "unverified": 0.0,
}


def _minmax(values: list[float]) -> dict[int, float]:
    if not values:
        return {}
    lo, hi = min(values), max(values)
    if hi <= lo:
        return {i: 1.0 for i in range(len(values))}
    return {i: (v - lo) / (hi - lo) for i, v in enumerate(values)}


class HybridRetriever:
    def __init__(
        self,
        session: Session,
        embedder: EmbeddingProvider,
        settings: Settings | None = None,
    ) -> None:
        self._semantic = SemanticRetriever(session, embedder)
        self._lexical = LexicalRetriever(session)
        self._s = settings or get_settings()

    def retrieve(
        self,
        *,
        query: str,
        scheme_id: uuid.UUID | None = None,
        scheme_version_id: uuid.UUID | None = None,
        authoritative_only: bool = True,
        candidate_limit: int | None = None,
    ) -> list[RetrievedChunk]:
        limit = candidate_limit or self._s.retrieval_candidate_limit
        sem = self._semantic.retrieve(
            query=query, scheme_id=scheme_id, scheme_version_id=scheme_version_id,
            authoritative_only=authoritative_only, limit=limit,
        )
        lex = self._lexical.retrieve(
            query=query, scheme_id=scheme_id, scheme_version_id=scheme_version_id,
            authoritative_only=authoritative_only, limit=limit,
        )

        sem_norm = _minmax([c.semantic_score for c in sem])
        lex_norm = _minmax([c.lexical_score for c in lex])

        merged: dict[uuid.UUID, RetrievedChunk] = {}
        for i, c in enumerate(sem):
            c.semantic_score = sem_norm.get(i, 0.0)
            merged[c.chunk_id] = c
        for i, c in enumerate(lex):
            norm = lex_norm.get(i, 0.0)
            if c.chunk_id in merged:
                merged[c.chunk_id].lexical_score = norm
            else:
                c.lexical_score = norm
                c.semantic_score = 0.0
                merged[c.chunk_id] = c

        results = list(merged.values())
        for c in results:
            trust = _TRUST_WEIGHT.get(c.trust_level, 0.0)
            version_bonus = (
                1.0
                if (scheme_version_id is not None and c.scheme_version_id == scheme_version_id)
                else 0.0
            )
            c.score = (
                W_SEMANTIC * c.semantic_score
                + W_LEXICAL * c.lexical_score
                + W_TRUST * trust
                + W_VERSION * version_bonus
            )
        # Temporal preference (prompt §15): when a specific scheme_version is
        # requested, chunks explicitly tagged with that version sort ahead of
        # untagged/other-version chunks, then by fused score. This prevents
        # mixing policy years regardless of raw score normalization artifacts.
        def _sort_key(c):
            version_match = (
                1 if (scheme_version_id is not None and c.scheme_version_id == scheme_version_id) else 0
            )
            return (version_match, c.score)

        results.sort(key=_sort_key, reverse=True)
        return results
