# CivicLens — Component Architecture

Status: v1.0 draft
Related: system-architecture.md, backend/module-boundaries.md, backend/service-layer.md

## 1. Backend Module Map

Each module under `backend/app/modules/` owns its own tables, service layer,
and router. Modules interact only through service-layer function calls or
internal events — never by importing another module's ORM models directly.

| Module | Owns | Depends on |
|---|---|---|
| `auth` | users, sessions, refresh tokens, OTP challenges | — (foundational) |
| `citizens` | citizen_profiles, addresses, consents | auth |
| `schemes` | schemes, scheme_versions, eligibility_rules, document_requirements | — (foundational, admin-authored) |
| `eligibility` | eligibility_checks (results), rule evaluation engine | citizens, schemes |
| `documents` | documents, document_extractions | citizens, (calls OCR worker) |
| `applications` | applications, application_status_history | citizens, schemes, eligibility, documents |
| `assistant` (ai/) | knowledge_sources, knowledge_chunks, RAG orchestration | schemes, eligibility (as a callable tool) |
| `notifications` | notification records, delivery preferences | citizens, applications |
| `admin` | audit_logs, case_notes, admin-facing aggregation views | all modules (read-heavy, cross-cutting) |

## 2. Layering Within a Module

```
router (api/v1/<module>.py)
   │  — HTTP concerns only: parsing, auth dependency, status codes
   ▼
service (modules/<module>/service.py)
   │  — business logic, orchestration, transaction boundaries
   ▼
repository (modules/<module>/repository.py)
   │  — persistence only: queries, no business logic
   ▼
models (modules/<module>/models.py)  — SQLAlchemy ORM
```

Pydantic schemas live alongside each module (`modules/<module>/schemas.py`)
and are the only types that cross the router boundary; ORM models never
leak into API responses directly (see backend/repository-pattern.md).

## 3. Cross-Module Interaction Examples

### 3.1 Running an eligibility check
`eligibility.service` calls `citizens.service.get_profile_snapshot()` and
`schemes.service.get_active_rules(scheme_id)` — both return typed DTOs, not
ORM objects — evaluates the rule DSL in-process, and persists an
`eligibility_checks` row referencing the profile_version and scheme_version
used. No module reaches into another's tables directly.

### 3.2 Assistant answering an eligibility question
`assistant.service` recognizes an eligibility-shaped question, calls
`eligibility.service.evaluate(citizen_id, scheme_id)` as a tool rather than
retrieving prose and letting the LLM describe rules itself, then composes a
response combining the deterministic result with retrieved supporting text
for context/tone.

### 3.3 Starting an application
`applications.service` calls `eligibility.service` to confirm current
eligibility status, `documents.service` to confirm required documents are
verified, and `schemes.service` for the current document_requirements list,
then assembles an `applications` row plus initial
`application_status_history` entry.

## 4. Frontend Components

- `apps/web`: citizen-facing PWA (React). Key surfaces: onboarding/profile,
  scheme discovery, scheme detail + eligibility explanation, document
  upload, application flow, assistant chat, notifications.
- `apps/admin`: scheme administrator + support staff console. Key surfaces:
  scheme/version/rule editor (built on the same rule DSL as the engine),
  knowledge base ingestion monitor, application queue, audit log viewer,
  case notes.

Both consume the same OpenAPI-generated client (`docs/api/api-overview.md`).

## 5. Worker Components

- `workers/ocr`: consumes document-upload events, calls OCR provider,
  writes `document_extractions`, flags low-confidence results.
- `workers/ingestion`: consumes knowledge-source ingestion jobs, chunks
  documents, generates embeddings, writes `knowledge_chunks`.
- `workers/notifications`: consumes notification events, dispatches via
  SMS/email provider, records delivery status.
- `ai/`: RAG orchestration library shared by the `assistant` module and the
  `workers/ingestion` pipeline (retrieval, prompt construction, citation
  formatting) — a library, not a separate deployable, invoked both
  synchronously (chat) and from workers (batch evaluation).

## 6. Boundary Enforcement

Module boundaries are enforced in CI via an import-linter style check:
a module may import another module's `service` and `schemas`, never its
`models` or `repository`. Violations fail the build (see
`backend/module-boundaries.md` for the exact rule set and
`infrastructure/ci-cd.md` for where this gate runs).
