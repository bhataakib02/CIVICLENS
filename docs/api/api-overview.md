# CivicLens — API Overview

Status: v1.0 draft
Related: ../../openapi.yaml (authoritative contract), authentication.md, authorization.md, error-handling.md, pagination.md, versioning.md, idempotency.md, webhooks.md

## 1. Conventions

- Base path: `/api/v1`. Breaking changes ship as `/api/v2`; see
  versioning.md for the deprecation policy (minimum 6-month overlap).
- All request/response bodies are JSON except file upload (`multipart/form-data`)
  and PDF export (`application/pdf`).
- All timestamps are ISO 8601 UTC.
- All list endpoints are paginated with `page` / `page_size` query params and
  a `{items, page, page_size, total}` envelope — see pagination.md.
- Errors follow a single shape (`error.code`, `error.message`,
  `error.request_id`, optional `error.field_errors`) — see
  error-handling.md. `request_id` always correlates to a server-side trace
  (NFR-OBS-1).

## 2. Authentication

Bearer JWT access tokens, obtained via phone+OTP (citizens) or
email+password+MFA (staff/admin). See authentication.md for the full flow
and authorization.md for the role/ownership model enforced on every
endpoint. Public (unauthenticated) endpoints are limited to `/health`,
`/health/ready`, and the OTP request/verify pair.

## 3. Resource Groups

| Group | Base path | Summary |
|---|---|---|
| Auth | `/auth/*` | OTP login, token refresh, logout |
| Profile | `/me`, `/me/addresses` | Citizen's own profile and addresses |
| Schemes | `/schemes/*` | Browse/search the public scheme catalog |
| Eligibility | `/eligibility/*` | Deterministic eligibility evaluation (single + bulk) |
| Assistant | `/assistant/*` | Retrieval-grounded conversational Q&A |
| Documents | `/documents/*` | Upload, OCR status, extraction confirmation |
| Applications | `/applications/*` | Application lifecycle: create, submit, withdraw, export |
| Notifications | `/notifications/*` | Notification history and preferences |
| Admin | `/admin/*` | Scheme/version/rule authoring, knowledge base management, audit logs (scheme_admin / admin roles only) |

Full request/response schemas for every endpoint live in `openapi.yaml`,
which is the source of truth this document summarizes — do not let this
page and the contract drift; the contract wins on any discrepancy.

## 4. Notable Design Choices

- **`/eligibility/check` never accepts a citizen-supplied result** — it
  always recomputes server-side from the current profile snapshot and the
  scheme's active `scheme_version`; there is no client-writable eligibility
  field anywhere in the API.
- **`/assistant/messages` responses always include `citations`**, and may
  include `eligibility_tool_calls` showing exactly which deterministic
  evaluation backed any eligibility-flavored answer — the client should
  render these, not just the prose answer, per FR-ASSISTANT-2.
- **`POST /applications` returns 409, not 201**, if the citizen isn't
  currently `eligible` or `likely_eligible` for the scheme — this is
  enforced server-side, not just as UI guidance.
- **`POST /applications/{id}/submit` validates completeness** (all
  mandatory documents verified, all scheme-specific answers present) and
  returns 422 with field-level errors rather than allowing a
  half-complete submission.
- **Idempotency**: `POST /applications` and `POST /documents` accept an
  `Idempotency-Key` header (see idempotency.md) so retried uploads/creates
  from a flaky mobile connection don't create duplicates.

## 5. Rate Limits

Enforced per authenticated user (or per phone number for OTP endpoints
pre-auth); current limits are documented in security/rate-limiting.md and
returned via standard `Retry-After` headers on 429 responses.

## 6. Client Generation

Both `apps/web` and `apps/admin` consume a TypeScript client generated
from `openapi.yaml` in CI (see infrastructure/ci-cd.md) — hand-written API
client code is disallowed precisely so the contract can't silently drift
from what the frontend actually calls.
