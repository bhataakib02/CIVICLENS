# Scope

Status: v1.0 draft
Related: product-requirements.md §3, roadmap.md

## In Scope (v1.0)

- Citizen auth (phone+OTP), profile, and address management.
- Scheme catalog: browse, search, detail view with citations.
- Deterministic eligibility engine, single and bulk check.
- Document upload, OCR/extraction, citizen confirmation, reuse across
  applications.
- Application lifecycle: create, complete, submit (validated), track
  status, withdraw, export as PDF for manual submission.
- Retrieval-grounded assistant (RAG) with mandatory citations, restricted
  to the ingested, vetted knowledge base.
- Notifications (SMS + in-app) for scheme matches, status changes,
  document re-verification, deadlines.
- Admin console: scheme/version/rule authoring with four-eyes review,
  knowledge base ingestion management, audit log viewer, case notes.
- Hindi + English localization.
- India-only.

## Explicitly Out of Scope (v1.0)

- **Direct government portal integration/automation** — CivicLens
  produces a submission-ready package; the citizen (or agent) submits it
  themselves through official channels. No scraping or automated
  submission into third-party government IT systems.
- **Payments/disbursement handling** — CivicLens does not touch benefit
  disbursement.
- **Legal advice or guaranteed eligibility outcomes** — all determinations
  are advisory, clearly labeled as such.
- **Multi-country support.**
- **Full offline-first mode** — PWA offline shell only (frontend/pwa.md),
  not full offline transaction capability.
- **Voice interface.**
- **Native mobile apps** — PWA only at launch.

## Deferred / Candidate for v1.1+ (see roadmap.md)

- Voice interface for lower-literacy accessibility.
- Direct government portal integration where official APIs exist.
- Additional regional languages beyond Hindi/English.
- Native app wrappers if PWA adoption/performance data warrants it.

## Scope Change Process

Any addition to in-scope functionality after this document is frozen for
a release goes through a documented scope-change review (impact on
timeline, security/privacy surface, and the acceptance-criteria.md launch
gate) — not an informal "let's just add this" decision mid-sprint.
