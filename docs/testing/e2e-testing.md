# End-to-End Testing

Status: v1.0 draft
Related: testing-strategy.md §6, frontend/accessibility.md §4, infrastructure/ci-cd.md §2

## 1. Scope

A small, deliberately curated set of full citizen journeys, run with
Playwright against a real browser targeting the staging environment
(never production, never local mocks) after every merge to `main`, and as
a release gate before production deploy.

## 2. Covered Journeys

1. Register (OTP) → build profile progressively → discover a scheme.
2. View eligibility explanation for a scheme (verify rule-by-rule
   breakdown renders with citations).
3. Upload a document → review/confirm extracted fields.
4. Start an application → attach a verified document → submit.
5. Receive and view an application status change notification.
6. Ask the assistant a question → verify a citation renders inline with
   the answer.
7. A representative accessibility pass (keyboard-only navigation through
   journey 1–2, screen-reader spot check) — see
   frontend/accessibility.md §4.

## 3. Why Kept Small

E2E tests are the slowest and most failure-prone layer (network, browser,
timing flakiness) — breadth of logical coverage belongs in unit/
integration/contract tests (testing-strategy.md's pyramid). E2E exists to
catch integration issues those layers structurally can't see: real
frontend-backend wiring, real browser rendering, real cross-service
timing (e.g., the WebSocket push actually arriving after an async job
completes).

## 4. Test Data

Runs against dedicated synthetic test accounts on staging, provisioned/
torn down per run — never against any account resembling a real citizen,
consistent with testing-strategy.md §10.

## 5. Flake Management

A flaky E2E test is treated as a bug to fix (usually a missing wait
condition or a genuine race condition worth knowing about), not silenced
via blanket retries — retries mask real timing bugs that matter given
this system's async-heavy architecture (ADR-006).
