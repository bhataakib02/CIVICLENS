# Accessibility

Status: v1.0 draft
Related: design-system.md, product/non-functional-requirements.md (NFR-ACC-*)

## 1. Standard

WCAG 2.1 AA conformance across all citizen-facing screens (NFR-ACC-1),
verified via automated scanning (axe or equivalent) in CI plus periodic
manual audits, including screen-reader walkthroughs of the core journeys
(profile setup, eligibility check, document upload, application
submission).

## 2. Specific Requirements

- Full keyboard navigability; no interaction reachable only via
  mouse/touch gesture.
- Sufficient color contrast for all text and meaningful UI elements
  (status indicators never rely on color alone — pass/fail/unknown
  eligibility outcomes carry icon + text label, not just a color chip).
- Form fields have associated labels and error messages programmatically
  linked (not just visually adjacent) for screen reader users.
- Focus management on dynamic content (e.g., assistant streaming
  responses, async document status updates) announces changes via ARIA
  live regions rather than silently updating.
- Touch targets meet minimum size guidelines, given the mobile-first,
  low-end-device target audience (overlaps with NFR-ACC-2).

## 3. Language & Reading Level

Plain-language content (class 8 reading level, NFR-ACC-4) is itself an
accessibility measure — cognitive accessibility, not just perceptual/motor
accessibility, given the target audience includes citizens with varying
literacy levels.

## 4. Testing

Accessibility checks are part of testing/e2e-testing.md's core-journey
suite and testing/testing-strategy.md's CI gates — not a pre-launch-only
audit that then lapses.
