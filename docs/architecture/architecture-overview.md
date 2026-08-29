# Architecture Overview

Status: v1.0 draft
Related: system-architecture.md, component-architecture.md

This is a short index/entry point; system-architecture.md is the primary
authoritative document.

## Read Order

1. **system-architecture.md** — overall style (modular monolith), request
   paths, data stores, key principles.
2. **component-architecture.md** — module map, layering, cross-module
   interaction examples.
3. **data-flow.md** — how data moves through the major citizen journeys.
4. **deployment-architecture.md** — how the above maps to actual AWS
   infrastructure.
5. **scalability.md**, **reliability.md**, **disaster-recovery.md** —
   cross-cutting quality attributes layered on top of the base design.

## One-Sentence Summary

CivicLens is a modular-monolith FastAPI backend (PostgreSQL + pgvector,
Redis, Celery workers) serving a citizen PWA and an admin console, with
eligibility decided deterministically and AI used only for language tasks
(retrieval-grounded Q&A, document/text extraction) — see ADR-001 and
ADR-003 for the two decisions that shape everything else.
