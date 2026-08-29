# Docker (Local Development)

Status: v1.0 draft
Related: infrastructure-overview.md, CONTRIBUTING.md §1

## 1. Compose Services

`docker-compose.yml` at the repo root defines:
- `postgres` — PostgreSQL with the `pgvector` extension pre-installed,
  matching the production RDS configuration as closely as practical.
- `redis` — Celery broker + cache.
- `backend` — FastAPI app, hot-reload enabled for development.
- `worker` — Celery worker, same image as `backend`, different entrypoint.
- `web` (optional profile) — `apps/web` dev server.
- `admin` (optional profile) — `apps/admin` dev server.

## 2. Local-vs-Production Parity

Local development uses the same PostgreSQL major version and `pgvector`
extension version as production, and the same Alembic migration history —
"works on my machine" schema drift is treated as a bug in the local
environment definition, not accepted as normal.

Managed AWS services without a practical local equivalent (S3, Secrets
Manager, KMS) are substituted locally with lightweight compatible
alternatives (e.g., a local S3-compatible service) so the full pipeline —
including document upload → OCR → extraction — is exercisable offline
during development.

## 3. Startup Verification

Per the CivicLens Backend v0.1 milestone
(architecture/system-architecture.md), `docker compose up` should result
in: PostgreSQL starts → Alembic migration runs → all tables created →
FastAPI starts → `GET /health` and `/health/ready` return 200 with a real
database connection.

## 4. Image Build

Production images are built from the same Dockerfiles used locally (no
separate "prod-only" Dockerfile drift), differing only in build args/
target stage (e.g., a `production` multi-stage target that excludes dev
dependencies and hot-reload tooling).
