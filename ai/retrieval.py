"""Retrieval pipeline façade — hybrid lexical + semantic search.

Re-exports the canonical retrieval subsystem from the backend. Consumer code
should import from ``ai.retrieval`` to insulate itself from the backend
package structure.

See ``docs/ai/retrieval-pipeline.md`` for the full architecture.
"""

from app.modules.knowledge.retrieval.hybrid import (
    HybridRetriever,
    W_LEXICAL,
    W_SEMANTIC,
    W_TRUST,
    W_VERSION,
)
from app.modules.knowledge.retrieval.reranker import (
    DeterministicReranker,
    Reranker,
    get_reranker,
)
from app.modules.knowledge.retrieval.semantic import RetrievedChunk

__all__ = [
    "HybridRetriever",
    "RetrievedChunk",
    "Reranker",
    "DeterministicReranker",
    "get_reranker",
    # Tuning constants (documented, deliberate)
    "W_SEMANTIC",
    "W_LEXICAL",
    "W_TRUST",
    "W_VERSION",
]
