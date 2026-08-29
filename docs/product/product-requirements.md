# CivicLens — Product Requirements Document (PRD)

Status: v1.0 draft
Owner: Product
Related: functional-requirements.md, non-functional-requirements.md, system-architecture.md

## 1. Problem Statement

Citizens in India are eligible for large numbers of government welfare schemes
(central + state) but discovery, eligibility interpretation, and application
are fragmented across departmental portals, PDFs, and physical offices.
Consequences:

- Eligible citizens miss schemes because they never discover them.
- Citizens misjudge their own eligibility from ambiguous scheme language and
  either apply for schemes they don't qualify for, or skip ones they do.
- Document requirements are inconsistent and citizens submit the wrong
  paperwork, causing rejections and re-submission cycles.
- Scheme rules change (budget cycles, amendments) and citizens act on stale
  information.

CivicLens is a citizen-facing assistant that unifies scheme discovery,
plain-language eligibility explanation, guided document collection, and
application tracking, backed by a verifiable knowledge base of government
sources (not free-form LLM knowledge).

## 2. Goals

1. A citizen can find every scheme they are plausibly eligible for within one
   session, without knowing scheme names in advance.
2. Every eligibility determination is explainable: the citizen sees *which*
   rule they passed or failed and *why*, with a citation to the source
   document/section.
3. Citizens can upload identity/income/residence documents once and reuse
   them across multiple scheme applications.
4. Application status is trackable end-to-end inside CivicLens, not just a
   redirect to a third-party portal.
5. The knowledge base is auditable: every scheme rule traces to a specific
   government source document and version, with an effective date range.

## 3. Non-Goals (v1.0)

- CivicLens does not submit applications directly into government IT systems
  on the citizen's behalf (no scraping/automation of third-party portals) —
  v1 produces a completed application package the citizen submits themselves,
  or hands off via an official API where one exists.
- CivicLens does not provide legal advice or guarantee eligibility outcomes;
  all determinations are advisory ("likely eligible" / "likely ineligible"
  with evidence), never a legal ruling.
- No payment processing or disbursement handling.
- No multi-country support in v1 (India-only).

## 4. Primary Users

| Persona | Description | Primary need |
|---|---|---|
| Citizen (applicant) | May have low digital literacy, prefers regional language | Find schemes, understand eligibility, get help applying |
| Assisting agent (CSC operator / NGO worker) | Applies on behalf of citizens at scale | Fast multi-citizen workflow, bulk eligibility checks |
| Scheme administrator | Government/partner staff maintaining scheme data | Keep scheme rules, documents and versions current and correct |
| CivicLens admin/ops | Internal team | Monitor knowledge base health, moderate content, handle escalations |

See `user-personas.md` and `user-stories.md` for details (not reproduced here).

## 5. Core User Journeys

### 5.1 Discovery
Citizen provides basic profile attributes (age, state, district, income
bracket, occupation, category, disability status, family composition, land
ownership, etc. — only what's needed, incrementally). CivicLens returns a
ranked list of schemes with an eligibility likelihood, not a single yes/no.

### 5.2 Eligibility explanation
For any scheme, the citizen sees each eligibility rule evaluated against
their profile: pass, fail, or "insufficient data" — with the exact rule text
and its source citation.

### 5.3 Document collection
CivicLens tells the citizen which documents are required for a scheme, lets
them upload once, and reuses the extracted structured data (name, DOB,
address, income) across all future eligibility checks and applications until
the citizen updates it.

### 5.4 Application
Citizen assembles an application package per scheme: personal data +
verified documents + any scheme-specific fields. CivicLens validates
completeness before allowing submission/export.

### 5.5 Tracking
Application status changes (submitted → under review → additional info
requested → approved/rejected → disbursed, or equivalent) are visible with
history and citizen-facing notifications.

### 5.6 Assistant Q&A
Citizen can ask free-text questions ("Am I eligible for a scholarship if my
father is a farmer?"). Answers are generated via retrieval over the
knowledge base (RAG), never from open-domain model knowledge, and always
carry citations back to source documents.

## 6. Success Metrics

- % of eligible-for-at-least-one-scheme citizens who discover ≥1 relevant
  scheme within their first session.
- Eligibility explanation comprehension: citizen self-reported understanding
  (survey / thumbs up-down on explanations).
- Application completion rate (started → submitted) per scheme.
- Time from document upload to reusable structured profile.
- Knowledge base staleness: max age of an unreviewed scheme_version.
- Assistant answer citation rate (should be ~100% — unanswerable without
  supporting source is a refusal, not a guess).

## 7. Constraints

- Must support low-bandwidth / low-end Android devices (PWA per
  `frontend/pwa.md`).
- Must support at least Hindi + English at launch, with an i18n framework
  that doesn't require code changes to add languages.
- All PII handling must comply with India's DPDP Act, 2023 (see
  `security/pii-handling.md`).
- Government scheme information changes on unpredictable schedules; the
  system must treat "knowledge freshness" as a first-class operational
  concern, not an afterthought (see `knowledge/source-verification.md`).

## 8. Release Scope (v1.0)

In scope: citizen auth, profile, scheme browse/search, eligibility engine
(deterministic rule evaluation, not LLM-decided), document upload + OCR
extraction, RAG-based assistant Q&A restricted to ingested sources,
application workflow with manual export/submission, notifications, admin
console for scheme/document/knowledge management, audit logging.

Out of scope for v1.0: direct government portal integration, payments,
multi-country, offline-first mode, voice interface (candidate for v1.1).

## 9. Open Questions

- Which state schemes are launch-priority (need partnership/data-sourcing
  agreements per state)?
- Is a government-verified identity check (e.g., Aadhaar-based) required at
  launch or can self-attested profile data be sufficient for eligibility
  *screening*, with verification deferred to actual application submission?
- Legal review needed on "advisory eligibility" disclaimers before launch.
