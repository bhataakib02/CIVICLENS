# Indexing Strategy

Status: v1.0 draft
Related: database-design.md §5, erd.md, data-dictionary.md

## 1. Standard Indexes

- B-tree on every foreign key column (SQLAlchemy/Alembic default for FK
  columns, verified explicitly rather than assumed).
- Unique indexes on `users.phone_number`, `users.email`.
- B-tree on `applications.status`, `documents.status`,
  `knowledge_sources.ingestion_status` for common filter queries.

## 2. Composite Indexes

- `eligibility_checks (citizen_profile_id, scheme_version_id)` — primary
  cache-lookup pattern (ai/eligibility-engine.md §4).
- `eligibility_rules (scheme_version_id, group_id)` — rule-set compilation
  query pattern.
- `application_status_history (application_id, created_at)` — status
  timeline retrieval, naturally time-ordered.

## 3. Search Indexes

- GIN + `pg_trgm` on `schemes.canonical_name`, and a `tsvector` GIN index
  on `scheme_versions.benefits_summary` for full-text search
  (FR-SCHEME-3).
- IVFFlat (or HNSW on pgvector ≥0.7) on `knowledge_chunks.embedding`,
  tuned (`lists`/`probes` or `m`/`ef_construction`) against the target
  scale in NFR-SCALE-3, re-tuned as the knowledge base grows.

## 4. Partial Indexes

- `applications (citizen_profile_id) WHERE status NOT IN ('approved',
  'rejected', 'withdrawn')` — speeds the common "active applications"
  query without indexing the (eventually much larger) terminal-status
  rows.
- `documents (citizen_profile_id) WHERE status = 'verified'` — speeds
  "reusable verified documents" lookups (FR-DOCS-5).

## 5. Review Cadence

Index effectiveness is reviewed using `pg_stat_statements` and query plan
analysis as part of load-testing.md exercises before major releases, not
set once and forgotten — a schema that grows past assumptions (e.g.,
`knowledge_chunks` well beyond the NFR-SCALE-3 target) needs its indexing
strategy revisited, not just its hardware scaled up.
