"""Embedding provider abstraction + deterministic test provider (prompt §11-§12).

The application depends on the EmbeddingProvider interface, never on a vendor
SDK directly, so the provider is replaceable via configuration.

- embed_text(text) -> vector
- embed_batch(texts) -> list[vector]

Every provider MUST return vectors of exactly `dimension` (1536 to match the
pgvector column, ADR-002). A DimensionMismatchError is raised otherwise — we
never silently insert wrong-dimension vectors.

The DeterministicTestEmbeddingProvider is for automated tests / local dev ONLY
(it is hash-seeded, reproducible, and captures lexical overlap so semantically
similar texts are closer — enough to exercise the pipeline without a network
call). Production requires an explicitly configured real provider; selecting
"test" while ENVIRONMENT=production raises at startup.
"""
from __future__ import annotations

import hashlib
import math
import re
from abc import ABC, abstractmethod

from app.core.config import Settings, get_settings

_TOKEN_RE = re.compile(r"[a-z0-9]+")


class EmbeddingError(Exception):
    pass


class DimensionMismatchError(EmbeddingError):
    pass


class EmbeddingProvider(ABC):
    """Abstract embedding provider. Implementations must honor `dimension`."""

    name: str = "abstract"

    def __init__(self, dimension: int) -> None:
        self.dimension = dimension

    @abstractmethod
    def _embed_one(self, text: str) -> list[float]:  # pragma: no cover - abstract
        ...

    def embed_text(self, text: str) -> list[float]:
        vec = self._embed_one(text or "")
        self._check(vec)
        return vec

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        out = [self._embed_one(t or "") for t in texts]
        for v in out:
            self._check(v)
        return out

    def _check(self, vec: list[float]) -> None:
        if len(vec) != self.dimension:
            raise DimensionMismatchError(
                f"{self.name} produced dim {len(vec)}, expected {self.dimension}."
            )


class DeterministicTestEmbeddingProvider(EmbeddingProvider):
    """Hash-seeded, reproducible embeddings for tests/dev ONLY.

    Approach: bag-of-tokens hashed into the vector space with L2 normalization.
    Shared tokens => higher cosine similarity, so retrieval behaves sensibly in
    tests. Deterministic: same text always yields the same vector.
    """

    name = "test-deterministic"

    def _embed_one(self, text: str) -> list[float]:
        vec = [0.0] * self.dimension
        tokens = _TOKEN_RE.findall(text.lower())
        if not tokens:
            # Stable non-zero vector for empty text (avoids NaN on normalize).
            vec[0] = 1.0
            return vec
        for tok in tokens:
            h = hashlib.sha256(tok.encode("utf-8")).digest()
            idx = int.from_bytes(h[:4], "big") % self.dimension
            sign = 1.0 if h[4] & 1 else -1.0
            weight = 1.0 + (h[5] / 255.0)
            vec[idx] += sign * weight
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec


def get_embedding_provider(settings: Settings | None = None) -> EmbeddingProvider:
    """Factory: build the configured embedding provider.

    Only the deterministic test provider is bundled. A real provider would be
    registered here; selecting "test" in production is refused so the
    production path always requires an explicit real provider (prompt §40).
    """
    settings = settings or get_settings()
    dim = settings.embedding_dimension
    provider = settings.embedding_provider.lower()

    if provider == "test":
        if settings.is_production:
            raise EmbeddingError(
                "The deterministic test embedding provider must not be used in production. "
                "Configure a real EMBEDDING_PROVIDER."
            )
        return DeterministicTestEmbeddingProvider(dim)

    # Real providers (e.g. "openai") would be constructed here behind this same
    # interface. Not bundled in this slice.
    raise EmbeddingError(
        f"Unknown or unconfigured embedding provider '{provider}'. "
        "Bundled option: 'test' (non-production)."
    )
