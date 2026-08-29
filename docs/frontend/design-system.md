# Design System

Status: v1.0 draft
Related: accessibility.md, frontend-architecture.md

## 1. Principles

- **Legible over decorative** — target users include low digital-literacy
  citizens; clarity beats visual flourish everywhere in the citizen app.
- **High contrast, large touch targets** — supports both accessibility
  (WCAG 2.1 AA, NFR-ACC-1) and usability on low-end devices/small screens.
- **Consistent status vocabulary** — the same color/icon language for
  "pass/fail/unknown" (eligibility) and "draft/submitted/under review/
  approved/rejected" (applications) is used everywhere those concepts
  appear, never redefined per screen.

## 2. Tokens

A shared token set (colors, spacing, typography scale, elevation) lives in
the component library consumed by both `apps/web` and `apps/admin`, so the
two apps feel like one product family despite serving different
audiences — admin trades some density/complexity budget for efficiency,
but doesn't diverge in core visual language.

## 3. Core Components

Eligibility rule-breakdown display (pass/fail/unknown per rule, with
citation link), document upload + confidence-flagged review card,
application status timeline, scheme card (catalog browsing), assistant
chat bubble with inline citations — these are the components most directly
shaped by this system's specific domain logic and are built once, reused
everywhere they appear.

## 4. Content Guidelines

Plain-language requirement (NFR-ACC-4, class 8 reading level) applies to
all UI copy, not just AI-generated explanations — button labels, error
messages, and form field help text are written and reviewed against the
same standard.

## 5. Iconography & Imagery

Avoid culturally-specific imagery that doesn't translate across India's
regional diversity; icons favor universally-recognizable metaphors
(checkmark, document, clock) over illustration-heavy style, keeping asset
weight low for NFR-ACC-2.
