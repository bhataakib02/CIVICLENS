# API Versioning

Status: v1.0 draft
Related: api-overview.md, openapi.yaml

## 1. Scheme

Path-based major versioning: `/api/v1`, and a future `/api/v2` for
breaking changes. No versioning in headers or query params — path
versioning is simplest for clients, caching, and routing.

## 2. What Counts as Breaking

Breaking: removing a field, changing a field's type or meaning, removing
an endpoint, changing an enum's set of valid values in a way that
invalidates existing client logic, tightening validation on an existing
field.

Non-breaking (ships within `v1` without a version bump): adding a new
optional field to a response, adding a new endpoint, adding a new enum
value that clients are expected to handle gracefully (documented as such
in the field's description), relaxing validation.

## 3. Deprecation Policy

A breaking change ships as `/api/v2` while `/api/v1` continues to be
served, with a minimum 6-month overlap window and a `Deprecation` /
`Sunset` header on `v1` responses once `v2` is available, giving
`apps/web`/`apps/admin` and any third-party integrators time to migrate.
`v1` is not removed until traffic to it is confirmed negligible or the
overlap window has elapsed, whichever is later.

## 4. Contract-First Enforcement

Since both frontends generate their client from `openapi.yaml`
(api-overview.md §6), any breaking change is caught at client-generation/
build time in CI, not discovered at runtime — this is treated as the
primary safety net for versioning discipline.
