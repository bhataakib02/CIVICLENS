# CivicLens — System Architecture

Status: v1.0 draft
Related: component-architecture.md, data-flow.md, deployment-architecture.md, ADR-001, ADR-002, ADR-006

## 1. Architectural Style

CivicLens backend is a **modular monolith** (ADR-001): a single deployable
FastAPI application internally organized into isolated modules with enforced
boundaries, backed by PostgreSQL (+ pgvector) and Redis, with Celery workers
for asynchronous AI/document workloads. Microservices are explicitly
rejected for v1.0 — the team and scale don't justify the operational
overhead; module boundaries are kept clean enough that extraction into
services remains possible later if a specific module's load profile
diverges sharply from the rest (most likely candidates: document
OCR/extraction and the RAG pipeline).

## 2. High-Level Component Diagram

```
                        ┌─────────────────────────┐
                        │   Citizen Web / PWA      │
                        │   (apps/web)             │
                        └────────────┬─────────────┘
                                     │ HTTPS / JSON
                        ┌────────────▼─────────────┐
                        │   Admin Console           │
                        │   (apps/admin)            │
                        └────────────┬─────────────┘
                                     │
                     ┌───────────────▼────────────────┐
                     │      API Gateway / Load         │
                     │      Balancer (ALB)             │
                     └───────────────┬────────────────┘
                                     │
                 ┌───────────────────▼───────────────────┐
                 │      FastAPI Backend (stateless,        │
                 │      horizontally scaled)                │
                 │  ┌───────────────────────────────────┐  │
                 │  │ api/v1  (routers per module)        │  │
                 │  ├───────────────────────────────────┤  │
                 │  │ modules/                             │
                 │  │   auth · citizens · schemes ·        │
                 │  │   eligibility · documents ·          │
                 │  │   applications · notifications ·     │
                 │  │   admin                              │
                 │  ├───────────────────────────────────┤  │
                 │  │ core/  (config, security, logging)  │  │
                 │  │ db/    (session, base models)       │  │
                 │  └───────────────────────────────────┘  │
                 └──────┬───────────────┬───────────────┬──┘
                        │               │               │
             ┌──────────▼───┐   ┌───────▼──────┐  ┌─────▼──────────┐
             │ PostgreSQL   │   │ Redis        │  │ Celery Workers  │
             │ + pgvector   │   │ (cache/queue │  │ (ai/, workers/) │
             │ (ADR-002)    │   │  broker)     │  │ (ADR-006)       │
             └──────────────┘   └──────────────┘  └────────┬────────┘
                                                             │
                                          ┌──────────────────┼──────────────────┐
                                          │                  │                  │
                                 ┌────────▼─────┐  ┌─────────▼────────┐ ┌──────▼───────┐
                                 │ OCR / Doc     │  │ Embedding /       │ │ Notification │
                                 │ Extraction    │  │ RAG pipeline      │ │ dispatch     │
                                 │ pipeline      │  │ (LLM provider)    │ │ (SMS/email)  │
                                 └───────────────┘  └──────────────────┘ └──────────────┘
                                          │
                                 ┌────────▼─────────┐
                                 │ Object Storage    │
                                 │ (documents, S3)   │
                                 │ (ADR-005)         │
                                 └───────────────────┘
```

## 3. Request Paths

### 3.1 Synchronous (API-served)
Citizen/admin requests that must return within a normal HTTP timeout:
auth, profile CRUD, scheme browse/search, eligibility evaluation (rule
engine is in-process and deterministic — no external call on the critical
path), application CRUD, notification preferences.

### 3.2 Asynchronous (worker-served)
Work that is too slow, unreliable, or bursty for the request/response cycle:
OCR + document extraction, knowledge source ingestion + chunking +
embedding generation, RAG generation for the assistant (streamed back to
the client over the sync connection but computed via a worker-backed
pipeline for retries/rate-limit handling), notification delivery
(SMS/email providers), scheduled staleness checks on the knowledge base.

The API enqueues a job onto Redis (Celery broker) and returns a job/status
reference; the client polls or receives a websocket/SSE push
(`backend/websocket-architecture.md`) for completion.

## 4. Data Stores

| Store | Purpose |
|---|---|
| PostgreSQL (primary) | All relational/domain data: users, profiles, schemes, rules, applications, audit logs |
| pgvector (same PG instance) | `knowledge_chunks` embeddings for RAG retrieval — kept in the same database as source-of-truth data rather than a separate vector DB, to keep citation joins (chunk → source → scheme_version) transactionally consistent (ADR-002) |
| Redis | Celery broker, response caching (eligibility result cache keyed by profile_version+scheme_version), rate limiting counters |
| Object storage (S3-compatible) | Uploaded documents, generated application-package PDFs (ADR-005) |

## 5. External Integrations

- LLM provider (Anthropic Claude) for RAG generation and free-text →
  structured-profile assistance. Never authoritative for eligibility
  outcomes (NFR-AI-2).
- OCR provider (managed OCR API, pluggable) for document text extraction.
- SMS gateway for OTP and notifications.
- Object storage (S3 or S3-compatible) for documents.
- (Future / not v1.0) direct government portal APIs where available.

## 6. Environments

Local (Docker Compose) → staging (AWS) → production (AWS), each with
isolated databases and object storage buckets; see
`infrastructure/environments.md` and `infrastructure/aws-architecture.md`.

## 7. Key Architectural Principles

1. **Eligibility determination is deterministic and explainable.** The rule
   engine, not the LLM, decides pass/fail. The LLM's role is limited to
   language tasks: retrieval-grounded Q&A, extracting structured data from
   free text/documents, and summarization — never adjudicating eligibility.
2. **Everything citation-bearing is traceable to a versioned source.**
   scheme_versions, eligibility_rules, and knowledge_chunks all carry
   provenance back to a knowledge_source with an effective date range.
3. **Module boundaries are enforced, not aspirational.** Cross-module access
   goes through service-layer interfaces, not direct ORM queries into
   another module's tables (see backend/module-boundaries.md).
4. **Async by default for anything unbounded or third-party-dependent.**
   OCR and LLM calls are never on a path that must complete within a normal
   web request timeout, both for latency and for resilience to provider
   outages (NFR-AVAIL-3).
5. **PII has a shorter blast radius than everything else.** Document storage,
   logging, and caching all treat PII as a distinct handling class (see
   security/pii-handling.md, security/document-security.md).
