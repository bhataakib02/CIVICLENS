# Document Intelligence

Status: v1.0 draft
Related: entity-extraction.md, ai-architecture.md §2.3, database/data-dictionary.md (documents, document_extractions), FR-DOCS-*

## 1. Pipeline

```
Upload (image/PDF) → validation + malware scan (document-security.md)
   → OCR (managed provider, pluggable interface)
   → structured field extraction (entity-extraction.md)
   → confidence scoring
   → citizen confirmation step (FR-DOCS-3)
   → verified data usable in profile/applications
```

Runs entirely in the async worker tier (`workers/ocr`, ADR-006) — never on
the synchronous request path.

## 2. Supported Document Types

Aadhaar (identity), income certificate, residence proof, caste/category
certificate, disability certificate, and an "other" catch-all that still
runs OCR but doesn't attempt structured extraction beyond raw text.

## 3. Confidence Handling

Each extracted field carries a confidence score (0–1). Below a defined
threshold, the field is flagged for citizen re-entry rather than silently
accepted (FR-DOCS-4) — the system never guesses a low-confidence value
into the profile. Confidence thresholds are calibrated against a labeled
sample (testing/ai-testing.md) and revisited as OCR provider or document
quality patterns change.

## 4. Human-in-the-Loop

No extracted field is used in eligibility evaluation or an application
until the citizen has confirmed it (`document_extractions.verified_by_citizen`).
This is a hard requirement, not a UX nicety — it's the mechanism that keeps
document intelligence in the "assistive extraction" category rather than
the "automated decision" category from ai-architecture.md §1.

## 5. Reuse

Once verified, extracted data can pre-fill profile fields and future
applications without re-extraction (FR-DOCS-5), reducing redundant OCR
calls and redundant citizen data entry.
