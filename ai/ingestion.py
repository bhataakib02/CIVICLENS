"""Knowledge ingestion pipeline — parse → normalize → chunk → embed → persist.

Re-exports the canonical ingestion subsystem from the backend. This module
orchestrates the full pipeline from raw fetched bytes to persisted,
deduplicated, embedded knowledge chunks.

See ``docs/ai/rag-architecture.md`` § Ingestion.
"""

from app.modules.knowledge.ingestion.chunker import chunk_document
from app.modules.knowledge.ingestion.fetcher import (
    FetchError,
    SafeFetcher,
    SsrfError,
)
from app.modules.knowledge.ingestion.metadata import (
    content_hash,
    detect_source_type,
    infer_trust_level,
)
from app.modules.knowledge.ingestion.normalizer import normalize
from app.modules.knowledge.ingestion.parser import parse
from app.modules.knowledge.ingestion.pipeline import (
    EmptyContentError,
    IngestionError,
    IngestionOutcome,
    IngestionPipeline,
)

__all__ = [
    # Full pipeline
    "IngestionPipeline",
    "IngestionOutcome",
    "IngestionError",
    "EmptyContentError",
    # Individual stages
    "parse",
    "normalize",
    "chunk_document",
    "content_hash",
    "detect_source_type",
    "infer_trust_level",
    # Fetcher
    "SafeFetcher",
    "FetchError",
    "SsrfError",
]
