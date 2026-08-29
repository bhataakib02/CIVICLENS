# `ai/` — RAG, Extraction & Classification Library

Shared library consumed by both `backend/app/modules/assistant` (synchronous
chat) and `workers/ingestion` (batch knowledge processing). Not a standalone
deployable.

## Responsibilities

- Retrieval pipeline (hybrid lexical + semantic) over `knowledge_chunks` —
  see `docs/ai/retrieval-pipeline.md`.
- Prompt assembly and generation orchestration — `docs/ai/prompt-engineering.md`,
  `docs/ai/rag-architecture.md`.
- Citation verification post-processing — `docs/ai/hallucination-controls.md`.
- Document field extraction and classification helpers used by
  `workers/ocr` — `docs/ai/entity-extraction.md`, `docs/ai/classification.md`.
- Eligibility-question tool-calling into
  `backend/app/modules/eligibility.service` — never itself decides
  eligibility (`docs/ai/ai-architecture.md` §1, ADR-003).

## Explicitly Not Here

The deterministic eligibility engine (`docs/ai/eligibility-engine.md`) lives
in `backend/app/modules/eligibility`, not in this package — despite the
"ai" naming convention on the docs, that engine has no model dependency.

## Before Changing Anything Here

Any change to prompts, retrieval configuration, or the model version used
must pass the evaluation gate in `docs/decisions/ADR-009-ai-evaluation-gates.md`
before merging — see `docs/ai/ai-evaluation.md` and
`docs/testing/ai-testing.md`.

## Rules

- Preserve module boundaries (`docs/backend/module-boundaries.md`).
- Add/update evaluation-set cases for any behavior change affecting
  generation quality.
- Never commit secrets, API keys, or real citizen data, including in
  test fixtures.
- Update `docs/ai/*` when a contract or pipeline behavior changes.
