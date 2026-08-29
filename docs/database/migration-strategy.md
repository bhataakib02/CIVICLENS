# Migration Strategy

Status: v1.0 draft
Related: database-design.md §6, backend/backend-architecture.md, infrastructure/ci-cd.md

## 1. Tooling

Alembic, one migration file per logical schema change. `--autogenerate` is
used to draft migrations but every generated migration is manually
reviewed before commit — autogenerate output is a starting point, not a
merge-ready artifact (it commonly misses data backfills, index tuning
choices, or check constraints that need explicit handling).

## 2. Backward-Compatible Changes (single-step)

Additive changes — new nullable column, new table, new index — ship in a
single migration and deploy alongside application code changes using
them, since they don't break code that hasn't been updated yet.

## 3. Backward-Incompatible Changes (two-step)

Column drops, type narrowing, `NOT NULL` additions on existing columns,
and renames follow a deprecate → backfill/verify → remove pattern across
at least two deploys:
1. **Deprecate**: add the new shape alongside the old (e.g., new column,
   dual-written by application code); stop reading the old shape in new
   code paths.
2. **Backfill**: migrate existing data to the new shape; verify
   completeness.
3. **Remove**: a later migration drops the old column/constraint, once
   confidence is high no code path still depends on it.

This avoids a deploy-time window where old application code (still
running during a rolling deploy, per deployment-architecture.md §5) hits a
schema it doesn't expect.

## 4. Data Migrations

Large data backfills (e.g., re-embedding `knowledge_chunks` after a model
change, ADR-002) run as a separate, monitored batch job — never inline in
an Alembic migration that would hold a long-running transaction/lock
during a deploy.

## 5. Testing

Every migration is tested against a copy of a representative dataset in
CI (apply forward from the previous head, verify application startup and
a smoke-test suite pass) before merge — schema drift between what's in
`erd.md`/`data-dictionary.md` and the actual migrated schema is treated as
a bug (database-design.md §2).
