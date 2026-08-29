"""Reranker abstraction (prompt §17).

    Retriever -> top 20-50 candidates -> Reranker -> top 5-10 evidence chunks

The interface is replaceable (a cross-encoder model reranker could be dropped
in later). The bundled DeterministicReranker uses a transparent lexical-overlap
+ hybrid-score blend, so it is reproducible and needs no model — enough to
narrow candidates before the (expensive, small-context) generation step.
"""
from __future__ import annotations

import re
from abc import ABC, abstractmethod

from app.modules.knowledge.retrieval.semantic import RetrievedChunk

_TOKEN_RE = re.compile(r"[a-z0-9]+")


class Reranker(ABC):
    @abstractmethod
    def rerank(
        self, query: str, candidates: list[RetrievedChunk], *, top_k: int
    ) -> list[RetrievedChunk]:  # pragma: no cover - abstract
        ...


class DeterministicReranker(Reranker):
    """Blend the hybrid score with query/chunk lexical-overlap (Jaccard).

    Deterministic and side-effect free. Sets each returned chunk's `score` to
    the final rerank score and returns the top_k.
    """

    def __init__(self, overlap_weight: float = 0.5) -> None:
        self._w = overlap_weight

    def rerank(self, query: str, candidates: list[RetrievedChunk], *, top_k: int) -> list[RetrievedChunk]:
        q_tokens = set(_TOKEN_RE.findall(query.lower()))
        scored: list[tuple[float, int, RetrievedChunk]] = []
        for i, c in enumerate(candidates):
            c_tokens = set(_TOKEN_RE.findall(c.content.lower()))
            if q_tokens and c_tokens:
                overlap = len(q_tokens & c_tokens) / len(q_tokens | c_tokens)
            else:
                overlap = 0.0
            final = (1 - self._w) * c.score + self._w * overlap
            c.score = round(final, 6)
            # i as a stable tie-breaker keeps ordering deterministic.
            scored.append((final, -i, c))
        scored.sort(key=lambda t: (t[0], t[1]), reverse=True)
        return [c for _f, _i, c in scored[:top_k]]


def get_reranker() -> Reranker:
    """Factory — returns the configured reranker (deterministic default)."""
    return DeterministicReranker()
