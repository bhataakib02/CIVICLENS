# Alerting

Status: v1.0 draft
Related: metrics.md, incident-response.md (security), product/non-functional-requirements.md (NFR-OBS-3)

## 1. Alert Categories

| Category | Example trigger | Severity |
|---|---|---|
| Availability | Core-flow error rate spike, health check failures | Sev1/Sev2 (incident-response.md) |
| Latency | p95 latency breaching NFR-PERF-* targets sustained over a window | Sev2/Sev3 |
| AI quality | Citation rate drop below threshold, refusal rate anomaly | Sev2/Sev3 |
| Knowledge freshness | `knowledge_sources.last_verified_at` beyond category threshold | Sev3, routed to scheme admins not on-call engineering |
| Security/anomaly | Elevated auth failure rate, one agent account touching an unusual volume of distinct citizen profiles | Sev1/Sev2, routed to security |
| Infrastructure | Queue depth backlog beyond threshold, DB connection saturation | Sev2/Sev3 |

## 2. Routing

Availability/latency/infrastructure alerts page on-call engineering.
AI-quality alerts route to the team owning the `ai/` package. Knowledge-
freshness alerts route to scheme administrators via the admin console
(FR-ADMIN-3) as well as an internal channel — these are a product/content
concern as much as an engineering one. Security/anomaly alerts route
directly per incident-response.md's process.

## 3. Alert Hygiene

Every alert has a documented runbook link (runbooks.md) and an owner —
an alert with no clear next action or owner is either fixed or removed,
not left to accumulate as noise that trains responders to ignore paging.

## 4. Thresholds

Thresholds are set from load-testing.md baselines and NFR targets, not
arbitrary numbers, and are revisited when either the NFR targets or
observed normal-traffic patterns change materially.
