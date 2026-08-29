# `data` — Fixtures & Non-Production Datasets

Synthetic test fixtures used across unit, integration, and E2E tests, and
by local development seeding. **Never contains real citizen data or real
government document content beyond what's needed for realistic, clearly
synthetic testing** — see `docs/testing/testing-strategy.md` §10 and
`docs/security/pii-handling.md`.

## Contents

- `data/citizens/` — synthetic citizen profile fixtures spanning a range
  of demographic/socioeconomic attribute combinations, used to exercise
  the eligibility engine's rule operators and the RAG evaluation set's
  eligibility-routing test cases.
- `data/schemes/` — sample scheme/scheme_version/eligibility_rules
  fixtures covering the full DSL operator set (`docs/ai/rule-dsl.md`),
  used in unit and integration tests.
- `data/knowledge/` — sanitized sample "government-style" source
  documents (not real government publications, written to resemble their
  structure) for ingestion pipeline testing.
- `data/documents/` — synthetic sample identity/income/residence document
  images for OCR/extraction pipeline testing.

## Rules

- No file in this directory may contain real PII, real government
  document content that isn't already public and explicitly permitted for
  reuse, or anything resembling an actual citizen's data.
- Fixtures are versioned alongside the tests/features that depend on
  them — a fixture change that breaks tests is a signal to investigate,
  not to regenerate blindly.
- New document types or rule operators added to the system should come
  with corresponding fixture coverage here in the same PR.
