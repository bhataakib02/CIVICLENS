# API / Contract Testing

Status: v1.0 draft
Related: testing-strategy.md §5, api/api-overview.md, openapi.yaml

## 1. Contract Conformance

Every endpoint in `openapi.yaml` has at least one automated test asserting
its actual response matches the declared schema (status codes, response
shape, required fields) — generated from the spec itself (e.g., via
schemathesis or an equivalent property-based API testing tool) so new
endpoints are caught if a contract test is missing, not left to manual
tracking.

## 2. What's Covered Beyond Basic Schema Match

- **Auth/authorization**: missing token → 401; wrong role → 403; ownership
  violation (e.g., citizen A requesting citizen B's application) → 403/404
  per api/authorization.md §3.
- **Validation**: malformed input → 422 with the expected `field_errors`
  shape (api/error-handling.md).
- **Pagination envelope**: list endpoints return the `{items, page,
  page_size, total}` shape consistently (api/pagination.md).
- **Idempotency**: repeated `POST /applications`/`POST /documents` with
  the same `Idempotency-Key` returns the original response, not a
  duplicate resource (api/idempotency.md).
- **Rate limiting**: exceeding a documented limit returns 429 with
  `Retry-After` (security/rate-limiting.md).

## 3. Drift Detection

Because both `apps/web` and `apps/admin` generate their client from
`openapi.yaml` (api/api-overview.md §6), a mismatch between the spec and
the actual implementation fails client generation in CI — this is a second,
independent line of defense against contract drift beyond the dedicated
contract test suite itself.

## 4. Run Cadence

Runs on every PR touching `backend/app/api` or `openapi.yaml` — required
for merge, not a nightly-only check, since contract breaks are cheap to
catch immediately and expensive to catch after a frontend release ships
against a changed API.
