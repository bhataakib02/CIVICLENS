# Webhooks

Status: v1.0 draft — not exposed externally at launch
Related: api-overview.md, backend/websocket-architecture.md

## 1. v1.0 Scope

CivicLens does not expose outbound webhooks to third parties in v1.0.
Real-time updates within CivicLens itself (e.g., application status
changes, assistant streaming responses) are delivered via websocket/SSE to
`apps/web`/`apps/admin` directly — see backend/websocket-architecture.md —
not via webhook callbacks to an external URL, since there are no external
integrators to notify at launch.

## 2. Inbound Webhooks (from providers, not the same as the above)

CivicLens does *consume* inbound webhook-style callbacks from providers
where relevant:
- SMS gateway delivery status callbacks → update `notifications.status`.
- (If/when adopted) OCR provider async-completion callbacks, as an
  alternative to polling.

These are internal integration details, not a citizen/admin-facing API
surface, and are documented in the relevant provider integration code
rather than in the public `openapi.yaml` contract.

## 3. Future Consideration

If CivicLens later integrates directly with government portal APIs
(explicitly out of scope for v1.0 per product-requirements.md §3), an
outbound webhook or callback mechanism for application status
synchronization would need its own security review (signature
verification, retry/backoff, replay protection) before being added to
this document as a real contract.
