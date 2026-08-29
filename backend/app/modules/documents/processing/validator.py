"""File validation (prompt §5, §14, §15, §44, §47).

Validates by CONTENT (magic bytes) not by filename/extension. Enforces the
allowed type set (PDF/JPEG/PNG), size limits, PDF page count, and image
dimensions (decompression / pixel-flood guard). Pure functions over bytes; no
external deps (PNG/JPEG dimensions parsed from headers, PDF pages counted via
pypdf which is already a dependency).

Returns a ValidationResult with the detected MIME and normalized extension, or
raises FileValidationError (a PERMANENT error — never retried).
"""
from __future__ import annotations

import io
import struct
from dataclasses import dataclass

from app.core.config import Settings, get_settings

SUPPORTED = {
    "application/pdf": "pdf",
    "image/jpeg": "jpeg",
    "image/png": "png",
}


class FileValidationError(Exception):
    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass
class ValidationResult:
    mime_type: str
    extension: str
    size_bytes: int
    page_count: int | None
    width: int | None
    height: int | None


def _sniff_mime(data: bytes) -> str | None:
    if data[:5] == b"%PDF-":
        return "application/pdf"
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    return None


def _png_dimensions(data: bytes) -> tuple[int, int] | None:
    # IHDR chunk begins at byte 16; width/height are big-endian uint32.
    if len(data) < 24 or data[12:16] != b"IHDR":
        return None
    width, height = struct.unpack(">II", data[16:24])
    return width, height


def _jpeg_dimensions(data: bytes) -> tuple[int, int] | None:
    # Walk JPEG segments to the SOF marker for dimensions.
    i = 2
    n = len(data)
    while i + 9 < n:
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            height = struct.unpack(">H", data[i + 5 : i + 7])[0]
            width = struct.unpack(">H", data[i + 7 : i + 9])[0]
            return width, height
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        seg_len = struct.unpack(">H", data[i + 2 : i + 4])[0]
        i += 2 + seg_len
    return None


def _pdf_page_count(data: bytes) -> int | None:
    try:
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(data))
        return len(reader.pages)
    except Exception:
        return None


def validate_file(
    data: bytes,
    *,
    declared_mime: str | None = None,
    settings: Settings | None = None,
) -> ValidationResult:
    settings = settings or get_settings()

    size = len(data)
    if size == 0:
        raise FileValidationError("Empty file.", code="EMPTY_FILE")
    if size > settings.document_max_size_bytes:
        raise FileValidationError("File exceeds maximum size.", code="FILE_TOO_LARGE")

    mime = _sniff_mime(data)
    if mime is None or mime not in SUPPORTED:
        raise FileValidationError("Unsupported or unrecognized file type.", code="UNSUPPORTED_TYPE")

    # MIME-spoofing guard: if the client declared a type, it must match the
    # sniffed content type (we trust content, not the declaration).
    if declared_mime and declared_mime.split(";")[0].strip().lower() not in (mime,):
        raise FileValidationError("Declared MIME does not match file content.", code="MIME_MISMATCH")

    page_count: int | None = None
    width = height = None

    if mime == "application/pdf":
        page_count = _pdf_page_count(data)
        if page_count is None:
            raise FileValidationError("Corrupt or unreadable PDF.", code="CORRUPT_FILE")
        if page_count == 0:
            raise FileValidationError("PDF has no pages.", code="CORRUPT_FILE")
        if page_count > settings.document_max_pages:
            raise FileValidationError("PDF exceeds maximum page count.", code="TOO_MANY_PAGES")
    else:
        dims = _png_dimensions(data) if mime == "image/png" else _jpeg_dimensions(data)
        if dims is None:
            raise FileValidationError("Corrupt or unreadable image.", code="CORRUPT_FILE")
        width, height = dims
        if width <= 0 or height <= 0:
            raise FileValidationError("Invalid image dimensions.", code="CORRUPT_FILE")
        if width * height > settings.document_max_image_pixels:
            # Pixel-flood / decompression-bomb guard.
            raise FileValidationError("Image dimensions exceed the allowed limit.", code="IMAGE_TOO_LARGE")

    return ValidationResult(
        mime_type=mime, extension=SUPPORTED[mime], size_bytes=size,
        page_count=page_count, width=width, height=height,
    )
