# `workers` — Celery Async Task Definitions

Background job definitions for OCR/extraction, knowledge ingestion, and
notification dispatch — the async half of the system's request handling
(ADR-006). Runs as a separate ECS/Fargate service from the API tier,
sharing the same codebase/image with a different entrypoint.

## Structure

```
workers/
├── ocr/            # document upload → OCR → entity extraction
├── ingestion/       # knowledge source → chunk → embed
└── notifications/   # notification event → SMS/email dispatch
```

See `docs/backend/background-jobs.md` for the full job catalog, retry
policy, and queue design, and `docs/architecture/system-architecture.md`
§3.2 for why these are async in the first place.

## Local Development

`docker compose up` runs a `worker` container using the same image as
`backend` with a Celery entrypoint instead of uvicorn, against the same
local Redis broker — the full async pipeline (e.g., document upload → OCR
→ extraction) is testable locally without any cloud dependency
(`docs/infrastructure/docker.md` §2).

## Rules

- Every job is idempotent — safe to retry or re-run without duplicating
  effects (`docs/backend/background-jobs.md` §1).
- Jobs use bounded retry + backoff, then dead-letter — no infinite retry,
  no silent drop (`docs/backend/background-jobs.md` §3,
  `docs/operations/runbooks.md` §2).
- Worker IAM roles are least-privilege per job type — the OCR worker in
  particular has no broader storage/database access than it strictly
  needs (`docs/security/document-security.md` §3).
- Do not commit secrets or real citizen data.
