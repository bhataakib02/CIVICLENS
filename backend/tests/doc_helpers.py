"""Helpers for building valid test document bytes (PNG/JPEG/PDF)."""
from __future__ import annotations

import io
import struct
import zlib

from app.modules.documents.processing.ocr import make_test_image_with_ocr_text


def png_bytes(width: int = 1, height: int = 1) -> bytes:
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = b"IHDR" + struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    ihdr_c = struct.pack(">I", len(ihdr) - 4) + ihdr + struct.pack(">I", zlib.crc32(ihdr) & 0xFFFFFFFF)
    idat_raw = b"IDAT" + zlib.compress(b"\x00" * (width * height * 3 + height))
    idat = struct.pack(">I", len(idat_raw) - 4) + idat_raw + struct.pack(">I", zlib.crc32(idat_raw) & 0xFFFFFFFF)
    iend = struct.pack(">I", 0) + b"IEND" + struct.pack(">I", zlib.crc32(b"IEND") & 0xFFFFFFFF)
    return sig + ihdr_c + idat + iend


def jpeg_bytes(width: int = 8, height: int = 8) -> bytes:
    # Minimal JPEG: SOI + APP0 + SOF0 (dimensions) + EOI. Enough for magic-byte
    # + dimension validation (not a decodable image, but structurally valid header).
    soi = b"\xff\xd8"
    app0 = b"\xff\xe0" + struct.pack(">H", 16) + b"JFIF\x00" + b"\x01\x01\x00" + struct.pack(">HH", 1, 1) + b"\x00\x00"
    sof0 = b"\xff\xc0" + struct.pack(">H", 17) + b"\x08" + struct.pack(">HH", height, width) + b"\x03\x01\x11\x00\x02\x11\x01\x03\x11\x01"
    eoi = b"\xff\xd9"
    return soi + app0 + sof0 + eoi


def pdf_bytes(text: str = "Income Certificate\nAnnual Income: 200000") -> bytes:
    """A minimal one-page PDF with a text stream (readable by pypdf)."""
    # Build a tiny valid PDF with one page and a content stream drawing text.
    escaped = text.replace("(", "\\(").replace(")", "\\)")
    lines = escaped.split("\n")
    content_ops = "BT /F1 12 Tf 50 700 Td 14 TL "
    for ln in lines:
        content_ops += f"({ln}) Tj T* "
    content_ops += "ET"
    stream = content_ops.encode("latin-1")

    objs = []
    objs.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objs.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    objs.append(
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>"
    )
    objs.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    objs.append(b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream")

    buf = io.BytesIO()
    buf.write(b"%PDF-1.4\n")
    offsets = []
    for i, body in enumerate(objs, start=1):
        offsets.append(buf.tell())
        buf.write(f"{i} 0 obj\n".encode() + body + b"\nendobj\n")
    xref_pos = buf.tell()
    n = len(objs) + 1
    buf.write(f"xref\n0 {n}\n".encode())
    buf.write(b"0000000000 65535 f \n")
    for off in offsets:
        buf.write(f"{off:010d} 00000 n \n".encode())
    buf.write(b"trailer\n<< /Size " + str(n).encode() + b" /Root 1 0 R >>\n")
    buf.write(b"startxref\n" + str(xref_pos).encode() + b"\n%%EOF")
    return buf.getvalue()


INCOME_OCR_TEXT = (
    "INCOME CERTIFICATE\n"
    "Name: Demo Citizen\n"
    "Annual Income: Rs 2,00,000\n"
    "Financial Year: 2025-2026\n"
    "Issuing Authority: Demo Tehsildar\n"
    "Certificate Number: DEMO-INC-001\n"
    "State: West Bengal"
)


def income_png(text: str = INCOME_OCR_TEXT) -> bytes:
    return make_test_image_with_ocr_text(png_bytes(4, 4), text)
