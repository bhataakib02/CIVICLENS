# Data Retention Policy

Status: v1.0 draft
Related: security/pii-handling.md §4, security/data-protection.md, DPDP Act obligations

## 1. Retention by Entity

| Entity | Retention | Notes |
|---|---|---|
| `citizen_profiles`, `addresses` | Until account deletion request, then anonymized | See pii-handling.md §4 |
| `documents` (files) | Until account deletion request, then deleted from object storage | Independent of application status |
| `applications`, `application_status_history` | Retained per statutory record-keeping requirements for government application records (jurisdiction/scheme-dependent, minimum baseline TBD with legal review) | Not deleted on account deletion — anonymized reference retained instead |
| `eligibility_checks` | Retained for audit/explainability purposes for a defined window (proposed: 3 years), then archived/purged | Supports appeals and dispute investigation |
| `audit_logs` | Retained for a compliance-driven minimum period (proposed: 7 years, pending legal confirmation), immutable throughout | Insert-only, never purged early |
| `knowledge_sources`, `knowledge_chunks`, `scheme_versions` | Retained indefinitely (historical policy record) | Superseded versions kept, not deleted (ADR-004) |
| `notifications` | Rolling window (proposed: 1 year), then purged | Low sensitivity, mostly delivery-status records |

Numeric windows marked "proposed" require legal/compliance sign-off before
being treated as final policy — flagged explicitly rather than presented
as settled.

## 2. Deletion Mechanics

Account deletion (pii-handling.md §4) anonymizes PII-bearing rows rather
than hard-deleting rows that other retained records (applications, audit
logs) reference — preserving referential integrity for records under
statutory retention while removing the citizen's identifiable data from
them.

## 3. Backups

Retention policy applies to live data; encrypted backups
(security/data-protection.md §5) age out on their own backup-lifecycle
schedule, documented separately in operations/backup-restore.md — a
deletion request is reflected in future backups going forward, consistent
with standard DPDP-compliant practice, and is not required to
retroactively scrub already-existing backup snapshots within their normal
retention window.
