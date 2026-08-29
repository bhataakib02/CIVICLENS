# WebSocket Architecture

Status: v1.0 draft
Related: architecture/system-architecture.md §3.2, ADR-006, api/api-overview.md

## 1. Purpose

Push real-time updates to the client for events that originate from
async workers, so the frontend doesn't need to poll: document
processing completion, application status changes, and streaming
assistant responses.

## 2. Connection Model

Client opens a single authenticated WebSocket connection per session
(`wss://.../ws`, JWT passed at connect time and validated like any other
request). The connection is scoped to the authenticated citizen/agent —
server-side, messages are only ever pushed for entities that user is
authorized to see (the same ownership checks from
security/authorization-model.md apply to what gets pushed, not just what
can be fetched via REST).

## 3. Message Types

| Type | Payload | Triggered by |
|---|---|---|
| `document.status_changed` | document_id, new status | OCR worker completes/fails |
| `application.status_changed` | application_id, from/to status | Status transition (any actor) |
| `assistant.token` | conversation_id, partial text | Streaming generation, token-by-token |
| `assistant.done` | conversation_id, final answer + citations | Generation complete |

## 4. Fallback

Clients that can't maintain a WebSocket connection (poor connectivity,
older browsers) fall back to polling the relevant REST endpoint
(`GET /documents/{id}`, `GET /applications/{id}`) — every piece of
information pushed over the socket is also obtainable via a normal REST
call, so the socket is purely a latency/efficiency optimization, never a
single point of failure for functionality (consistent with
NFR-ACC-2's low-bandwidth device support).

## 5. Scaling

WebSocket connections are held by the stateless API tier instances; a
Redis pub/sub backplane fans out worker-originated events to whichever
instance holds the relevant client connection, so horizontal API scaling
(ADR-001) isn't broken by sticky-connection requirements.
