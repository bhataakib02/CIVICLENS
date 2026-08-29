# CivicLens — Functional Requirements

Status: v1.0 draft
Related: product-requirements.md, non-functional-requirements.md, api/api-overview.md

Each requirement has an ID for traceability into API contracts, tests, and
ADRs. Format: `FR-<module>-<n>`.

## FR-AUTH — Authentication & Accounts

- FR-AUTH-1: A citizen can register with phone number + OTP, or email +
  password. Phone+OTP is the primary method (higher expected adoption).
- FR-AUTH-2: A citizen can have exactly one account per verified phone
  number; duplicate registration attempts must be rejected with a clear
  "account exists, log in instead" response.
- FR-AUTH-3: Sessions use short-lived access tokens (JWT) + rotating refresh
  tokens. Refresh tokens are revocable (logout-all-devices).
- FR-AUTH-4: An assisting agent (CSC operator) can operate under a distinct
  role that lets them create/manage citizen profiles on behalf of citizens,
  with an explicit consent record captured per citizen (see FR-CONSENT).
- FR-AUTH-5: Admin and scheme-administrator roles authenticate via a
  separate, more restrictive flow (mandatory MFA).

## FR-PROFILE — Citizen Profile

- FR-PROFILE-1: A citizen profile stores demographic and socioeconomic
  attributes needed for eligibility evaluation (age/DOB, gender, state,
  district, income bracket or declared annual income, caste category,
  disability status, occupation, land ownership, family size, marital
  status, education level).
- FR-PROFILE-2: Profile fields are collected incrementally ("progressive
  profiling") — a citizen is never forced to fill a long form before seeing
  any value; each new field unlocks more precise eligibility results.
- FR-PROFILE-3: A citizen can edit any profile field at any time; edits
  trigger re-evaluation of previously computed eligibility results.
- FR-PROFILE-4: A citizen can maintain multiple addresses (permanent /
  current) and select which applies per scheme where relevant.
- FR-PROFILE-5: Profile changes are versioned; eligibility_checks reference
  the profile snapshot used, so past determinations remain explainable even
  after profile edits.

## FR-CONSENT — Consent Management

- FR-CONSENT-1: Explicit, scoped consent is captured before: (a) an agent
  acts on a citizen's behalf, (b) documents are processed by OCR/extraction,
  (c) profile data is shared with a third-party scheme portal on export.
- FR-CONSENT-2: A citizen can view and revoke active consents; revocation
  stops future use but does not retroactively delete already-submitted
  government applications.

## FR-SCHEME — Scheme Catalog

- FR-SCHEME-1: Schemes are browsable by category (education, health,
  agriculture, housing, employment, social security, disability, women &
  child, etc.), by administering department, and by state/central scope.
- FR-SCHEME-2: Each scheme has a canonical `scheme` record and one or more
  `scheme_versions`, each with an effective date range, so historical
  versions remain queryable.
- FR-SCHEME-3: Full-text and semantic search over scheme name, description,
  and benefits.
- FR-SCHEME-4: Each scheme detail view shows: benefits, eligibility summary,
  required documents, application process, administering department, source
  citations, and last-verified date.

## FR-ELIGIBILITY — Eligibility Engine

- FR-ELIGIBILITY-1: Eligibility is evaluated by a deterministic rule engine
  against structured `eligibility_rules`, not by asking an LLM to "decide."
  See `ai/eligibility-engine.md` and `ai/rule-dsl.md`.
- FR-ELIGIBILITY-2: For a given citizen + scheme, the engine returns one of:
  `eligible`, `not_eligible`, `likely_eligible` (missing optional data),
  `insufficient_data` (missing required data), each with a per-rule
  breakdown (pass/fail/unknown + human-readable explanation + source
  citation).
- FR-ELIGIBILITY-3: A citizen can run a bulk eligibility check across all
  active schemes for their profile in a single request; results are ranked
  by likelihood and benefit relevance.
- FR-ELIGIBILITY-4: Eligibility results are cached per (profile_version,
  scheme_version) pair and invalidated when either changes.
- FR-ELIGIBILITY-5: Rule authors (scheme admins) can simulate a rule change
  against a sample of anonymized profiles before publishing a new
  scheme_version.

## FR-ASSISTANT — Conversational Assistant (RAG)

- FR-ASSISTANT-1: The assistant answers free-text questions using retrieval
  over ingested `knowledge_chunks` only; it must not answer from open-domain
  model knowledge for scheme-specific facts.
- FR-ASSISTANT-2: Every assistant answer that makes a factual claim about a
  scheme includes a citation to the source `knowledge_source` /
  `scheme_version`.
- FR-ASSISTANT-3: If retrieval confidence is below threshold or no relevant
  chunk exists, the assistant must say it doesn't have a verified answer
  rather than guessing, and offer to route to human/agent support.
- FR-ASSISTANT-4: The assistant can invoke the eligibility engine as a tool
  when a citizen asks an eligibility question, rather than describing rules
  in prose from retrieved text alone.

## FR-DOCS — Document Intelligence

- FR-DOCS-1: A citizen can upload identity, income, residence, and
  category-certificate documents (image or PDF).
- FR-DOCS-2: Uploaded documents are OCR'd and structured fields are
  extracted (name, DOB, document number, issuing authority, address,
  income figure, validity date) into `document_extractions`.
- FR-DOCS-3: Extracted fields are shown to the citizen for confirmation
  before being used to auto-fill profile or applications.
- FR-DOCS-4: The system flags low-confidence extractions and blurry/invalid
  uploads for re-capture rather than silently accepting bad data.
- FR-DOCS-5: A document, once verified, can be reused across multiple
  scheme applications without re-upload.

## FR-APPLICATION — Application Workflow

- FR-APPLICATION-1: A citizen can start an application for any scheme they
  are `eligible` or `likely_eligible` for.
- FR-APPLICATION-2: The application assembles required documents +
  profile fields + scheme-specific questions, and blocks submission until
  all required items are present and verified.
- FR-APPLICATION-3: Application status transitions follow a defined state
  machine (see `backend/module-boundaries.md` / status history table) and
  every transition is recorded in `application_status_history` with actor
  and timestamp.
- FR-APPLICATION-4: A citizen can export a completed application package
  (PDF + attachments) for manual submission where no direct integration
  exists.
- FR-APPLICATION-5: A citizen can withdraw an application prior to a
  terminal status.

## FR-NOTIFY — Notifications

- FR-NOTIFY-1: Citizens receive notifications (SMS + in-app, email optional)
  for: new scheme matches, application status changes, document
  re-verification requests, and scheme deadline reminders.
- FR-NOTIFY-2: Notification preferences are configurable per channel and per
  category.

## FR-ADMIN — Administration

- FR-ADMIN-1: Scheme administrators can create/edit schemes, scheme
  versions, eligibility rules, and document requirements through an admin
  UI backed by the same rule DSL used by the engine (no shadow logic).
- FR-ADMIN-2: Every scheme_version publish requires a review step (four-eyes
  principle) before it becomes effective.
- FR-ADMIN-3: Admins can view knowledge base ingestion status, flag stale
  sources, and trigger re-ingestion.
- FR-ADMIN-4: Admins can view audit logs filtered by user, action type, and
  date range.

## FR-CASEWORK — Case Notes & Support

- FR-CASEWORK-1: Support staff/agents can attach case notes to a citizen or
  application for tracking manual follow-up, visible only to staff roles.
