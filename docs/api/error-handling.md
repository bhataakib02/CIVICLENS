# API Error Handling

Status: v1.0 draft
Related: api-overview.md, openapi.yaml (components.schemas.Error)

## 1. Error Envelope

Every non-2xx response body follows one shape:

```json
{
  "error": {
    "code": "validation_error",
    "message": "declared_annual_income must be a non-negative number",
    "request_id": "req_9f2c...",
    "field_errors": [
      {"field": "declared_annual_income", "message": "must be >= 0"}
    ]
  }
}
```

`field_errors` is present only for validation failures (422); other error
types omit it.

## 2. Status Code Usage

| Code | Meaning |
|---|---|
| 400 | Malformed request (bad JSON, wrong content type) |
| 401 | Missing/invalid/expired auth token |
| 403 | Authenticated but not authorized (role or ownership failure) |
| 404 | Resource not found, or hidden for authorization reasons (authorization.md §3) |
| 409 | Conflict with current state (e.g., starting an application for an ineligible scheme) |
| 422 | Request well-formed but fails validation |
| 429 | Rate limited |
| 5xx | Server error — always logged with the same `request_id` returned to the client |

## 3. `request_id` Correlation

Every response (success or error) carries a `request_id` that correlates
to the corresponding trace in operations/tracing.md and log lines in
operations/logging.md — essential for citizen support to diagnose a
reported issue without needing the citizen to describe what happened in
technical terms.

## 4. Client Guidance

Clients should treat `error.code` as the stable, programmatically
switchable identifier and `error.message` as human-readable/log-friendly
only — `message` text is not guaranteed stable across releases,
`code` is.

## 5. No Silent Failures

Every code path either returns a success response or a properly-shaped
error — there's no "empty 200" or swallowed-exception pattern; this is
enforced via contract tests (testing/api-testing.md).
