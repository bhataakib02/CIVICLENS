# State Management

Status: v1.0 draft
Related: frontend-architecture.md §3

## 1. State Categories

| Category | Examples | Managed by |
|---|---|---|
| Server/cache state | Schemes, eligibility results, applications, documents | Query-cache library (fetch, cache, invalidate, background-refetch), keyed by the same identifiers as the API |
| Session/auth state | Access token, current user, role | A small dedicated auth store; token refresh handled transparently by the API client layer, not scattered per-feature |
| UI/local state | Form input, modal open/closed, wizard step | Component-local state (useState/useReducer) — never promoted to global state unless genuinely shared across distant components |
| Real-time/derived state | Live document status, live application status | Query cache entries updated by WebSocket events (backend/websocket-architecture.md), not a separate parallel store |

## 2. Principles

- **Server state is not duplicated into a separate global store.** The
  query cache is the single source of truth for anything that originates
  server-side; components read from it directly rather than syncing a
  copy into Redux-style global state, which would create two sources of
  truth to keep consistent.
- **Eligibility and profile edits invalidate related cache entries
  explicitly** — editing a profile field invalidates cached eligibility
  results (mirroring the backend's own cache invalidation on profile
  version change, ai/eligibility-engine.md §4), so the UI never shows a
  stale eligibility result next to a just-edited profile field.
- **Offline resilience**: given NFR-ACC-2's low-connectivity target, the
  cache layer tolerates request failures gracefully (showing last-known
  data with a staleness indicator) rather than blanking the UI on a
  transient network error.

## 3. Multi-Step Flows

The application-submission wizard and progressive-profiling flow keep
their in-progress state locally (not yet submitted to the server) until an
explicit save/submit action, with periodic local persistence (not
browser localStorage per the artifact-storage restriction pattern
elsewhere in this doc set, but the app's own IndexedDB-backed persistence
layer) so a citizen doesn't lose multi-minute form progress to a dropped
connection.
