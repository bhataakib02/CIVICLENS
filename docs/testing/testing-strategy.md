# CivicLens — Testing Strategy

Status: v1.0 draft
Related: unit-testing.md, integration-testing.md, api-testing.md, e2e-testing.md, security-testing.md, load-testing.md, ai-testing.md, NFR-MAINT-3

## 1. Testing Pyramid

```
        ┌────────────┐
        │   E2E (few) │   citizen journeys, real browser, staging env
        ├────────────┤
        │ API/contract │   every endpoint against openapi.yaml
        ├────────────┤
        │ Integration  │   module + real Postgres/Redis, no mocks on DB
        ├────────────┤
        │  Unit (many) │   service logic, rule engine, DSL parser
        └────────────┘
```

Bias toward the base of the pyramid. The eligibility engine and rule DSL
in particular get exhaustive unit + property-based coverage because they
are the component whose correctness citizens' actual benefits depend on.

## 2. Coverage Gates (CI-enforced, NFR-MAINT-3)

- `core` and `eligibility` modules: ≥ 80% line coverage, enforced as a CI
  gate that fails the build below threshold.
- Every API endpoint in `openapi.yaml` has at least one contract test
  asserting the response matches its declared schema — a generated
  checklist against the spec is part of CI, not manually tracked.
- No PR merges without passing unit + integration suites; E2E runs on a
  merge-queue/nightly cadence against staging, not on every PR (too slow),
  but is a release gate.

## 3. Unit Testing

Scope: pure functions and service-layer logic with dependencies mocked at
the repository boundary. Priority areas:
- Rule DSL parser/validator (grammar conformance, rejection of malformed
  rules, field-registry enforcement).
- Eligibility engine `evaluate()` — every operator, every result category
  (`eligible`/`not_eligible`/`likely_eligible`/`insufficient_data`),
  property-based tests asserting the "never eligible when a mandatory rule
  is unknown" invariant.
- Application status state machine — every legal and illegal transition.
- Document extraction confidence thresholding logic.

## 4. Integration Testing

Scope: a module's service + repository layer against a real (ephemeral,
Dockerized) PostgreSQL and Redis — no mocking the database, since ORM
query correctness and migration/schema drift are exactly what this layer
should catch. Cross-module flows (e.g., starting an application triggers
an eligibility re-check and a document-completeness check) are tested here
using real service calls across module boundaries, not through the HTTP
layer.

## 5. API / Contract Testing

Every endpoint tested against `openapi.yaml`: request validation
(malformed input → 422 with expected shape), auth/authorization (missing
token → 401, wrong role/ownership → 403), pagination envelope shape, and
error envelope shape. Contract tests run against a generated client so
schema drift between the spec and the implementation fails CI
automatically rather than being caught by a human reviewer.

## 6. End-to-End Testing

A small, curated set of full citizen journeys run against staging with a
real browser (Playwright): register → build profile → discover a scheme →
view eligibility explanation → upload a document → start and submit an
application → see status update. Kept deliberately small (slow, flaky by
nature) — breadth of coverage belongs to the lower layers.

## 7. AI-Component Testing

Split by component, per ai-testing.md:
- **Eligibility engine**: treated as deterministic software (unit +
  property-based tests, §3) — not evaluated like a model, because it isn't
  one.
- **RAG assistant**: evaluated against a held-out question/answer set with
  scored factual accuracy, citation presence, and correct refusal on
  unsupported questions (ADR-009); regression-tested on every prompt or
  retrieval-pipeline change before it can ship.
- **Document extraction / OCR**: evaluated against a labeled sample of
  representative documents (various quality/lighting/languages) tracking
  field-level extraction accuracy and confidence-threshold calibration.

## 8. Security Testing

SAST and dependency scanning on every merge; DAST and manual penetration
testing before production launch and periodically thereafter (NFR-SEC-4).
Specific test cases derived directly from security/threat-model.md — each
enumerated threat has at least one corresponding automated or manual test.
See security-testing.md.

## 9. Load Testing

Run against staging before major releases and after significant
architectural changes, targeting the thresholds in
non-functional-requirements.md (NFR-PERF-*, NFR-SCALE-*). Scenarios:
sustained bulk-eligibility-check load, spike traffic on scheme search,
sustained assistant usage (cost + latency under concurrency). See
load-testing.md.

## 10. Test Data

Synthetic citizen profiles and a sanitized scheme/rule fixture set are used
throughout — no real citizen PII is ever used in any non-production
environment, including staging E2E and load tests.
