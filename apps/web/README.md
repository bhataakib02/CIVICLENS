# `apps/web` — Citizen PWA

The citizen-facing Progressive Web App: onboarding/profile, scheme
discovery, eligibility explanation, document upload, application flow,
assistant chat, notifications.

## Before Implementing

Read `docs/architecture/component-architecture.md` §4,
`docs/frontend/frontend-architecture.md`, `docs/frontend/design-system.md`,
`docs/frontend/pwa.md`, and `docs/frontend/accessibility.md` — this app has
specific low-end-device, low-bandwidth, and WCAG 2.1 AA requirements
(NFR-ACC-*) that shape nearly every implementation decision here.

## Key Constraints

- Must work on 2GB-RAM-class Android devices on 2G/3G-equivalent networks
  — bundle size is budgeted and tracked in CI.
- Hindi + English at launch, i18n framework extensible without a
  redeploy (`docs/frontend/internationalization.md`).
- All server communication via the generated OpenAPI client
  (`docs/api/api-overview.md` §6) — never hand-written fetch calls.
- No `localStorage`/`sessionStorage` reliance beyond what the app's own
  IndexedDB-backed persistence layer provides for offline draft state.

## Rules

- Preserve module boundaries — feature modules consume the generated API
  client and shared component library, not each other's internals.
- Add tests with behavior changes; accessibility checks are part of CI,
  not a pre-launch-only audit.
- Do not commit secrets or real citizen data, including in screenshots/
  fixtures used for visual regression testing.
- Update `docs/frontend/*` and `docs/api/api-overview.md` when contracts
  or architecture change.
