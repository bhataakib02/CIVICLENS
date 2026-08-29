# `backend` — FastAPI Modular Monolith

The core API service: auth, citizens, schemes, eligibility, documents,
applications, assistant, notifications, admin — organized as a modular
monolith (ADR-001).

## Before Implementing

Read, in order: `docs/architecture/system-architecture.md`,
`docs/architecture/component-architecture.md`,
`docs/backend/backend-architecture.md`,
`docs/backend/module-boundaries.md`, `docs/backend/service-layer.md`,
`docs/backend/repository-pattern.md`.

## Local Setup

See `CONTRIBUTING.md` §1 for the full `docker compose up` + Alembic +
uvicorn workflow.

## Structure

```
app/
├── api/v1/       # thin routers, one per module
├── core/          # config, security, logging, shared exceptions
├── db/             # session management, declarative base
├── modules/        # domain modules — see component-architecture.md §1
└── main.py
migrations/         # Alembic
tests/               # mirrors app/ structure
```

## Hard Rules (CI-enforced, not just convention)

- Cross-module imports: `service`/`schemas` only, never `models`/
  `repository` (`docs/backend/module-boundaries.md`) — enforced via
  import-linting in CI.
- Eligibility is never decided by an LLM call — the engine in
  `modules/eligibility` is deterministic, in-process, no network calls
  (ADR-003, `docs/ai/eligibility-engine.md`).
- Every endpoint must match `openapi.yaml`; drift fails CI
  (`docs/api/api-overview.md` §6, `docs/testing/api-testing.md`).

## Rules

- Add tests with behavior changes; coverage gates in
  `docs/testing/testing-strategy.md` §2.
- Do not commit secrets or real citizen data — use the synthetic fixture
  set (`docs/testing/testing-strategy.md` §10).
- Update `docs/database/erd.md`/`data-dictionary.md` alongside any schema
  migration; update `openapi.yaml` alongside any endpoint change.
