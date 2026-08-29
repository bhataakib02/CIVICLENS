# CivicLens — Security Scorecard

Status: Baseline Security Assessment (Prompt 11 Audit)

| Domain | Status | Rating Criteria | Key Mitigations Implemented |
|---|---|---|---|
| **Authentication** | **GREEN** | Robust multi-factor / OTP validation, rate-limited login, Argon2id hashing, timing attack protection. | Opaque tokens, sliding window rate limits, enumeration prevention. |
| **Authorization** | **GREEN** | Role-based & ownership checks enforced at service layer; IDOR/BOLA protected; Four-Eyes publish rule enforced. | Row-level `citizen_profile_id` check, mandatory `author != reviewer` assertion on scheme publish. |
| **Data Protection** | **GREEN** | S3 server-side encryption, private buckets, short-lived signed URLs, PII redaction layer in logs. | Pre-signed URL expiry, field-level log scrubbing. |
| **Document Security** | **GREEN** | Magic byte validation, filename sanitization, isolated OCR worker context, fail-closed malware handling. | Safe processing, path traversal protection, MIME check. |
| **AI & RAG Security** | **GREEN** | Strict prompt injection isolation (`<untrusted_context>`), typed Pydantic validation, deterministic eligibility routing. | Delimited prompt structure, validation retries, no LLM state mutation. |
| **API Security** | **GREEN** | Parameterized SQL query execution (SQLAlchemy), strict schema extra attribute rejection, bound pagination limits. | `ConfigDict(extra="forbid")`, pagination max bounds (100). |
| **Infrastructure Security** | **GREEN** | Private subnets for RDS & Redis, Security Groups least privilege, non-root containers. | VPC isolation, HSTS / Security Headers. |
| **CI/CD Security** | **GREEN** | Fork PR credential isolation, pinned actions, dependency vulnerability checks. | GitHub Actions security configuration. |
| **Observability** | **GREEN** | Structured JSON logging, redacting PII, transactional outbox auditing. | Audit trail for all sensitive operations. |
| **Privacy & PII** | **GREEN** | PII minimization across endpoints, masking sensitive identity attributes. | Consent-bound agent scope, minimal payload design. |
| **Dependency Security** | **GREEN** | Automated vulnerability scans, standard locked dependency trees. | Clean dependency manifests. |
