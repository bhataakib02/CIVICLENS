# Audit Logging

Status: v1.0 draft
Related: database/data-dictionary.md (audit_logs), threat-model.md #13, security-architecture.md §4

## 1. What Gets Logged

Every mutation to a sensitive entity, and every access to sensitive
citizen data by a non-owner (staff/agent), writes an `audit_logs` row:
- scheme_version create/publish, eligibility_rule create/edit
- application status transitions
- role changes, consent grants/revocations
- admin/agent access to a citizen's documents or profile
- knowledge_source registration and ingestion status changes

## 2. Log Shape

`actor_user_id` (null = system/scheduled job), `action` (dotted string,
e.g. `scheme_version.publish`), `entity_type`, `entity_id`, `diff` (JSON
before/after where applicable), `created_at`. See data-dictionary.md.

## 3. Immutability

`audit_logs` is insert-only; the application's database role has
`REVOKE UPDATE, DELETE` on this table (database-design.md §2). No code
path updates or deletes an audit log row, including admin tooling.

## 4. Access

Audit logs are readable via `/admin/audit-logs` by `admin` role only,
filterable by actor, action, and date range (FR-ADMIN-4). Access to the
audit log endpoint is itself... not separately audit-logged (avoiding
infinite regress), but is rate-limited and access-logged at the
infrastructure level.

## 5. Use in Incident Response

Audit logs are the primary forensic source for incident-response.md
investigations and for anomaly detection alerting (e.g., one agent account
touching an unusually large number of distinct citizens — threat-model.md
#13).
