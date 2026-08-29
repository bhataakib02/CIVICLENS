# Metrics

Status: v1.0 draft
Related: observability.md, alerting.md, product/non-functional-requirements.md

## 1. Service-Level Metrics (per NFR targets)

| Metric | Target | NFR |
|---|---|---|
| Scheme search / eligibility p95 latency | ≤ 800ms | NFR-PERF-1 |
| Assistant answer p95 latency | ≤ 6s | NFR-PERF-2 |
| Document processing p95 | ≤ 60s | NFR-PERF-3 |
| Bulk eligibility check p95 | ≤ 3s | NFR-PERF-4 |
| Core flow monthly availability | ≥ 99.5% | NFR-AVAIL-1 |
| Assistant monthly availability | ≥ 99% | NFR-AVAIL-2 |

## 2. Domain Metrics

- Assistant citation rate (% of factual sentences with a valid citation) —
  tracked continuously, not just at the pre-deploy evaluation gate
  (ai/hallucination-controls.md §5).
- Assistant refusal rate and refusal-correctness proxy (manual/periodic
  sampling review).
- Eligibility result distribution (eligible/not_eligible/likely_eligible/
  insufficient_data) — a sudden shift can indicate a rule authoring bug
  even before a citizen complaint surfaces it.
- OCR extraction confidence distribution and re-capture rate.
- Knowledge source staleness distribution (count of sources past their
  verification cadence).
- Application funnel (started → submitted → approved/rejected) per
  scheme, supporting the product success metrics in
  product/product-requirements.md §6.

## 3. Infrastructure Metrics

Standard: CPU/memory per ECS service, RDS connection count and query
latency, Redis memory/eviction rate, Celery queue depth and per-queue
processing time.

## 4. Tooling

Metrics collected via the standard cloud-provider/APM integration for the
ECS/Fargate stack, exported to a dashboarding tool (aws-architecture.md
stack); dashboards are versioned alongside infrastructure code where the
tooling supports it, not maintained as untracked ClickOps artifacts.
