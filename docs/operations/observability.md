# Observability

Status: v1.0 draft
Related: logging.md, metrics.md, tracing.md, alerting.md, product/non-functional-requirements.md (NFR-OBS-*)

## 1. Three Pillars

- **Logging** (logging.md) — structured, PII-redacted, correlated by
  `request_id`.
- **Metrics** (metrics.md) — latency, error rate, throughput per endpoint/
  job type, plus domain-specific metrics (citation rate, eligibility
  cache hit rate, OCR confidence distribution).
- **Tracing** (tracing.md) — distributed traces across API → service →
  repository → (async) worker, correlated by `request_id`/`trace_id`.

## 2. Domain-Specific Observability (beyond standard web-service telemetry)

Because eligibility and assistant answers carry real consequences,
CivicLens logs enough context to reproduce, not just detect, an incident:

- Every `eligibility_checks` row already persists `rule_breakdown` and the
  exact `scheme_version_id`/`profile_version_no` used (NFR-OBS-2) — this
  *is* an observability record, not just a domain record.
- Every assistant answer logs the retrieved `knowledge_chunks` used, the
  prompt version, and the model version, so a disputed or flagged answer
  can be reproduced exactly.

## 3. Dashboards

Per-module dashboards (API latency/error rate, worker queue depth/
processing time) plus domain dashboards (eligibility check volume by
result category, assistant citation rate over time, knowledge base
staleness distribution) — the latter surfaced to product/ops, not just
engineering, since they reflect product health, not just system health.

## 4. Correlation

Every log line, trace span, and error response shares a `request_id`
(api/error-handling.md §3), letting support staff go from "a citizen
reported X" to the exact server-side execution in one lookup.
