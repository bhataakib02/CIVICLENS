# CivicLens — Database Design

Status: v1.0 draft
Related: erd.md, data-dictionary.md, ADR-002, ADR-004

## 1. Engine & Extensions

PostgreSQL 15+, with:
- `pgvector` — embedding storage/search for `knowledge_chunks` (ADR-002).
- `pg_trgm` — trigram indexes for fuzzy scheme name / full-text search.
- `uuid-ossp` (or app-generated UUIDv7) — primary keys.

## 2. Design Principles

1. **UUID primary keys everywhere.** Avoids leaking sequential IDs, and
   simplifies future read-replica / partition strategies.
2. **Soft versioning, not soft deletion, for policy data.** `schemes` never
   loses history: a `scheme_version` is immutable once published, with an
   `effective_from` / `effective_to` range. Superseding a version creates a
   new row; nothing is destructively updated (ADR-004).
3. **Every citizen-affecting determination is snapshot-referenced.** An
   `eligibility_checks` row stores the exact `profile_version_id` and
   `scheme_version_id` it was computed against, so results remain
   explainable even after the citizen or the scheme changes later.
4. **PII is column-scoped, not table-scoped.** Tables holding PII
   (citizen_profiles, addresses, documents) are flagged in the data
   dictionary and subject to the encryption/retention rules in
   `security/pii-handling.md`; this keeps the schema itself the source of
   truth for what needs special handling, rather than tribal knowledge.
5. **Append-only audit trail.** `audit_logs` and
   `application_status_history` are insert-only; no updates or deletes,
   enforced via a `REVOKE UPDATE, DELETE` on the application's DB role for
   those tables.
6. **Foreign keys enforce integrity; cascades are explicit and deliberate.**
   Deleting a citizen profile does not cascade-delete `applications` or
   `audit_logs` — those persist with an anonymization flag instead, to
   satisfy both "right to erasure" and statutory application-record
   retention.

## 3. Schema Groups

### 3.1 Identity & Citizen Data
`users` → `citizen_profiles` → `addresses`, plus `consents`.
See erd.md for the full relationship diagram.

### 3.2 Government Knowledge (scheme catalog + rules)
`schemes` → `scheme_versions` → `eligibility_rules`,
`document_requirements`; `knowledge_sources` → `knowledge_chunks`.

### 3.3 Documents
`documents` → `document_extractions`.

### 3.4 Eligibility & Applications
`eligibility_checks`, `applications` → `application_status_history`.

### 3.5 Cross-cutting
`audit_logs`, `notifications`, `case_notes`.

## 4. Key Design Decisions

- **scheme_versions is the unit of truth, not schemes.** All eligibility
  rules and document requirements FK to a `scheme_version_id`, never
  directly to `scheme_id`. `schemes` is just the stable identity/grouping
  row (name history, category, department).
- **eligibility_rules use a structured DSL stored as JSONB**, not free text
  and not application code, so the same rule can be evaluated by the engine
  and rendered in the admin editor and citizen-facing explanation (see
  ai/rule-dsl.md).
- **knowledge_chunks store both the embedding and the source span** (source
  document id, character/page offsets) so every RAG citation can be traced
  back to an exact passage, not just "this document somewhere."
- **profile_version is implemented via a `citizen_profile_versions` history
  table** written on every edit to `citizen_profiles`, rather than a full
  event-sourced model — simpler to query, sufficient for the explainability
  requirement (FR-PROFILE-5).

## 5. Indexing Strategy (summary — see indexing-strategy.md for full list)

- B-tree on all foreign keys.
- Composite index on `eligibility_checks (citizen_id, scheme_version_id)`
  for cache lookups.
- IVFFlat (or HNSW, pgvector ≥0.7) index on `knowledge_chunks.embedding`.
- GIN + pg_trgm on `schemes.name`, `schemes.description` for search.
- Partial index on `applications (status)` excluding terminal statuses, for
  fast "active applications" queries.

## 6. Migration Strategy (summary — see migration-strategy.md for full policy)

Alembic, one migration per logical change, autogenerate + manual review
required (no blind `--autogenerate` merges). Destructive migrations
(column drops, type narrowing) require a two-step deploy (deprecate →
backfill/verify → remove) documented in the migration's docstring.
