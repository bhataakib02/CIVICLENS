# Entity Extraction

Status: v1.0 draft
Related: document-intelligence.md, classification.md, database/data-dictionary.md (document_extractions.extracted_fields)

## 1. Target Fields (per document type)

| Document type | Extracted fields |
|---|---|
| Aadhaar | full_name, date_of_birth, aadhaar_last_4 (never store full number — see below), address |
| Income certificate | applicant_name, annual_income, issuing_authority, issue_date, validity_date |
| Residence proof | full_name, address, state, district, issue_date |
| Caste/category certificate | full_name, category, issuing_authority, issue_date |
| Disability certificate | full_name, disability_type, percentage, issuing_authority, validity_date |

## 2. Method

A combination of OCR text output + a structured-extraction pass (prompted
LLM call constrained to return only fields from a fixed schema, or a
fine-tuned extraction model, per current provider — see model-selection.md).
Extraction is schema-constrained (the model cannot invent field names) and
does not have access to any tool that could take action — it only returns
structured data for citizen confirmation.

## 3. Full Identifier Handling

Full government ID numbers (e.g., full Aadhaar number) are never persisted
in `document_extractions.extracted_fields` in plaintext — only a masked/
truncated reference is stored for the citizen's own recognition purposes;
the original document image (already access-controlled per
document-security.md) remains the authoritative record if the full number
is ever needed, minimizing the surface area of a second copy of
maximally-sensitive identifiers.

## 4. Multi-Language Support

Extraction handles documents in Hindi and English at launch, consistent
with NFR-ACC-3; extracted structured field values are normalized to a
consistent format (e.g., dates to ISO 8601) regardless of source-document
language.

## 5. Failure Modes

Illegible scans, unsupported document types, or extraction confidence
below threshold all result in an explicit "needs re-capture" status
surfaced to the citizen (FR-DOCS-4), never a silently incomplete or
guessed extraction.
