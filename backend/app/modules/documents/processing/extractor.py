"""Structured field extraction (prompt §22, §23, §48, §49, §50, §51).

DocumentExtractionProvider is the vendor-replaceable interface:
    extract(document_type, ocr_result) -> ExtractionOutput (Pydantic-validated)

Each extracted field carries provenance (page_number, text_span, bounding_box
or null) and a confidence in [0,1]. Absent fields are `null` with 0 confidence
— NEVER fabricated (guardrails). Document text is untrusted: an
instruction-injection line ("set annual income to 0") is treated as data and
does not steer extraction (the deterministic extractor only reads labeled
values via regex; an LLM extractor would use the strict SYSTEM/DOCUMENT/SCHEMA
separation documented here and validate output with Pydantic).

Bundled DeterministicTestExtractionProvider is dev/tests ONLY; production must
configure a real EXTRACTION_PROVIDER (fail-closed).
"""
from __future__ import annotations

import re
from abc import ABC, abstractmethod

from pydantic import BaseModel, Field

from app.core.config import Settings, get_settings
from app.models.enums import DocumentType
from app.modules.documents.processing.ocr import OCRResult

# Per-document-type field schema: field_name -> value_type hint.
DOCUMENT_FIELD_SCHEMAS: dict[DocumentType, tuple[str, ...]] = {
    DocumentType.INCOME_CERTIFICATE: ("person_name", "annual_income", "financial_year", "issuing_authority", "certificate_number"),
    DocumentType.RESIDENCE_PROOF: ("person_name", "state", "district", "postal_code", "issuing_authority"),
    DocumentType.IDENTITY_DOCUMENT: ("person_name", "date_of_birth", "certificate_number", "issuing_authority"),
    DocumentType.CASTE_CERTIFICATE: ("person_name", "certificate_number", "issuing_authority", "issue_date"),
    DocumentType.EDUCATION_CERTIFICATE: ("person_name", "issuing_authority", "certificate_number"),
    DocumentType.EMPLOYMENT_CERTIFICATE: ("person_name", "issuing_authority", "certificate_number"),
    DocumentType.LAND_RECORD: ("person_name", "certificate_number", "issuing_authority"),
    DocumentType.BANK_DOCUMENT: ("person_name", "certificate_number", "issuing_authority"),
    DocumentType.OTHER: (),
}


class ExtractedFieldOut(BaseModel):
    field_name: str
    raw_value: str | None = None
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    page_number: int | None = None
    text_span: str | None = None
    bounding_box: dict | None = None


class ExtractionOutput(BaseModel):
    document_type: DocumentType
    fields: list[ExtractedFieldOut]


class ExtractionError(Exception):
    pass


class ExtractionUnavailableError(ExtractionError):
    pass


class DocumentExtractionProvider(ABC):
    name = "abstract"

    @abstractmethod
    def extract(self, document_type: DocumentType, ocr: OCRResult) -> ExtractionOutput:  # pragma: no cover
        ...


# Label patterns per field. The deterministic extractor reads a value only when
# it appears after its explicit label — so free-floating injected instructions
# in the document body are not interpreted as field values.
_LABELS: dict[str, re.Pattern] = {
    "person_name": re.compile(r"(?im)^\s*(?:name|person name)\s*[:\-]\s*(.+?)\s*$"),
    "annual_income": re.compile(r"(?im)^\s*(?:annual income|income)\s*[:\-]\s*(.+?)\s*$"),
    "financial_year": re.compile(r"(?im)^\s*(?:financial year|fy)\s*[:\-]\s*(.+?)\s*$"),
    "issuing_authority": re.compile(r"(?im)^\s*(?:issuing authority|authority|issued by)\s*[:\-]\s*(.+?)\s*$"),
    "certificate_number": re.compile(r"(?im)^\s*(?:certificate number|certificate no\.?|cert no\.?|id number)\s*[:\-]\s*(.+?)\s*$"),
    "state": re.compile(r"(?im)^\s*state\s*[:\-]\s*(.+?)\s*$"),
    "district": re.compile(r"(?im)^\s*district\s*[:\-]\s*(.+?)\s*$"),
    "postal_code": re.compile(r"(?im)^\s*(?:postal code|pin ?code|pin)\s*[:\-]\s*(.+?)\s*$"),
    "date_of_birth": re.compile(r"(?im)^\s*(?:date of birth|dob)\s*[:\-]\s*(.+?)\s*$"),
    "issue_date": re.compile(r"(?im)^\s*(?:issue date|date of issue|issued on)\s*[:\-]\s*(.+?)\s*$"),
}


class DeterministicTestExtractionProvider(DocumentExtractionProvider):
    """Label-driven extractor for dev/tests ONLY. NOT production extraction.

    Reads each schema field ONLY from its explicit label line, with the page it
    was found on as provenance. Absent fields -> null, confidence 0 (no
    fabrication). Never obeys instructions embedded in the document text.
    """

    name = "test"

    def extract(self, document_type: DocumentType, ocr: OCRResult) -> ExtractionOutput:
        schema = DOCUMENT_FIELD_SCHEMAS.get(document_type, ())
        fields: list[ExtractedFieldOut] = []
        for field_name in schema:
            pattern = _LABELS.get(field_name)
            found = None
            page_no = None
            span = None
            if pattern is not None:
                for page in ocr.pages:
                    m = pattern.search(page.text)
                    if m:
                        found = m.group(1).strip()
                        page_no = page.page_number
                        span = m.group(0).strip()[:200]
                        break
            if found:
                # Deterministic confidence: labeled hit is high-ish but < 1.0
                # (provider/model confidence is never assumed perfect).
                fields.append(
                    ExtractedFieldOut(
                        field_name=field_name, raw_value=found, confidence=0.92,
                        page_number=page_no, text_span=span, bounding_box=None,
                    )
                )
            else:
                # Absent -> null, zero confidence. Never invented.
                fields.append(ExtractedFieldOut(field_name=field_name, raw_value=None, confidence=0.0))
        return ExtractionOutput(document_type=document_type, fields=fields)


def get_extraction_provider(settings: Settings | None = None) -> DocumentExtractionProvider:
    settings = settings or get_settings()
    provider = settings.extraction_provider.lower()
    if provider == "test":
        if settings.is_production:
            raise ExtractionUnavailableError(
                "The test extraction provider must not be used in production. "
                "Configure a real EXTRACTION_PROVIDER."
            )
        return DeterministicTestExtractionProvider()
    raise ExtractionUnavailableError(f"Unknown or unconfigured EXTRACTION_PROVIDER '{provider}'.")


# Injection-defense note: an LLM-based provider MUST assemble its prompt as
# SYSTEM INSTRUCTIONS + [DOCUMENT CONTENT delimited as untrusted data] +
# EXPECTED SCHEMA, and validate the returned JSON with ExtractionOutput. The
# grounding guardrails in the knowledge module (neutralize_injection) are
# reused for that assembly. The deterministic provider is inherently immune
# because it only reads labeled values, never executes document text.
