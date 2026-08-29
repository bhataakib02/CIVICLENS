"""Document parsers (prompt §8).

Produces a ParsedDocument: a list of ParsedBlock (text + optional heading +
page_number). Never raises on messy input — on failure it returns an empty
document, and the pipeline marks the source REJECTED rather than silently
storing empty content.

- HTML: stdlib html.parser (no bs4/lxml system deps). Drops script/style/nav/
  header/footer/aside/form; retains headings (h1-h6 -> section markers),
  paragraphs, and list items.
- PDF: pypdf, one block per page, page_number retained.
- text/plain: paragraphs split on blank lines.
"""
from __future__ import annotations

import io
from dataclasses import dataclass, field
from html.parser import HTMLParser

from app.core.logging import get_logger

logger = get_logger("civiclens.knowledge.parser")

_BOILERPLATE_TAGS = {"script", "style", "nav", "header", "footer", "aside", "form", "noscript"}
_HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
_BLOCK_TAGS = {"p", "li", "td", "th", "blockquote", "pre", "div", "section", "article"}


@dataclass
class ParsedBlock:
    text: str
    heading: str | None = None
    page_number: int | None = None


@dataclass
class ParsedDocument:
    blocks: list[ParsedBlock] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not any(b.text.strip() for b in self.blocks)

    @property
    def text(self) -> str:
        return "\n\n".join(b.text for b in self.blocks if b.text.strip())


class _HTMLExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: list[ParsedBlock] = []
        self._skip_depth = 0
        self._buf: list[str] = []
        self._current_heading: str | None = None
        self._in_heading = False
        self._heading_buf: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in _BOILERPLATE_TAGS:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if tag in _HEADING_TAGS:
            self._flush()
            self._in_heading = True
            self._heading_buf = []
        elif tag in _BLOCK_TAGS:
            self._flush()
        elif tag == "br":
            self._buf.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in _BOILERPLATE_TAGS and self._skip_depth:
            self._skip_depth -= 1
            return
        if self._skip_depth:
            return
        if tag in _HEADING_TAGS and self._in_heading:
            heading = " ".join("".join(self._heading_buf).split()).strip()
            self._current_heading = heading or self._current_heading
            if heading:
                self.blocks.append(ParsedBlock(text=heading, heading=heading))
            self._in_heading = False
            self._heading_buf = []
        elif tag in _BLOCK_TAGS:
            self._flush()

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        if self._in_heading:
            self._heading_buf.append(data)
        else:
            self._buf.append(data)

    def _flush(self) -> None:
        text = " ".join("".join(self._buf).split()).strip()
        self._buf = []
        if text:
            self.blocks.append(ParsedBlock(text=text, heading=self._current_heading))

    def close(self) -> None:  # type: ignore[override]
        super().close()
        self._flush()


def parse_html(data: bytes | str) -> ParsedDocument:
    try:
        html = data.decode("utf-8", errors="replace") if isinstance(data, bytes) else data
        ext = _HTMLExtractor()
        ext.feed(html)
        ext.close()
        # Deduplicate exact repeated blocks (common nav/boilerplate remnants).
        seen: set[str] = set()
        blocks: list[ParsedBlock] = []
        for b in ext.blocks:
            key = b.text.strip()
            if key and key not in seen:
                seen.add(key)
                blocks.append(b)
        return ParsedDocument(blocks=blocks)
    except Exception:
        logger.warning("html_parse_failed")
        return ParsedDocument(blocks=[])


def parse_pdf(data: bytes) -> ParsedDocument:
    try:
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(data))
        blocks: list[ParsedBlock] = []
        for i, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            if text:
                blocks.append(ParsedBlock(text=text, heading=None, page_number=i))
        return ParsedDocument(blocks=blocks)
    except Exception:
        logger.warning("pdf_parse_failed")
        return ParsedDocument(blocks=[])


def parse_text(data: bytes | str) -> ParsedDocument:
    try:
        text = data.decode("utf-8", errors="replace") if isinstance(data, bytes) else data
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        return ParsedDocument(blocks=[ParsedBlock(text=p) for p in paragraphs])
    except Exception:
        logger.warning("text_parse_failed")
        return ParsedDocument(blocks=[])


def parse(content: bytes, content_type: str) -> ParsedDocument:
    """Dispatch by content-type. Unknown types are treated as plain text."""
    ct = (content_type or "").lower()
    if "pdf" in ct:
        return parse_pdf(content)
    if "html" in ct or "xhtml" in ct:
        return parse_html(content)
    return parse_text(content)
