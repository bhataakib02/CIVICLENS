# Architecture Decision Records

ADRs capture decisions that materially affect architecture, security,
data, AI, or operations, and would otherwise be re-litigated or forgotten.
Each ADR contains context, decision, consequences, and alternatives
considered — see any ADR below for the template in practice.

## Index

| ADR | Decision |
|---|---|
| [ADR-001](ADR-001-modular-monolith.md) | Modular monolith over microservices |
| [ADR-002](ADR-002-postgresql-pgvector.md) | PostgreSQL + pgvector over a separate vector database |
| [ADR-003](ADR-003-deterministic-eligibility.md) | Eligibility determined by a deterministic rule engine, never the LLM |
| [ADR-004](ADR-004-policy-versioning.md) | Immutable scheme versioning, never in-place policy edits |
| [ADR-005](ADR-005-object-storage.md) | Object storage for documents, not database BLOBs |
| [ADR-006](ADR-006-async-processing.md) | Celery workers for async AI/document workloads |
| [ADR-007](ADR-007-hybrid-rag.md) | Hybrid retrieval (lexical + semantic) for the RAG assistant |
| [ADR-008](ADR-008-rule-dsl.md) | Closed-grammar rule DSL, no embedded scripting or NL-at-evaluation-time |
| [ADR-009](ADR-009-ai-evaluation-gates.md) | Mandatory evaluation gate before any RAG/prompt change ships |

## When to Write a New ADR

A new ADR is warranted when a decision: is hard to reverse, affects
multiple modules or teams, involves a real tradeoff (not an obviously
correct choice), or is likely to be questioned again later without a
written record of why it was made. Not warranted for routine
implementation choices already covered by an existing document's
conventions (e.g., naming a new database column doesn't need an ADR;
choosing to encrypt a new PII column type per an existing policy doesn't
either — see security/pii-handling.md).

## Numbering

ADRs are numbered sequentially and never renumbered or reused, even if an
ADR is later superseded — a superseding ADR references the one it
replaces and the old one is marked `Superseded` rather than deleted.
