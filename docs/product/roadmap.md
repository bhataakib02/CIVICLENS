# Roadmap

Status: v1.0 draft — directional, not a committed schedule
Related: scope.md, product-requirements.md

## v1.0 (Launch)

Full scope per scope.md: citizen discovery/eligibility/documents/
applications, admin authoring, RAG assistant, Hindi + English, India-wide
central schemes plus launch-priority state schemes (pending data-sourcing
agreements — product-requirements.md §9).

## v1.1 (Candidate)

- Broader state-scheme coverage as data-sourcing agreements expand.
- Additional regional languages beyond Hindi/English, exercising the
  i18n framework's designed extensibility (NFR-ACC-3).
- Voice interface for citizens with lower literacy or limited text-input
  comfort, particularly relevant given the target demographic
  (product-requirements.md's persona work).
- Deeper agent/CSC-operator tooling (bulk operations, dashboards for
  agents serving many citizens).
- Deadline-aware proactive notifications (e.g., "this scheme's
  application window closes in 5 days and you appear eligible").

## v1.2+ (Directional, Not Yet Scoped in Detail)

- Direct government portal integration where official submission APIs
  become available, revisiting the v1.0 out-of-scope decision on a
  scheme-by-scheme basis as integration opportunities are validated.
- Native app wrappers if PWA metrics indicate a meaningful gap.
- Expanded document types and richer document-intelligence coverage.

## Not Currently Planned

- Payment/disbursement handling — a substantial scope and compliance
  expansion (handling money, not just eligibility/paperwork), would need
  its own dedicated product and security review before being seriously
  considered, not assumed as an eventual roadmap item by default.

## Prioritization Principle

Each roadmap item is evaluated primarily against product-requirements.md
§6's success metrics (discovery rate, comprehension, completion rate,
knowledge freshness) — features that don't clearly move one of those
metrics are deprioritized regardless of how technically interesting they
are.
