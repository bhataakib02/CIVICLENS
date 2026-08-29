# Logging

Status: v1.0 draft
Related: observability.md, security/pii-handling.md §2, tracing.md

## 1. Format

Structured JSON logs (not free-text) across API and worker tiers, with a
consistent field set: `timestamp`, `level`, `request_id`/`trace_id`,
`module`, `message`, plus context-specific fields.

## 2. PII Redaction

A redaction layer strips or hashes fields matching the PII column list in
database/data-dictionary.md before any log line is emitted — this runs at
the logging library level (a formatter/processor), not as an
ad hoc discipline left to individual log call sites, so a developer
forgetting to redact manually doesn't leak PII (NFR-PRIV-2).

## 3. Log Levels

- `ERROR` — unhandled exceptions, failed jobs after retry exhaustion,
  security-relevant denials.
- `WARN` — degraded conditions (low OCR confidence, retrieval below
  citation threshold, retry attempts).
- `INFO` — request lifecycle, job lifecycle, state transitions
  (application status changes, scheme_version publishes).
- `DEBUG` — local development only, never enabled in staging/production
  by default (both cost and PII-adjacent risk reasons).

## 4. Retention

Logs retained per a defined window (proposed: 90 days hot, longer-term
archive for compliance-relevant categories) — shorter than
`audit_logs`' database retention, since logs are an operational/debugging
tool while `audit_logs` is the compliance-grade record of sensitive
actions (security/audit-logging.md).

## 5. Access

Log access is restricted to engineering/on-call roles, itself access-
logged at the infrastructure level, consistent with the least-privilege
posture in security/security-architecture.md.
