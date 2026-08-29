# API Idempotency

Status: v1.0 draft
Related: api-overview.md §4, openapi.yaml (POST /applications, POST /documents)

## 1. Why It Matters

Citizens on low-bandwidth/flaky mobile connections (NFR-ACC-2) commonly
retry a request after a timeout without knowing whether the original
request actually succeeded server-side. For create operations
(`POST /applications`, `POST /documents`), a naive retry could create
duplicate applications or duplicate document uploads.

## 2. Mechanism

Idempotency-sensitive endpoints accept an `Idempotency-Key` header
(client-generated UUID, one per logical user action). The server stores a
short-lived (24h) mapping of `(user_id, idempotency_key) → response`. A
repeated request with the same key returns the original response without
re-executing the operation.

## 3. Scope

Applied to: `POST /applications` (starting an application),
`POST /documents` (uploading a document). Not applied to read-only or
naturally-idempotent endpoints (e.g., `PATCH /me`, which is safe to retry
as-is since it's a field-level upsert).

## 4. Client Behavior

Clients generate a new `Idempotency-Key` per distinct user action (e.g.,
per "tap upload" event), and reuse the same key across automatic retries
of that same action — never across genuinely separate actions, which
would incorrectly suppress a legitimate second submission.
