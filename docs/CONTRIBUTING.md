# Contributing to CivicLens

Thanks for working on CivicLens. This is a citizen-facing welfare-eligibility
platform — code quality, correctness, and privacy discipline here have
direct real-world stakes. Read this before your first PR.

## 1. Local Setup

```bash
git clone <repo-url>
cd civiclens
cp .env.example .env          # fill in local secrets — never commit .env
docker compose up -d          # PostgreSQL, Redis
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pre-commit install
alembic upgrade head
uvicorn app.main:app --reload
```

Verify: `GET http://localhost:8000/health` and `/health/ready` both return
200 with a real PostgreSQL connection (per the v0.1 milestone in
docs/architecture/system-architecture.md).

## 2. Repository Structure

See `docs/README.md` for the full documentation map and
`docs/architecture/component-architecture.md` for the module layout. In
short: `backend/app/modules/<domain>` owns its own models/service/router;
`ai/` holds the RAG + extraction pipeline shared between the API and
workers; `workers/` holds Celery task definitions; `apps/web` and
`apps/admin` are the frontends.

## 3. Development Rules

- Keep changes scoped and reviewable — prefer several small PRs over one
  large one.
- Update the relevant `docs/` file(s) in the same PR when behavior,
  architecture, the database schema, or the API contract changes. Docs
  drift is treated as a bug.
- Any change to `eligibility_rules`, the rule DSL grammar, or the
  eligibility engine's evaluation logic requires the reviewer checklist in
  `docs/ai/rule-dsl.md` §6 and `docs/ai/eligibility-engine.md` §7 — this is
  not optional even for "small" changes.
- Any change to the RAG prompt, retrieval configuration, or the model
  version used by the assistant must pass the evaluation gate in
  `docs/decisions/ADR-009-ai-evaluation-gates.md` before merging.
- Cross-module access goes through another module's `service` layer only
  — never import another module's `models` or `repository` directly. This
  is enforced in CI (see `docs/backend/module-boundaries.md`); a failing
  import-lint check is a real failure, not a false positive to work
  around.
- Do not introduce a new dependency without a clear reason stated in the
  PR description.
- Never commit secrets, credentials, real citizen documents, or production
  data of any kind — including in test fixtures or notebooks. Use the
  synthetic fixture set described in `docs/testing/testing-strategy.md`
  §10.
- Add tests for new business logic and any security-sensitive change.
  Coverage gates are described in `docs/testing/testing-strategy.md` §2.

## 4. Commit & Branch Conventions

- Branch names: `feat/<short-desc>`, `fix/<short-desc>`,
  `docs/<short-desc>`, `chore/<short-desc>`.
- Commits: imperative mood, scoped prefix where useful
  (`eligibility: fix boundary case on 'between' operator`).
- Squash-merge to `main`; PR title becomes the squash commit message.

## 5. Pull Request Expectations

Every PR description should cover:
- **What changed** and **why**.
- **Affected modules** (name them explicitly — helps reviewers with
  relevant module context self-select).
- **Database/API changes** — link the migration and/or the `openapi.yaml`
  diff if applicable.
- **Security impact** — "none" is a valid answer, but state it explicitly;
  if the change touches auth, PII, documents, or the rule engine, say so
  and reference `docs/security/threat-model.md` if relevant.
- **Testing performed** — what you ran locally, what CI covers, what (if
  anything) still needs manual verification.
- **Documentation updated** — which files, or explicitly "none needed" with
  a one-line reason.

Use `.github/PULL_REQUEST_TEMPLATE.md` as the starting checklist.

## 6. Code Review

At least one approval required; changes to `eligibility_rules`/rule DSL,
authentication, or authorization require a second reviewer with relevant
domain context (four-eyes principle, matching the production
`scheme_version` publish workflow itself — see FR-ADMIN-2). CI must be
green: lint (ruff), type-check (mypy), unit + integration tests, contract
tests against `openapi.yaml`, and the module-boundary import-lint check.

## 7. Reporting Issues

Bugs and feature requests: use the templates in `.github/ISSUE_TEMPLATE/`.
Security vulnerabilities: **do not** open a public issue — follow
`SECURITY.md`.

## 8. Code of Conduct

All contributors are expected to follow `CODE_OF_CONDUCT.md`.
