# Knowledge Document Versioning

Status: v1.0 draft
Related: source-verification.md, database/database-design.md §2, ADR-004

## 1. Principle

Mirrors the immutable-versioning principle applied to `scheme_versions`
(ADR-004): when a government source's content genuinely changes (not just
a re-verification confirming no change), a new ingestion produces a new
`knowledge_source` record (or a new version thereof) rather than
overwriting the old one in place.

## 2. Mechanics

A source content change detected during source-verification.md's process
triggers: (1) the old `knowledge_source`'s chunks remain queryable for
historical citation purposes (e.g., explaining a past `eligibility_check`
computed against the old rules), (2) a new `knowledge_source` (or version)
is ingested and reviewed, (3) any `scheme_version` referencing the old
source is superseded by a new `scheme_version` referencing the new source
(ADR-004), keeping the provenance chain consistent end to end.

## 3. Why Not In-Place Update

In-place update of `knowledge_chunks` content would silently invalidate
past `eligibility_checks`' citations (a citizen could look up the cited
section months later and find different text than what was actually
evaluated against their profile) — the same explainability argument as
ADR-004, applied one layer down the provenance chain.

## 4. Retention

Superseded knowledge sources are retained indefinitely (not purged),
consistent with retention-policy.md's treatment of `scheme_versions` and
`knowledge_sources` as a historical policy record.
