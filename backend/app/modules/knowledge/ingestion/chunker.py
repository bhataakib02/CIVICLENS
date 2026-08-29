"""Deterministic chunking (prompt §10).

Groups normalized blocks into chunks that:
- respect heading/section boundaries (a new heading starts a new chunk),
- respect paragraph boundaries (never split mid-paragraph unless a single
  paragraph exceeds the size limit, in which case it is split on sentence-ish
  boundaries),
- stay within a target character budget with a fixed overlap,
- carry section + page_number metadata,
- get a stable chunk_hash (sha256 of normalized content + section + page),
  so the SAME source always produces the SAME chunk hashes (idempotency).

Determinism: no randomness, no wall-clock, pure function of the input blocks
and the fixed size parameters below.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from app.modules.knowledge.ingestion.parser import ParsedBlock, ParsedDocument

# Fixed, deterministic chunk parameters (characters, not tokens, to avoid a
# tokenizer dependency; ~4 chars/token => ~500 tokens per chunk).
CHUNK_MAX_CHARS = 2000
CHUNK_OVERLAP_CHARS = 200
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


@dataclass
class Chunk:
    content: str
    section: str | None
    page_number: int | None
    chunk_index: int
    chunk_hash: str
    char_start: int
    char_end: int


def _hash(content: str, section: str | None, page: int | None) -> str:
    h = hashlib.sha256()
    h.update((section or "").encode("utf-8"))
    h.update(b"\x00")
    h.update(str(page if page is not None else "").encode("utf-8"))
    h.update(b"\x00")
    h.update(content.encode("utf-8"))
    return h.hexdigest()


def _split_large(paragraph: str) -> list[str]:
    """Split an oversized paragraph deterministically on sentence boundaries,
    then hard-wrap any residual sentence longer than the budget."""
    pieces: list[str] = []
    buf = ""
    for sentence in _SENTENCE_SPLIT.split(paragraph):
        if not sentence:
            continue
        if len(buf) + len(sentence) + 1 <= CHUNK_MAX_CHARS:
            buf = f"{buf} {sentence}".strip()
        else:
            if buf:
                pieces.append(buf)
            if len(sentence) <= CHUNK_MAX_CHARS:
                buf = sentence
            else:
                for i in range(0, len(sentence), CHUNK_MAX_CHARS):
                    pieces.append(sentence[i : i + CHUNK_MAX_CHARS])
                buf = ""
    if buf:
        pieces.append(buf)
    return pieces


def chunk_document(doc: ParsedDocument) -> list[Chunk]:
    chunks: list[Chunk] = []
    cursor = 0

    def emit(content: str, section: str | None, page: int | None) -> None:
        nonlocal cursor
        content = content.strip()
        if not content:
            return
        start = cursor
        end = cursor + len(content)
        cursor = end
        idx = len(chunks)
        chunks.append(
            Chunk(
                content=content,
                section=section,
                page_number=page,
                chunk_index=idx,
                chunk_hash=_hash(content, section, page),
                char_start=start,
                char_end=end,
            )
        )

    # Group consecutive blocks by (section heading, page) then pack.
    current_section: str | None = None
    buf = ""
    buf_page: int | None = None

    def flush(section: str | None) -> None:
        nonlocal buf, buf_page
        if buf.strip():
            emit(buf, section, buf_page)
        buf = ""
        buf_page = None

    for block in doc.blocks:
        # A heading block starts a new section (and a new chunk boundary).
        if block.heading and block.heading == block.text:
            flush(current_section)
            current_section = block.heading
            continue

        section = block.heading or current_section
        para = block.text
        if len(para) > CHUNK_MAX_CHARS:
            flush(section)
            for piece in _split_large(para):
                emit(piece, section, block.page_number)
            continue

        if buf and (len(buf) + len(para) + 2 > CHUNK_MAX_CHARS or buf_page != block.page_number):
            flush(section)
        # Apply deterministic overlap: seed the new buffer with the tail of the
        # previous chunk when starting fresh within the same section.
        if not buf and chunks and CHUNK_OVERLAP_CHARS > 0 and chunks[-1].section == section:
            tail = chunks[-1].content[-CHUNK_OVERLAP_CHARS:]
            buf = tail
        buf = f"{buf}\n\n{para}".strip() if buf else para
        buf_page = block.page_number

    flush(current_section)
    return chunks
