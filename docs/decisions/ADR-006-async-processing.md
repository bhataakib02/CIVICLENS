# ADR-006: Celery Workers for Async AI/Document Workloads

Status: Accepted
Date: 2026-08-29
Related: architecture/system-architecture.md, backend/background-jobs.md, NFR-AVAIL-3, NFR-PERF-3

## Context

OCR extraction, embedding generation, RAG generation, and notification
delivery all involve third-party calls with variable and sometimes long
latency, and are subject to third-party outages/rate limits. Putting these
on the synchronous request path would make the API's availability and
latency hostage to external providers.

## Decision

Use Celery with Redis as the broker for all such workloads. The API
enqueues a job and returns immediately (job reference or 202 Accepted);
workers process independently and the client polls or receives a
push update (websocket/SSE) on completion.

## Consequences

- Positive: API tier availability and latency are decoupled from
  third-party provider health (NFR-AVAIL-3) — an OCR provider outage
  degrades document processing, not login or scheme browsing.
- Positive: workers scale independently of the API tier based on queue
  depth, appropriate given bursty upload/ingestion patterns.
- Positive: built-in retry/backoff semantics for flaky third-party calls.
- Negative: introduces eventual consistency for these flows — the client
  must handle a "processing" state, not just synchronous success/failure.
- Negative: an additional operational component (broker, worker fleet,
  dead-letter handling) to monitor.

## Alternatives Considered

- **Synchronous calls with generous timeouts**: rejected — ties API tier
  availability directly to third-party provider health and blocks request
  threads/connections during slow OCR or LLM calls.
- **Serverless async functions (e.g., Lambda) instead of Celery**:
  reasonable alternative, not chosen for v1.0 to keep the operational model
  consistent with the rest of the modular monolith (same deploy tooling,
  same observability stack); may be revisited per-workload if a specific
  job type's scaling profile warrants it.
