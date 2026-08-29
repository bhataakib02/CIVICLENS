# Load Testing

Status: v1.0 draft
Related: testing-strategy.md §9, product/non-functional-requirements.md (NFR-PERF-*, NFR-SCALE-*), architecture/scalability.md

## 1. When

Before major releases, after significant architectural changes, and
before any anticipated traffic surge (e.g., a scheme application deadline
expected to drive a spike) — run against the staging environment, which
mirrors production topology at reduced scale (infrastructure/environments.md
§2).

## 2. Scenarios

| Scenario | Validates |
|---|---|
| Sustained bulk-eligibility-check load | NFR-PERF-4 target holds under concurrent multi-citizen bulk checks against the full ~500-scheme catalog |
| Scheme search/browse spike | NFR-PERF-1 target holds under a sudden traffic spike (e.g., a scheme announced in the news) |
| Sustained assistant usage | NFR-PERF-2 latency and provider rate-limit headroom under concurrent chat sessions |
| Document upload burst | Worker autoscaling (NFR-SCALE-2) keeps processing latency within NFR-PERF-3 under a burst of uploads |
| Knowledge base at target scale | pgvector retrieval latency (NFR-SCALE-3) at the 50,000-chunk target, and beyond, to find the actual breaking point, not just confirm the target |

## 3. Method

Synthetic load generation (e.g., k6/Locust) driving the same
`openapi.yaml`-generated client contracts used elsewhere, against
synthetic test accounts and fixture data — never real citizen data
(testing-strategy.md §10).

## 4. Outcome

Results feed back into architecture/scalability.md's "known future
bottlenecks" list and into alerting.md's threshold-setting — load testing
isn't just a pass/fail gate, it's the primary source of ground truth for
capacity planning.
