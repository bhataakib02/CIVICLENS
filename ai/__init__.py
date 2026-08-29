"""ai — RAG, Extraction & Classification Library.

Shared library consumed by both ``backend/app/modules/assistant`` (synchronous
chat) and ``workers/ingestion`` (batch knowledge processing). Not a standalone
deployable — see ``docs/ai/rag-architecture.md``.

This package re-exports the canonical implementations from the backend so that
callers import from ``ai.*`` instead of reaching into ``backend.app.modules.*``
directly.
"""

from ai.embeddings import (
    EmbeddingProvider,
    get_embedding_provider,
)
from ai.extraction import (
    ClassificationResult,
    classify_document,
)
from ai.generation import (
    LLMProvider,
    get_llm_provider,
)
from ai.grounding import (
    build_grounding_context,
    extract_evidence_refs,
    sanitize_evidence_text,
)
from ai.ingestion import IngestionPipeline
from ai.retrieval import HybridRetriever, RetrievedChunk

__all__ = [
    # Retrieval
    "HybridRetriever",
    "RetrievedChunk",
    # Embeddings
    "EmbeddingProvider",
    "get_embedding_provider",
    # Generation
    "LLMProvider",
    "get_llm_provider",
    # Grounding
    "build_grounding_context",
    "extract_evidence_refs",
    "sanitize_evidence_text",
    # Extraction
    "ClassificationResult",
    "classify_document",
    # Ingestion
    "IngestionPipeline",
]
