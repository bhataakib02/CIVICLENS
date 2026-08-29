"""Embedding provider abstraction (vendor-replaceable)."""
from app.modules.knowledge.embeddings.provider import (
    EmbeddingProvider,
    get_embedding_provider,
)

__all__ = ["EmbeddingProvider", "get_embedding_provider"]
