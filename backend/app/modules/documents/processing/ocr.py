"""OCR provider abstraction (prompt §19, §20).

The application depends on OCRProvider, never on a vendor. Output retains
page-level provenance (never a single flattened string).

Bundled providers:
- PdfTextOCRProvider: extracts embedded text from PDFs via pypdf (real, works
  for text-based PDFs — not image OCR, but a genuine local extraction path).
- TestOCRProvider: for dev/tests ONLY. For images (which have no embedded
  text), it reads an in-repo sidecar convention: a test image whose bytes end
  with a UTF-8 block after a `\\n#OCR#\\n` marker returns that block as page
  text. This lets image-OCR paths be tested deterministically WITHOUT claiming
  real OCR. Production must configure a real CloudOCRProvider.

Production requires an explicitly configured real provider; selecting "test" in
production fails closed.
"""
from __future__ import annotations

import io
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.core.config import Settings, get_settings

_OCR_MARKER = b"\n#OCR#\n"


class OCRError(Exception):
    pass


class OCRUnavailableError(OCRError):
    pass


@dataclass
class OCRBlock:
    text: str
    bounding_box: dict | None = None


@dataclass
class OCRPage:
    page_number: int
    text: str
    blocks: list[OCRBlock] = field(default_factory=list)


@dataclass
class OCRResult:
    pages: list[OCRPage]
    provider: str

    @property
    def full_text(self) -> str:
        return "\n\n".join(p.text for p in self.pages if p.text)

    @property
    def is_empty(self) -> bool:
        return not any(p.text.strip() for p in self.pages)


class OCRProvider(ABC):
    name = "abstract"

    @abstractmethod
    def extract_text(self, data: bytes, mime_type: str) -> OCRResult:  # pragma: no cover
        ...


class TestOCRProvider(OCRProvider):
    """Deterministic OCR for dev/tests ONLY. NOT production OCR."""

    name = "test"

    def extract_text(self, data: bytes, mime_type: str) -> OCRResult:
        if "pdf" in mime_type:
            return _pdf_text(data, provider=self.name)
        # Images: read the sidecar test-OCR block if present.
        marker = data.rfind(_OCR_MARKER)
        if marker != -1:
            block = data[marker + len(_OCR_MARKER):].decode("utf-8", errors="replace")
            pages = _split_pages(block)
            return OCRResult(pages=pages, provider=self.name)
        # No embedded text in the image and no sidecar => empty OCR (valid case).
        return OCRResult(pages=[OCRPage(page_number=1, text="", blocks=[])], provider=self.name)


class PdfTextOCRProvider(OCRProvider):
    """Real local text extraction from text-based PDFs (pypdf)."""

    name = "pdf_text"

    def extract_text(self, data: bytes, mime_type: str) -> OCRResult:
        if "pdf" not in mime_type:
            raise OCRError("PdfTextOCRProvider only supports PDF input.")
        return _pdf_text(data, provider=self.name)


def _pdf_text(data: bytes, *, provider: str) -> OCRResult:
    try:
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(data))
    except Exception as exc:
        raise OCRError("Failed to read PDF for OCR.") from exc
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        blocks = [OCRBlock(text=ln.strip()) for ln in text.split("\n") if ln.strip()]
        pages.append(OCRPage(page_number=i, text=text, blocks=blocks))
    return OCRResult(pages=pages or [OCRPage(page_number=1, text="", blocks=[])], provider=provider)


def _split_pages(block: str) -> list[OCRPage]:
    # Test sidecar may separate pages with a form-feed.
    raw_pages = block.split("\f") if "\f" in block else [block]
    pages = []
    for i, txt in enumerate(raw_pages, start=1):
        t = txt.strip()
        pages.append(OCRPage(page_number=i, text=t, blocks=[OCRBlock(text=ln.strip()) for ln in t.split("\n") if ln.strip()]))
    return pages


class TesseractOCRProvider(OCRProvider):
    """Production local OCR using PyTesseract."""

    name = "tesseract"

    def extract_text(self, data: bytes, mime_type: str) -> OCRResult:
        try:
            import pytesseract
            from PIL import Image

            img = Image.open(io.BytesIO(data))
            text = pytesseract.image_to_string(img).strip()
            blocks = [OCRBlock(text=ln.strip()) for ln in text.split("\n") if ln.strip()]
            return OCRResult(
                pages=[OCRPage(page_number=1, text=text, blocks=blocks)],
                provider=self.name,
            )
        except Exception as exc:
            raise OCRError(f"Tesseract OCR processing failed: {exc}") from exc


class AWSTextractOCRProvider(OCRProvider):
    """Production Cloud OCR using AWS Textract."""

    name = "aws_textract"

    def extract_text(self, data: bytes, mime_type: str) -> OCRResult:
        import os

        region = os.getenv("AWS_REGION", "ap-south-1")
        access_key = os.getenv("AWS_ACCESS_KEY_ID")

        if not access_key:
            raise OCRUnavailableError("AWS Textract credentials missing. Activation is PROVIDER-DEPENDENT.")

        try:
            import boto3

            client = boto3.client("textract", region_name=region)
            response = client.detect_document_text(Document={"Bytes": data})

            blocks = []
            raw_lines = []
            for item in response.get("Blocks", []):
                if item.get("BlockType") == "LINE":
                    line_text = item.get("Text", "").strip()
                    if line_text:
                        raw_lines.append(line_text)
                        bbox = item.get("Geometry", {}).get("BoundingBox")
                        blocks.append(OCRBlock(text=line_text, bounding_box=bbox))

            full_text = "\n".join(raw_lines)
            return OCRResult(
                pages=[OCRPage(page_number=1, text=full_text, blocks=blocks)],
                provider=self.name,
            )
        except Exception as exc:
            raise OCRError(f"AWS Textract processing failed: {exc}") from exc


def get_ocr_provider(settings: Settings | None = None) -> OCRProvider:
    settings = settings or get_settings()
    provider = settings.ocr_provider.lower()
    if provider == "test":
        if settings.is_production:
            raise OCRUnavailableError(
                "The test OCR provider must not be used in production. Configure a real OCR_PROVIDER."
            )
        return TestOCRProvider()
    if provider in ("pdf_text", "pdf"):
        return PdfTextOCRProvider()
    if provider == "tesseract":
        return TesseractOCRProvider()
    if provider in ("aws_textract", "textract"):
        return AWSTextractOCRProvider()
    raise OCRUnavailableError(
        f"Unknown or unconfigured OCR_PROVIDER '{provider}'. Supported values: 'test', 'pdf_text', 'tesseract', 'aws_textract'."
    )



def make_test_image_with_ocr_text(base_image: bytes, text: str) -> bytes:
    """Test helper: append an OCR sidecar block to a valid image's bytes."""
    return base_image + _OCR_MARKER + text.encode("utf-8")
