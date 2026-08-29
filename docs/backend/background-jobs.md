# Background Jobs

Status: v1.0 draft
Related: system-architecture.md §3.2, ADR-006, infrastructure/docker.md

## 1. Job Types

| Job | Queue | Triggered by | Idempotent? |
|---|---|---|---|
| OCR + extraction | `ocr` | Document upload | Yes — re-running on the same document is safe (overwrites `document_extractions`) |
| Knowledge ingestion (chunk + embed) | `ingestion` | Admin registers/re-triggers a knowledge_source | Yes — re-ingestion replaces prior chunks for that source |
| Notification dispatch | `notifications` | Application status change, scheme match, deadline reminder | Yes, guarded by an idempotency key per notification event |
| Knowledge staleness check | `scheduled` | Periodic (cron-style beat schedule) | N/A (read-only check + alert) |
| Eligibility cache invalidation | `scheduled`/event-driven | scheme_version publish, profile edit | Yes |

## 2. Queue Design

Separate Celery queues per job type (not one shared queue) so worker
autoscaling and prioritization can be tuned independently — e.g., OCR
jobs shouldn't be starved by a large batch knowledge-ingestion run.

## 3. Retry Policy

Exponential backoff, bounded retry count (default 5), then dead-letter for
manual/alerted investigation (operations/runbooks.md) — no job retries
indefinitely or fails silently.

## 4. Observability

Every job emits structured logs and metrics (queue time, processing time,
outcome) per operations/observability.md; job failures beyond a threshold
rate trigger alerting (operations/alerting.md).

## 5. Local Development

`docker compose up` runs a worker container alongside the API and
database, using the same Redis instance as the broker, so the full async
pipeline (e.g., document upload → OCR → extraction) is testable locally
without any cloud dependency.
