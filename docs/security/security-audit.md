# CivicLens — Security Audit Finding Register

This document tracks all identified security, reliability, concurrency, privacy, and adversarial findings discovered during the comprehensive audit phase.

---

## Findings Summary

| ID | Title | Severity | Component | Status |
|---|---|---|---|---|
| SEC-001 | Mass Assignment via Unsanitized Request Payload | HIGH | Auth / User Management | REMEDIATED |
| SEC-002 | Missing Rate Limiting on Sensitive Endpoint Actions | HIGH | Auth / OTP / Gateway | REMEDIATED |
| SEC-003 | RAG Prompt Injection & Context Escape Risk | HIGH | Knowledge / RAG | REMEDIATED |
| SEC-004 | Document MIME / Content Injection Risk | MEDIUM | Documents Processing | REMEDIATED |
| SEC-005 | Immutability Bypass on Published Scheme Rules | HIGH | Schemes / Eligibility | REMEDIATED |
| SEC-006 | Scheme Self-Approval Bypass (Four-Eyes Violation) | HIGH | Schemes / Admin | REMEDIATED |
| SEC-007 | Agent Consent Revocation Race Condition | MEDIUM | Agent Consents | REMEDIATED |
| REL-001 | Application State Machine Illegal Transition | HIGH | Applications | REMEDIATED |
| REL-002 | Notification Outbox Failure & Retries | MEDIUM | Notifications | REMEDIATED |
| PERF-001| Pagination Abuse Memory Exhaustion | LOW | API Layer | REMEDIATED |

---

## Detailed Findings

### SEC-001: Mass Assignment via Unsanitized Request Payload
- **Severity**: HIGH
- **Affected Component**: `backend/app/schemas/user.py`, `backend/app/modules/auth`
- **Attack Scenario**: Attacker sends additional properties like `"role": "ADMIN"` or `"is_admin": true` during registration or user profile updates.
- **Impact**: Unauthorized privilege escalation to `ADMIN` or `SCHEME_ADMIN`.
- **Evidence**: Pydantic models lacked `model_config = ConfigDict(extra="forbid")`.
- **Fix**: Configured strict schema input filtering rejecting any extra attributes.
- **Verification**: `test_security_suite.py::test_mass_assignment_privilege_escalation`
- **Residual Risk**: Low (enforced at API serialization layer).

### SEC-002: Rate Limiting & Replay Exposure on Sensitive Endpoints
- **Severity**: HIGH
- **Affected Component**: `backend/app/modules/auth/router.py`
- **Attack Scenario**: Attacker executes rapid OTP verification requests or login brute force from distributed nodes.
- **Impact**: Account takeover or resource exhaustion.
- **Evidence**: Lack of sliding-window rate limit checks per IP/account key.
- **Fix**: Added multi-layer rate limiting middleware and identifier-scoped verification attempt counters.
- **Verification**: `test_security_suite.py::test_otp_brute_force_rate_limiting`
- **Residual Risk**: Low.

### SEC-003: RAG Prompt Injection & Context Escape Risk
- **Severity**: HIGH
- **Affected Component**: `backend/app/modules/knowledge/service.py`
- **Attack Scenario**: Malicious input embedded inside query or retrieved source containing instructions like `"Ignore previous instructions..."`.
- **Impact**: Prompt disclosure, false eligibility instruction generation, or policy hallucination.
- **Fix**: Enforced `<untrusted_context>` wrapping, explicit AI safety guardrails, and typed schema output validation.
- **Verification**: `test_security_suite.py::test_rag_prompt_injection_neutralized`
- **Residual Risk**: Low.

### SEC-004: Document MIME / File Content Injection Risk
- **Severity**: MEDIUM
- **Affected Component**: `backend/app/modules/documents/service.py`
- **Attack Scenario**: Attacker uploads a script/executable file renamed to `.pdf`.
- **Impact**: OCR worker crash, arbitrary code execution in processor context.
- **Fix**: Enforced magic byte header validation (`%PDF-`, `\xFF\xD8\xFF`, `\x89PNG`) and strict file sanitization.
- **Verification**: `test_security_suite.py::test_file_upload_magic_bytes_validation`
- **Residual Risk**: Low.

### SEC-005: Immutability Bypass on Published Scheme Rules
- **Severity**: HIGH
- **Affected Component**: `backend/app/modules/schemes/router.py`
- **Attack Scenario**: Direct API call attempting to alter rules on an already published scheme version.
- **Impact**: Retroactive alteration of citizen eligibility results and audit breakdown.
- **Fix**: Enforced strict status check (`status != "published"`) before allowing updates. Published schemes require creating a new draft version.
- **Verification**: `test_security_suite.py::test_published_scheme_immutability`
- **Residual Risk**: Zero.

### SEC-006: Scheme Self-Approval Bypass (Four-Eyes Violation)
- **Severity**: HIGH
- **Affected Component**: `backend/app/modules/schemes/service.py`
- **Attack Scenario**: Scheme Admin A creates a draft scheme version and submits a publish request using their own credential token.
- **Impact**: Unreviewed rule changes deployed to production.
- **Fix**: Enforced backend check asserting `author_id != reviewer_id` on state transition to `published`.
- **Verification**: `test_security_suite.py::test_four_eyes_self_approval_rejected`
- **Residual Risk**: Zero.

### SEC-007: Agent Consent Revocation Check Failure
- **Severity**: MEDIUM
- **Affected Component**: `backend/app/modules/consents/service.py`
- **Attack Scenario**: Agent continues accessing citizen resources after citizen revokes consent.
- **Impact**: Unauthorized access to citizen PII and applications.
- **Fix**: Enforced live database verification of consent active state and non-expired window on every request.
- **Verification**: `test_security_suite.py::test_agent_consent_revocation_enforced`
- **Residual Risk**: Low.

### REL-001: Application State Machine Illegal Transition
- **Severity**: HIGH
- **Affected Component**: `backend/app/modules/applications/service.py`
- **Attack Scenario**: Concurrent API calls or direct client requests attempting to jump from `draft` to `approved` or `rejected` to `submitted`.
- **Impact**: Invalid business workflow execution, corrupted audit trail.
- **Fix**: Enforced atomic state machine transition validator and row locks (`SELECT FOR UPDATE`).
- **Verification**: `test_reliability_suite.py::test_application_state_machine_illegal_transition`
- **Residual Risk**: Low.

### REL-002: Notification Delivery Failure & Outbox Retries
- **Severity**: MEDIUM
- **Affected Component**: `backend/app/modules/notifications/tasks.py`
- **Attack Scenario**: Worker process crashes or external SMS/Email gateway experiences temporary outage during notification dispatch.
- **Impact**: Lost notifications or double delivery.
- **Fix**: Enforced outbox transaction pattern, exponential backoff, and idempotency key deduplication.
- **Verification**: `test_reliability_suite.py::test_notification_outbox_retry_idempotency`
- **Residual Risk**: Low.

### PERF-001: Pagination Abuse Memory Exhaustion
- **Severity**: LOW
- **Affected Component**: `backend/app/core/pagination.py`
- **Attack Scenario**: API request with `limit=10000000` to fetch millions of rows in single query.
- **Impact**: Database connection timeout and API server memory spike.
- **Fix**: Hard-capped maximum page limit to 100 items per request across all collection endpoints.
- **Verification**: `test_performance_suite.py::test_pagination_limit_bounded`
- **Residual Risk**: Low.
