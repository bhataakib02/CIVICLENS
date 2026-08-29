# Frontend Architecture

Status: v1.0 draft
Related: architecture/component-architecture.md §4, api/api-overview.md §6, pwa.md, state-management.md

## 1. Two Applications

- `apps/web` — citizen-facing PWA (React), optimized for low-end devices
  and constrained connectivity (pwa.md, NFR-ACC-2).
- `apps/admin` — scheme administrator + support staff console (React),
  optimized for desktop, information-dense workflows (rule editor,
  knowledge base monitor, application queue).

Both are separate builds/deployments sharing a common component library
and the generated API client (api/api-overview.md §6) but not a single
monolithic app — their audiences, device targets, and update cadences
differ enough to warrant separation.

## 2. Structure (per app)

```
apps/web/src/
├── api/           # generated client + thin wrappers
├── components/    # shared UI primitives (design-system.md)
├── features/      # feature-scoped modules: onboarding, schemes,
│                  #   eligibility, documents, applications, assistant
├── i18n/          # translation resources (internationalization.md)
├── state/         # global state (state-management.md)
└── routes/
```

## 3. Data Fetching

All server communication goes through the generated OpenAPI client;
feature modules don't hand-construct fetch calls. Server state (schemes,
eligibility results, applications) is cached and invalidated via a
query-cache library rather than duplicated into global state
(state-management.md).

## 4. Rendering Strategy

Client-side rendered PWA (not SSR) for v1.0 — simplifies hosting
(static assets via CDN, per deployment-architecture.md) and fits the
offline/installable PWA model better than SSR would; revisit if SEO or
first-paint requirements change materially.

## 5. Real-Time Updates

WebSocket connection (backend/websocket-architecture.md) drives live
updates for document processing and application status, with REST polling
fallback for constrained connectivity.
