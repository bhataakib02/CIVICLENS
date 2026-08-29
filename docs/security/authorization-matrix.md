# CIVICLENS AUTHORIZATION MATRIX

**Version:** v1.0.0-rc.2  
**Date:** 2026-08-29  

---

## Endpoint RBAC & Scope Permissions

| Endpoint Path | HTTP Method | Citizen | Agent | Scheme Admin | Admin | Auth Requirement |
|:---|:---:|:---:|:---:|:---:|:---:|:---|
| `/api/v1/auth/otp/request` | POST | Public | Public | Public | Public | Unauthenticated |
| `/api/v1/auth/otp/verify` | POST | Public | Public | Public | Public | Unauthenticated |
| `/api/v1/citizens/profile` | GET / PUT | Allowed (Self) | Allowed (With Consent) | Denied | Denied | Bearer JWT (Scope: `profile:read/write`) |
| `/api/v1/schemes` | GET | Allowed | Allowed | Allowed | Allowed | Bearer JWT |
| `/api/v1/schemes` | POST | Denied | Denied | Allowed | Allowed | Bearer JWT (Role: `scheme_admin`, `admin`) |
| `/api/v1/schemes/{id}/publish` | POST | Denied | Denied | Allowed (Four-eyes check) | Allowed (Four-eyes check) | Bearer JWT (`author_id != reviewer_id`) |
| `/api/v1/eligibility/evaluate` | POST | Allowed (Self) | Allowed (Assisted) | Denied | Denied | Deterministic Rule Engine |
| `/api/v1/documents/upload` | POST | Allowed | Allowed | Denied | Denied | Magic-byte & MIME check, scan |
| `/api/v1/applications` | POST | Allowed | Allowed | Denied | Denied | Idempotency Key required |
| `/api/v1/applications/{id}/review` | POST | Denied | Allowed | Denied | Allowed | Role: `agent`, `admin` |
| `/api/v1/audit/logs` | GET | Denied | Denied | Denied | Allowed | Role: `admin` |
| `/api/v1/system/health` | GET | Public | Public | Public | Public | Public Readiness check |

---

## Security Invariants

1. **Consent-Gated Agent Access:** Agents attempting to view Citizen PII without active, unexpired, matching consent receive `403 Forbidden` (`CONSENT_REQUIRED`).
2. **Four-Eyes Scheme Approval:** The creator of a scheme version (`author_id`) cannot approve or publish their own version (`403 Forbidden: FOUR_EYES_VIOLATION`).
3. **Immutability of Published Schemes:** Once a scheme version moves to `PUBLISHED`, direct mutations are rejected; new revisions require creating a `DRAFT` version.
4. **Idempotent Application Submission:** Application submissions require an `X-Idempotency-Key` header to prevent duplicate application state creation.
