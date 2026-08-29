"""Document classification (prompt §21).

Deterministic keyword-signal classifier over OCR text. Returns a document type
+ confidence in [0,1]. Below the configured threshold the pipeline routes to
VERIFICATION_REQUIRED (never a silent uncertain classification).

This is a transparent, reproducible classifier — a model-based classifier could
replace it behind the same function signature.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from app.models.enums import DocumentType

# Keyword signals per type (lowercased, word-ish).
_SIGNALS: dict[DocumentType, tuple[str, ...]] = {
    DocumentType.INCOME_CERTIFICATE: ("income", "annual income", "salary", "financial year", "income certificate"),
    DocumentType.RESIDENCE_PROOF: ("residence", "resident", "address proof", "domicile", "residence proof"),
    DocumentType.IDENTITY_DOCUMENT: ("identity", "identification", "date of birth", "id number", "passport"),
    DocumentType.CASTE_CERTIFICATE: ("caste", "category certificate", "scheduled caste", "obc", "community certificate"),
    DocumentType.DISABILITY_CERTIFICATE: ("disability", "disabled", "handicap", "divyang"),
    DocumentType.EDUCATION_CERTIFICATE: ("degree", "marksheet", "university", "diploma", "education", "graduation"),
    DocumentType.EMPLOYMENT_CERTIFICATE: ("employment", "employer", "designation", "appointment", "experience certificate"),
    DocumentType.LAND_RECORD: ("land", "khasra", "khatauni", "survey number", "acres", "landholding"),
    DocumentType.BANK_DOCUMENT: ("bank", "account number", "ifsc", "statement", "passbook"),
}

_TOKEN_RE = re.compile(r"[a-z][a-z ]+")


@dataclass
class ClassificationResult:
    document_type: DocumentType
    confidence: float


def classify(text: str, *, declared_type: DocumentType | None = None) -> ClassificationResult:
    lowered = (text or "").lower()
    if not lowered.strip():
        return ClassificationResult(DocumentType.OTHER, 0.0)

    scores: dict[DocumentType, int] = {}
    for dtype, signals in _SIGNALS.items():
        hits = sum(1 for s in signals if s in lowered)
        if hits:
            scores[dtype] = hits

    if not scores:
        return ClassificationResult(DocumentType.OTHER, 0.2)

    best_type = max(scores, key=lambda k: scores[k])
    best = scores[best_type]
    total = sum(scores.values())
    # Confidence = dominance of the top signal, bounded to a sensible range.
    confidence = round(min(0.99, 0.5 + 0.5 * (best / total)), 3)

    # A matching declared type nudges confidence up (citizen intent corroborates).
    if declared_type is not None and declared_type == best_type:
        confidence = round(min(0.99, confidence + 0.1), 3)

    return ClassificationResult(best_type, confidence)
