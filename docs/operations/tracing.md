# Tracing

Status: v1.0 draft
Related: observability.md, logging.md, backend/backend-architecture.md §2

## 1. Instrumentation

Distributed tracing (OpenTelemetry or equivalent) instruments: API request
handling, service-layer calls (including cross-module calls per
backend/component-architecture.md §3), database queries, external
provider calls (LLM, OCR, SMS), and async worker job execution — spans
share a `trace_id` propagated from the originating API request through to
any downstream async job it enqueued.

## 2. Why This Matters Specifically Here

Several CivicLens flows span the sync/async boundary (document upload →
async OCR; assistant message → retrieval → generation, itself potentially
multiple provider calls) — without trace propagation across that
boundary, debugging "why did this document take 3 minutes to process" or
"why was this assistant answer slow" would require manually correlating
disjoint logs. Tracing makes the full path (system-architecture.md §3)
inspectable as one connected timeline.

## 3. Sampling

Full sampling in staging; production uses a sampling strategy balancing
cost and diagnostic value, with elevated/full sampling automatically
triggered for any request resulting in an error (5xx) or a flagged/
low-confidence assistant response, so the cases most worth debugging are
the ones least likely to be sampled away.

## 4. Correlation With Logs

Every log line includes the active `trace_id` (logging.md §1), so an
engineer can pivot from a log line straight to the full distributed trace
and back.
