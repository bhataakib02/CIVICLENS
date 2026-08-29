# CI/CD

Status: v1.0 draft
Related: environments.md, terraform.md, testing/testing-strategy.md, backend/module-boundaries.md

## 1. Pipeline Stages (per PR)

```
PR opened
   │
   ▼
Lint (ruff) + type-check (mypy) + module-boundary import-lint
   │
   ▼
Unit tests + integration tests (ephemeral Postgres/Redis)
   │
   ▼
Contract tests against openapi.yaml
   │
   ▼
Frontend: build + generate API client from openapi.yaml (fails on drift)
   │
   ▼
Security: SAST + dependency scanning (testing/security-testing.md)
   │
   ▼
AI pipeline: evaluation gate run if ai/ package changed (ADR-009)
   │
   ▼
All green → mergeable
```

Any stage failure blocks merge; there is no override path that skips the
module-boundary or evaluation gates for a "just this once" change.

## 2. Post-Merge

```
Merge to main
   │
   ▼
Build container images, tag with commit SHA
   │
   ▼
terraform plan + apply (staging) — automatic
   │
   ▼
E2E suite runs against staging (testing/e2e-testing.md)
   │
   ▼
Manual approval gate
   │
   ▼
terraform plan + apply (production) — rolling deploy
   │
   ▼
Post-deploy smoke tests (/health, /health/ready, a few critical-path checks)
```

## 3. Rollback

A failed post-deploy smoke test automatically halts the rollout and
triggers rollback to the previous task definition revision (ECS supports
this natively); database migrations follow the backward-compatible
two-step pattern (database/migration-strategy.md §3) specifically so a
code rollback never leaves the app pointed at an incompatible schema.

## 4. Secrets in CI

CI-scoped credentials (deploy roles, not application secrets) are stored
in the CI platform's encrypted secrets store, scoped per-environment, and
never echoed to build logs (security/secrets-management.md §5).
