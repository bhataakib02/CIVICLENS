# ADR-001: Modular Monolith over Microservices

Status: Accepted
Date: 2026-08-29
Related: architecture/system-architecture.md, backend/module-boundaries.md, NFR-SCALE-1, NFR-MAINT-1

## Context

CivicLens's backend covers eight distinct domains (auth, citizens, schemes,
eligibility, documents, applications, notifications, admin). A microservice
split along these lines is architecturally tempting but the team is small
at launch, expected traffic is moderate, and most flows (e.g. starting an
application) touch four or five of these domains in a single logical
transaction.

## Decision

Build a single deployable FastAPI application ("modular monolith") with
strictly enforced internal module boundaries (service-layer-only
cross-module calls, no cross-module ORM access — see
backend/module-boundaries.md), horizontally scaled behind a load balancer.
Celery workers handle async workloads (OCR, embeddings, notifications)
as a separate deployable, scaled independently.

## Consequences

- Positive: one deployment pipeline, one database to keep consistent for
  cross-domain transactions (e.g., application submission touching
  eligibility + documents + applications atomically), lower operational
  overhead for a small team, faster iteration.
- Positive: module boundaries mean a future extraction (most likely OCR or
  the RAG pipeline, which have divergent load/scaling profiles) remains
  possible without a rewrite.
- Negative: a bug in one module can in principle affect the availability of
  the whole API tier (mitigated by the async split for the riskiest/most
  variable-latency workloads — see system-architecture.md §3.2).
- Negative: requires discipline (enforced via CI import-linting) to prevent
  boundaries from eroding as the team grows.

## Alternatives Considered

- **Microservices from day one**: rejected — deployment/operational
  overhead outweighs engineering value at this scale and team size (see
  original design conversation). Revisit if a specific module's load
  profile diverges sharply and the team has grown enough to own separate
  services.
- **Serverless functions per endpoint**: rejected — poor fit for the
  eligibility engine's need for in-process rule-set caching and for
  transactional cross-module writes.
