# CivicLens — Security Architecture

Status: v1.0 draft
Related: threat-model.md, pii-handling.md, document-security.md, authentication-security.md, authorization-model.md, secrets-management.md, rate-limiting.md, audit-logging.md, incident-response.md

## 1. Identity & Access

- **Authentication**: phone+OTP (primary, citizens) or email+password with
  mandatory MFA (staff/admin roles). JWT access tokens (short-lived, ~15
  min) + rotating, revocable refresh tokens (authentication-security.md).
- **Authorization**: role-based (citizen, agent, scheme_admin, admin) at
  the API layer, plus row-level ownership checks (a citizen can only ever
  read/write their own citizen_profile, documents, applications — enforced
  in the service layer, not just the router) (authorization-model.md).
- **Agent-on-behalf-of-citizen** access requires an explicit `consents` row
  scoped to `agent_assist`; the service layer checks for an active consent
  before allowing an agent-authenticated request to touch a citizen's data.

## 2. Data Protection

- TLS 1.2+ everywhere in transit.
- PII columns (see data-dictionary.md) encrypted at rest via
  column-level or transparent database encryption, per
  pii-handling.md.
- Documents live in access-controlled object storage; every fetch goes
  through the API, which issues short-lived pre-signed URLs after an
  authorization check — objects are never public or predictably-keyed
  (document-security.md, addressing "cross-user document access" in
  threat-model.md).
- Secrets (DB credentials, API keys, signing keys) live in a managed
  secrets store, never in source control or plain environment files
  committed to the repo (secrets-management.md).

## 3. Application-Layer Controls

- Input validation via Pydantic schemas at every API boundary; the
  eligibility rule DSL is a closed grammar with no code execution
  (rule-dsl.md, ADR-008) — this is itself a security control, not just a
  modeling choice.
- Rate limiting per user/IP on auth endpoints (OTP request/verify) and on
  the assistant endpoint (cost + abuse control) (rate-limiting.md).
- File upload validation: type/size limits, malware scanning before a
  document reaches the OCR pipeline or is persisted long-term
  (document-security.md).
- Prompt-injection defenses on the RAG pipeline: retrieved government
  document content is treated as untrusted data, never as instructions —
  the system prompt structure keeps retrieved content in a clearly
  delimited "context" role the model is instructed not to treat as
  commands (ai/ai-safety.md, ai/hallucination-controls.md).

## 4. Audit & Detection

- Every state-changing action on sensitive entities (scheme_version
  publish, eligibility rule change, application status transition, admin
  access to a citizen's documents) writes an immutable `audit_logs` row
  (audit-logging.md).
- Alerting on anomalous access patterns (e.g., one agent account touching
  an unusually large number of distinct citizen profiles in a short
  window) — see operations/alerting.md.

## 5. Incident Response

See incident-response.md for the runbook. Summary: defined severity tiers,
on-call escalation, mandatory breach-notification timeline aligned to DPDP
Act obligations, and a post-incident review requirement for any Sev1/Sev2.

## 6. Security Review Gate

Per NFR-SEC-4, an independent security review / penetration test is
required before the system processes real citizen documents in production.
CI also runs automated security testing (SAST, dependency scanning) on
every merge — see testing/security-testing.md and
infrastructure/ci-cd.md.

## 7. Relationship to the Threat Model

This document describes controls; threat-model.md enumerates the specific
threats each control is designed to mitigate. Every threat in
threat-model.md must map to at least one control here — an unmapped threat
is an open risk, not something to leave implicit.
