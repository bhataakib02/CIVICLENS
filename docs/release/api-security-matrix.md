# CivicLens — API Security & Authorization Matrix

This document maps every production endpoint in FastAPI to its authentication requirements, role authorization, object-level authorization (IDOR protection), rate limiting policy, and audit trail generation.

---

## API Security Matrix

| Endpoint Route | Auth Required | Required Role | Object-Level Authorization (IDOR) | Rate Limit | Audit Trail Logged |
|---|---|---|---|---|---|
| `POST /auth/register` | No | Anonymous | N/A | 10 req/min | Yes (`AUTH_REGISTER`) |
| `POST /auth/login` | No | Anonymous | N/A | 5 req/min | Yes (`AUTH_LOGIN`) |
| `POST /auth/otp/request` | No | Anonymous | Phone Number Scope | 3 req/min | Yes (`OTP_REQUEST`) |
| `POST /auth/otp/verify` | No | Anonymous | OTP Session Hash | 5 req/min | Yes (`OTP_VERIFY`) |
| `GET /me/profile` | Yes | Citizen / Agent | `current_user.id == profile.user_id` | 100 req/min | No |
| `PUT /me/profile` | Yes | Citizen / Agent | `current_user.id == profile.user_id` | 30 req/min | Yes (`PROFILE_UPDATE`) |
| `POST /me/consents` | Yes | Citizen | `current_user.id == profile.user_id` | 20 req/min | Yes (`CONSENT_GRANT`) |
| `POST /consents/verify` | Yes | Agent | Active Consent Token Verification | 50 req/min | Yes (`CONSENT_VERIFY`) |
| `GET /schemes` | Optional | Any | Public Catalog | 200 req/min | No |
| `POST /schemes` | Yes | Admin / Scheme Admin | Admin Role Check | 20 req/min | Yes (`SCHEME_CREATE`) |
| `POST /admin/scheme-versions/{id}/publish` | Yes | Admin / Scheme Admin | **Four-Eyes Enforcement**: `created_by != actor_id` | 10 req/min | Yes (`SCHEME_PUBLISH`) |
| `POST /eligibility/check` | Yes | Citizen / Agent | `profile_id == current_user_profile_id` | 60 req/min | Yes (`ELIGIBILITY_CHECK`) |
| `POST /documents/upload-init` | Yes | Citizen / Agent | Owner Profile Scope + Magic Bytes Header | 30 req/min | Yes (`DOCUMENT_UPLOAD_INIT`) |
| `GET /documents/{id}/download` | Yes | Citizen / Agent | Owner Check / Active Consent Check | 60 req/min | Yes (`DOCUMENT_DOWNLOAD`) |
| `POST /applications/{id}/submit` | Yes | Citizen / Agent | `application.citizen_id == current_profile_id` | 10 req/min | Yes (`APPLICATION_SUBMIT`) |
| `POST /assistant/query` | Yes | Citizen / Agent | Citizen Session Scope | 30 req/min | Yes (`AI_QUERY`) |
