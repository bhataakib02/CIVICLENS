"""Content normalization (prompt §9).

Operates on ParsedBlocks, preserving section/heading/page boundaries. It:
- applies Unicode NFKC normalization,
- collapses runs of whitespace within a block,
- removes exact duplicate lines that repeat across many blocks (typical PDF
  running headers/footers),
- drops empty blocks.

It deliberately does NOT lowercase, stem, or strip punctuation — that would
destroy meaningful policy language (income figures, clause numbers).
"""
from __future__ import annotations

import re
import unicodedata
from collections import Counter

from app.modules.knowledge.ingestion.parser import ParsedBlock, ParsedDocument

_WS_RE = re.compile(r"[ \t\u00a0]+")
_MULTI_NL_RE = re.compile(r"\n{3,}")
# A running header/footer must be short and repeat on many pages to be dropped.
_MAX_REPEAT_LINE_LEN = 80
_MIN_REPEAT_FRACTION = 0.5


def _clean_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    # Normalize line endings, collapse intra-line whitespace, cap blank runs.
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [_WS_RE.sub(" ", ln).strip() for ln in text.split("\n")]
    text = "\n".join(lines)
    text = _MULTI_NL_RE.sub("\n\n", text)
    return text.strip()


def _repeating_lines(blocks: list[ParsedBlock]) -> set[str]:
    """Identify short lines that repeat across a large fraction of paged blocks
    (running headers/footers)."""
    paged = [b for b in blocks if b.page_number is not None]
    if len(paged) < 3:
        return set()
    counts: Counter[str] = Counter()
    for b in paged:
        for ln in b.text.split("\n"):
            s = ln.strip()
            if s and len(s) <= _MAX_REPEAT_LINE_LEN:
                counts[s] += 1
    threshold = max(3, int(len(paged) * _MIN_REPEAT_FRACTION))
    return {line for line, n in counts.items() if n >= threshold}


def normalize(doc: ParsedDocument) -> ParsedDocument:
    repeating = _repeating_lines(doc.blocks)
    out: list[ParsedBlock] = []
    for b in doc.blocks:
        cleaned = _clean_text(b.text)
        if repeating:
            kept = [ln for ln in cleaned.split("\n") if ln.strip() not in repeating]
            cleaned = "\n".join(kept).strip()
        if not cleaned:
            continue
        heading = _clean_text(b.heading) if b.heading else None
        out.append(ParsedBlock(text=cleaned, heading=heading or None, page_number=b.page_number))
    return ParsedDocument(blocks=out)
