"""Citation building + validation (prompt §19, §26).

Citations are built ONLY from the evidence markers actually provided to the
model. If the model cites an [EVIDENCE n] that wasn't provided, that citation
is invalid (a fabrication signal). page_number is passed through as-is (null if
unavailable — never invented).
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from app.modules.knowledge.retrieval.semantic import RetrievedChunk

_EVIDENCE_REF_RE = re.compile(r"\[EVIDENCE\s+(\d+)\]", re.IGNORECASE)


@dataclass
class Citation:
    source_id: str
    chunk_id: str
    source_url: str
    page_number: int | None
    section: str | None
    evidence_index: int


def citations_for_indices(
    indices: list[int], markers: dict[int, RetrievedChunk]
) -> tuple[list[Citation], list[int]]:
    """Map cited evidence indices to Citation objects.

    Returns (valid_citations, invalid_indices). An index not present in the
    provided markers is invalid (the model referenced non-existent evidence).
    """
    valid: list[Citation] = []
    invalid: list[int] = []
    seen: set[int] = set()
    for idx in indices:
        if idx in seen:
            continue
        seen.add(idx)
        chunk = markers.get(idx)
        if chunk is None:
            invalid.append(idx)
            continue
        valid.append(
            Citation(
                source_id=str(chunk.source_id),
                chunk_id=str(chunk.chunk_id),
                source_url=chunk.source_url,
                page_number=chunk.page_number,
                section=chunk.section,
                evidence_index=idx,
            )
        )
    return valid, invalid


def extract_evidence_refs(text: str) -> list[int]:
    """Parse [EVIDENCE n] references from a model answer."""
    return [int(m.group(1)) for m in _EVIDENCE_REF_RE.finditer(text or "")]
