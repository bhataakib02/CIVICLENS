# Backend Architecture

Status: v1.0 draft
Related: architecture/system-architecture.md, architecture/component-architecture.md, module-boundaries.md, service-layer.md, repository-pattern.md

This is the backend-focused companion to architecture/system-architecture.md
— read that first for the system-wide picture. This document covers
backend-internal conventions.

## 1. Directory Layout

```
backend/
├── app/
│   ├── api/v1/          # routers, one file per module, thin HTTP layer
│   ├── core/             # config, security (JWT), logging setup, exceptions
│   ├── db/                # session management, declarative base, mixins
│   ├── modules/
│   │   ├── auth/
│   │   ├── citizens/
│   │   ├── schemes/
│   │   ├── eligibility/
│   │   ├── documents/
│   │   ├── applications/
│   │   ├── assistant/
│   │   ├── notifications/
│   │   └── admin/
│   │       └── (each: models.py, schemas.py, repository.py, service.py)
│   └── main.py            # FastAPI app assembly, router registration
├── migrations/            # Alembic
└── tests/                  # mirrors app/ structure
```

## 2. Request Lifecycle

`main.py` wires: CORS/middleware → auth dependency (validates JWT, injects
current user) → router → service → repository → response schema
serialization → structured logging of the request outcome (with
`request_id`).

## 3. Configuration

`core/config.py` loads environment-specific settings via environment
variables (populated from the secrets store in deployed environments,
`.env` locally) — no environment-specific values are hardcoded in source.

## 4. Dependency Injection

FastAPI's dependency system provides: current authenticated user, a
scoped DB session per request, and role/ownership-check dependencies
reused across routers — keeping routers declarative rather than
imperative about auth.

## 5. Consistency With Other Docs

The module list, layering, and boundary rules here are the same ones
described in architecture/component-architecture.md and
module-boundaries.md — this document exists as the backend-team-facing
entry point; those exist as the architecture-level and rule-level
references respectively. If they ever disagree, that's a documentation
bug to fix immediately (docs/README.md's change rule).
