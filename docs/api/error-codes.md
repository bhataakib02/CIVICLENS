# CivicLens — Production Error Codes & Client Contract

This document indexes production error code identifiers, HTTP status codes, meanings, and client retry policies.

---

## Production Error Code Index

| Error Code Identifier | HTTP Status | Meaning | Retryable? | Client Action |
|---|---|---|---|---|
| `INVALID_CREDENTIALS` | 401 Unauthorized | Email or password incorrect. | No | Prompt user to re-enter password. |
| `TOKEN_EXPIRED` | 401 Unauthorized | Access token expired. | Yes | Perform refresh token request. |
| `REFRESH_TOKEN_INVALID` | 401 Unauthorized | Refresh token invalid or revoked. | No | Redirect user to `/login`. |
| `RESOURCE_FORBIDDEN` | 403 Forbidden | User lacks role or ownership permissions. | No | Display authorization error message. |
| `FOUR_EYES_REQUIRED` | 409 Conflict | Author cannot publish own scheme version. | No | Require separate admin reviewer approval. |
| `VERSION_IMMUTABLE` | 409 Conflict | Published scheme version cannot be edited. | No | Create new draft version. |
| `INVALID_STATE_TRANSITION`| 400 Bad Request | Invalid application status transition. | No | Refresh state and show valid actions. |
| `INVALID_FILE_HEADER` | 422 Unprocessable | File header magic bytes mismatch MIME type. | No | Prompt user to re-upload valid PDF/image. |
| `FILE_TOO_LARGE` | 413 Payload Too Large| Upload size exceeds 10MB limit. | No | Prompt user to compress file. |
| `RATE_LIMIT_EXCEEDED` | 429 Too Many Requests | Endpoint rate limit threshold exceeded. | Yes | Exponential backoff retry after header interval. |
| `SERVICE_UNAVAILABLE` | 503 Service Unavailable| Downstream dependency (DB/Redis) offline. | Yes | Retry request after delay. |
