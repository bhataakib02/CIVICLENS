# ADR-004: Immutable Scheme Versioning, Never In-Place Policy Edits

Status: Accepted
Date: 2026-08-29
Related: database/database-design.md, database/erd.md, knowledge/document-versioning.md, threat-model.md #8

## Context

Government scheme rules and benefits change over time (budget cycles,
amendments). If `schemes`/eligibility rules were edited in place, past
`eligibility_checks` and `applications` would become inexplicable — a
citizen told "eligible" six months ago might, on re-inspection, appear to
fail current rules, with no record of what actually applied at the time.

## Decision

`scheme_versions` are immutable once published, each with an
`effective_from` / `effective_to` date range. Any policy change creates a
new `scheme_version`, never an update to an existing one.
`eligibility_checks` and `applications` reference the specific
`scheme_version_id` (and citizen `profile_version_no`) they were computed
against.

## Consequences

- Positive: every historical determination remains fully explainable, even
  after the scheme or the citizen's profile changes.
- Positive: enables scheme admins to schedule a future-dated version
  (effective_from in the future) and preview its impact via simulation
  (FR-ELIGIBILITY-5) before it goes live.
- Negative: the schema is larger and queries must be version-aware (always
  join through the correct `scheme_version_id`, not just `scheme_id`) —
  mitigated by keeping this join pattern centralized in the `schemes` and
  `eligibility` service layers rather than repeated ad hoc across the
  codebase.

## Alternatives Considered

- **In-place mutation with an audit_logs diff trail**: rejected — audit
  logs are good for "what changed and when" but poor for "what set of
  rules was actually live and queryable at time T," which the eligibility
  engine and citizen-facing history need to query directly and
  efficiently.
