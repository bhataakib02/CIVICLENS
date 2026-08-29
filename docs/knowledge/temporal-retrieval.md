# Temporal Retrieval

Status: v1.0 draft
Related: ai/retrieval-pipeline.md §4, document-versioning.md, ADR-004

## 1. Default Behavior

By default, both the eligibility engine and the RAG assistant operate
"as of now" — retrieval is scoped to `knowledge_chunks` belonging to
currently-effective `scheme_versions` (`effective_from` ≤ today ≤
`effective_to` or `effective_to` is null), and eligibility evaluation uses
the currently-published rule set (ai/retrieval-pipeline.md §4).

## 2. Historical Queries

Two scenarios require retrieval scoped to a *past* point in time rather
than "now":
- **Explaining a past eligibility_check**: reconstructing exactly what a
  determination was based on uses the specific `scheme_version_id` stored
  on that `eligibility_checks` row (database/database-design.md §2) —
  this bypasses "current" retrieval entirely and goes straight to the
  exact version referenced.
- **A citizen or auditor asking "what were the rules as of [past date]"**:
  the assistant can be asked an explicit as-of question; retrieval is
  scoped to the `scheme_version` whose effective range covered that date,
  not the current one.

## 3. Why This Matters

Without explicit temporal scoping, a citizen asking about a determination
made months ago could be shown current (possibly different) rules and
wrongly conclude the original determination was wrong — temporal
retrieval is what keeps the system's explainability promise intact across
policy changes over time, not just at a single point in time.

## 4. Implementation Note

Temporal scoping is a query filter parameter passed through the retrieval
pipeline (ai/retrieval-pipeline.md), not a separate retrieval system —
one pipeline, an optional `as_of_date` parameter defaulting to "now."
