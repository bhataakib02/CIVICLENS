# CivicLens — Threat Model

Status: v1.0 draft
Related: security-architecture.md, pii-handling.md, document-security.md, ai/ai-safety.md, ai/hallucination-controls.md

Methodology: STRIDE-informed, scoped to CivicLens's actual attack surface
(citizen PII, government documents, an eligibility/rule engine, and an LLM
pipeline). Each threat lists impact, primary mitigation, and where the
mitigation is documented/implemented. This is a living document — new
threats get added as the system grows, not treated as a one-time exercise.

## 1. Citizen document theft
**Impact**: exposure of identity/income/residence documents (high-sensitivity
PII, potential identity fraud).
**Mitigation**: documents in access-controlled object storage, short-lived
pre-signed URLs issued only after an authorization check, encryption at
rest, malware/type scanning on upload. See document-security.md.

## 2. Cross-user document access
**Impact**: one citizen (or a compromised account) reading another citizen's
documents/profile.
**Mitigation**: row-level ownership checks in the service layer on every
document/profile/application read — never relying on the router or the
frontend to enforce this. Object storage keys are non-guessable UUIDs, not
sequential or citizen-derived. See authorization-model.md.

## 3. Prompt injection through government documents
**Impact**: an ingested (or maliciously submitted) knowledge source contains
text crafted to make the LLM ignore its instructions — e.g. to claim false
eligibility, leak system prompt content, or take unintended actions via
tool use.
**Mitigation**: retrieved content is passed to the model in a structurally
distinct, clearly-delimited context block with explicit instructions that
context is data, not commands; the model has no tool access that can
mutate state (the eligibility engine tool is read-only from the
assistant's perspective); knowledge sources are ingested only from a
vetted publisher allowlist, not arbitrary citizen-submitted URLs. See
ai/ai-safety.md.

## 4. RAG poisoning
**Impact**: a malicious or low-quality source enters the knowledge base and
the assistant cites it as authoritative, misleading citizens about
eligibility or benefits.
**Mitigation**: knowledge_sources ingestion restricted to a vetted publisher
allowlist with a review step before a source is marked `ingested` and
eligible for retrieval; source-verification.md defines a periodic
re-verification process; every assistant answer surfaces its source so a
citizen (or auditor) can independently check it.

## 5. Malicious uploaded files
**Impact**: an uploaded "document" is actually malware, or a crafted file
designed to exploit the OCR pipeline.
**Mitigation**: strict file type/size validation, malware scanning before
persistence, OCR pipeline runs in an isolated worker context with no
access to production credentials beyond what it strictly needs
(least-privilege worker IAM role). See document-security.md,
infrastructure/networking.md.

## 6. Privilege escalation
**Impact**: a citizen or agent account gains admin/scheme_admin capability,
or an agent account acts without a valid consent record.
**Mitigation**: role checks enforced server-side on every mutating
endpoint; consent-scoped access for agents, checked per-request, not
cached indefinitely; admin/scheme_admin accounts require MFA; role
changes themselves are audit-logged. See authorization-model.md,
audit-logging.md.

## 7. Eligibility-rule tampering
**Impact**: an unauthorized or malicious change to `eligibility_rules`
falsely includes or excludes citizens from a scheme, or a rule is crafted
to execute unintended logic.
**Mitigation**: rule DSL is a closed grammar with no code execution
(ADR-008, rule-dsl.md) — tampering can at worst produce an incorrect but
inert data structure, not arbitrary execution. Publish requires two-person
review (FR-ADMIN-2). Every rule change is versioned and audit-logged with
before/after diffs.

## 8. Stale government policies
**Impact**: a scheme's eligibility criteria or benefits change in the real
world but CivicLens continues serving outdated rules, causing citizens to
misjudge eligibility or apply incorrectly.
**Mitigation**: `knowledge_sources.last_verified_at` tracked and alerted on
beyond a staleness threshold (NFR-OBS-3); scheme_versions carry explicit
effective date ranges; source-verification.md defines a periodic review
cadence per scheme category.

## 9. PII leakage through logs
**Impact**: PII appears in plaintext application logs, error traces, or
analytics, expanding the blast radius of any log-access compromise.
**Mitigation**: structured logging with an enforced redaction layer for
fields flagged **PII** in data-dictionary.md; log pipeline tested against
this in security-testing.md; code review checklist item. See
pii-handling.md.

## 10. LLM hallucination
**Impact**: assistant states an incorrect fact about a scheme or implies an
eligibility outcome not actually produced by the deterministic engine.
**Mitigation**: architectural separation of "decides" vs. "describes"
(ai-architecture.md §1); mandatory citations (NFR-AI-1); eligibility
questions routed to the deterministic engine as a tool, never answered from
retrieved prose alone; evaluation gate before any pipeline change ships
(ADR-009). See hallucination-controls.md.

## 11. Application state manipulation
**Impact**: a citizen or malicious actor forces an application into a
status it shouldn't reach (e.g., directly to `approved`) bypassing the
intended workflow.
**Mitigation**: status transitions enforced by an explicit state machine in
the `applications` service layer, not settable directly via a generic
PATCH; every transition requires a valid actor role for that transition
type and is recorded in `application_status_history` (immutable).

## 12. API abuse
**Impact**: scraping the scheme catalog at scale, OTP-bombing a phone
number, or driving up LLM cost via assistant spam.
**Mitigation**: rate limiting per user/IP tuned per endpoint sensitivity
(rate-limiting.md), CAPTCHA or equivalent on repeated OTP requests, cost
and request-volume alerting on the assistant endpoint.

## 13. Insider misuse
**Impact**: a staff member with legitimate access (admin, agent) browses or
exports citizen data without a business reason.
**Mitigation**: audit logging of all sensitive-data access (not just
mutations), anomaly alerting (security-architecture.md §4), least-privilege
role scoping, case notes and agent actions attributable to a specific
account (no shared credentials).

## Note

All mitigations listed here must be implemented and tested, not merely
documented — each maps to a concrete control in security-architecture.md
and, where applicable, a test in testing/security-testing.md. A threat
entry without a corresponding implemented control is an open risk and
should be tracked as such, not treated as closed by virtue of being
written down.
