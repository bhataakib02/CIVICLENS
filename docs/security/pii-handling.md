# PII Handling

Status: v1.0 draft
Related: security-architecture.md, threat-model.md, database/data-dictionary.md, data-protection.md

## 1. What Counts as PII in CivicLens

Every column flagged **PII** in `database/data-dictionary.md`:
`users.phone_number`, `users.email`, `citizen_profiles.date_of_birth`,
`citizen_profiles.declared_annual_income`,
`citizen_profile_versions.snapshot`, `addresses.line1`,
`document_extractions.extracted_fields`, plus the raw document files
themselves (document-security.md). This list is the schema's source of
truth — a new column is not exempt from these rules just because it was
added later; PII classification is a required step in schema-change review.

## 2. Handling Rules

- **At rest**: PII columns are encrypted at the storage layer (see
  data-protection.md). Document files live in access-controlled object
  storage, never the database (ADR-005).
- **In transit**: TLS 1.2+ everywhere, no exceptions for internal
  service-to-service calls.
- **In logs**: a redaction middleware strips or hashes known PII field
  names/patterns before any log line is emitted; PII must never appear in
  application logs, error traces, or analytics events in plaintext
  (NFR-PRIV-2). This is tested in security-testing.md.
- **In caches**: eligibility result caching (Redis) stores only
  non-identifying keys (profile_version_no + scheme_version_id) and
  computed results, never raw PII values.
- **In prompts sent to the LLM**: only the minimum profile fields needed
  for the current task are included in any prompt (e.g., structured
  extraction, RAG context); raw documents are never sent to the LLM
  unmodified — extraction happens via the OCR pipeline first.

## 3. Consent & Purpose Limitation

Every use of PII maps to a `consents` scope (FR-CONSENT-1): agent
assistance, document processing, or portal export. Data is not used for a
purpose outside its consented scope — e.g., income data collected for
eligibility screening is not repurposed for marketing without separate
consent (CivicLens does not do marketing use of PII in v1.0 at all).

## 4. Right to Erasure & Correction (DPDP Act)

- A citizen can request correction of any profile field directly
  (FR-PROFILE-3).
- A citizen can request deletion of their account and PII. Deletion
  anonymizes `citizen_profiles`/`addresses`/`documents` (nulling PII
  columns, retaining non-PII structural rows) rather than hard-deleting
  `applications`/`audit_logs`/`eligibility_checks`, which persist under
  statutory retention requirements for submitted government applications
  (retention-policy.md) — this tension is intentional and documented, not
  an oversight.
- Deletion/anonymization requests are themselves audit-logged.

## 5. Minimization

Profile collection is incremental (FR-PROFILE-2) precisely so PII
collection stays scoped to what's needed to answer the citizen's current
question, rather than front-loading a maximal data grab.
