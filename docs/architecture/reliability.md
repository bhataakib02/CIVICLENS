# Reliability

Status: v1.0 draft
Related: system-architecture.md, NFR-AVAIL-*, operations/observability.md

## 1. Failure Domains

The architecture deliberately isolates failure domains so a single
provider or component outage has bounded blast radius:

| Failure | Blast radius | Why |
|---|---|---|
| LLM provider outage | Assistant subsystem only | Eligibility engine has no LLM dependency (ADR-003, NFR-AVAIL-3) |
| OCR provider outage | Document processing delayed, queued for retry | Async worker tier, not on the sync request path (ADR-006) |
| SMS gateway outage | Notification delivery delayed | Async, queued for retry; in-app notifications unaffected |
| Single AZ outage | No customer-visible impact | Multi-AZ RDS, multi-AZ ECS task placement |
| Redis outage | Degraded (cache misses, Celery backlog), not down | Eligibility results recomputable; workers resume on Redis recovery |

## 2. Retry & Backoff

Async jobs (OCR, embedding generation, notification delivery) use
exponential backoff with a bounded retry count, after which a job moves to
a dead-letter queue for manual/alerted investigation rather than retrying
forever or silently dropping (operations/runbooks.md).

## 3. Graceful Degradation

Per NFR-AVAIL-2, if the assistant subsystem is unavailable, scheme
browsing and deterministic eligibility checking continue to function —
the frontend surfaces a clear "assistant temporarily unavailable" state
rather than a full-page failure.

## 4. Health Checks

`/health` (liveness) and `/health/ready` (readiness, verifies a real
database connection) back ECS task health checks and ALB target group
health checks, so unhealthy instances are automatically cycled out of
rotation.
