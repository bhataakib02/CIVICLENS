# `apps/admin` — Scheme Administration & Support Console

Internal-facing console for scheme administrators and support staff:
scheme/version/rule authoring, knowledge base ingestion monitoring,
application queue, audit log viewer, case notes.

## Before Implementing

Read `docs/architecture/component-architecture.md` §4,
`docs/frontend/frontend-architecture.md`, and `docs/ai/rule-dsl.md`
(the rule editor here must render/edit the exact same DSL structure the
engine evaluates — one AST, three renderers, per rule-dsl.md §7).

## Key Constraints

- Desktop-first, information-dense — different design priorities from
  `apps/web`, though sharing the same design token set
  (`docs/frontend/design-system.md`).
- The scheme_version publish flow enforces four-eyes review in the UI
  (disabling self-publish, surfacing the required second reviewer step) —
  this is a UX affordance on top of the server-side enforcement in
  `docs/security/authorization-model.md` §4, never a substitute for it.
- Rule editor must validate against the DSL grammar and field registry
  client-side for immediate feedback, with the server-side validation in
  `docs/ai/rule-dsl.md` as the actual authority.
- Admin/scheme_admin accounts require MFA (`docs/security/authentication-security.md`
  §2) — the login flow here differs from `apps/web`'s OTP flow.

## Rules

- Preserve module boundaries; consume the same generated API client as
  `apps/web`.
- Add tests with behavior changes, especially around the rule editor and
  publish workflow given their direct impact on citizen eligibility
  outcomes.
- Do not commit secrets or real citizen data.
- Update `docs/api/api-overview.md` and `docs/ai/rule-dsl.md` when
  contracts change.
