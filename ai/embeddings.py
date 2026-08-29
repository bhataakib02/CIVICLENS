"""Embedding provider abstraction and batch-embed utilities.

Re-exports the canonical embedding subsystem from the backend. The application
depends on the ``EmbeddingProvider`` interface — never on a vendor SDK
directly — so the provider is replaceable via configuration.

See ``docs/ai/rag-architecture.md`` § Embedding Layer.
"""

from app.modules.knowledge.embeddings.provider import (
    DeterministicTestEmbeddingProvider,
    DimensionMismatchError,
    EmbeddingError,
    EmbeddingProvider,
    get_embedding_provider,
)

__all__ = [
    "EmbeddingProvider",
    "EmbeddingError",
    "DimensionMismatchError",
    "DeterministicTestEmbeddingProvider",
    "get_embedding_provider",
]
