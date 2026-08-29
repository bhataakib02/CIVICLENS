# Runbooks

Status: v1.0 draft
Related: alerting.md, incident-response.md, backup-restore.md, backend/background-jobs.md §3

This document indexes operational runbooks; each links to a detailed
procedure (kept alongside the alert that triggers it, versioned in
source control, not tribal knowledge).

## 1. Availability

- **API error rate spike** — check recent deploys first (rollback
  candidate per infrastructure/ci-cd.md §3), then dependency health
  (database, Redis), then provider status (LLM/OCR/SMS).
- **Health check failures** — verify database connectivity from the
  affected task; check for connection pool exhaustion; check RDS metrics.

## 2. Async Job Failures

- **Job stuck / queue backlog growing** — check worker fleet health/
  scaling, check for a poison-pill job repeatedly failing and blocking
  its queue, check third-party provider status.
- **Dead-letter queue accumulating** — inspect failure reasons; common
  causes: provider outage (transient, safe to bulk-retry once resolved),
  malformed input (needs code fix, not a retry), provider rate limiting
  (needs backoff tuning).

## 3. Knowledge Base

- **Knowledge source ingestion failed** — check fetch/parse error in job
  logs; common causes: source URL moved/changed format, document behind
  an access wall not anticipated at registration time.
- **Staleness alert fired** — routed to the relevant scheme administrator
  per alerting.md §2; procedure is source-verification.md §4.

## 4. AI Quality

- **Citation rate drop alert** — check for a recent prompt/retrieval/
  model change (should have passed the evaluation gate, ADR-009 —
  investigate whether the gate itself missed the regression, which is
  itself an action item); check for a shift in the mix of incoming
  question types.

## 5. Security

- **Anomalous access pattern flagged** — follow incident-response.md's
  triage process; do not unilaterally revoke access without following
  the documented escalation for Sev1/Sev2.

## 6. Restore

- **Database/document restore** — see backup-restore.md §4.
