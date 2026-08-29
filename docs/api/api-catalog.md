# CivicLens — OpenAPI Endpoint Catalog

This document indexes all 11 router modules matching the canonical `openapi.yaml` specification.

---

## Endpoint Catalog

### Authentication (`/api/v1/auth`)
- `POST /auth/register`: Register a new citizen or agent user account.
- `POST /auth/login`: Authenticate email + password, returning JWT access token & opaque refresh token.
- `POST /auth/refresh`: Exchange a valid refresh token for a new access token.
- `POST /auth/logout`: Revoke active refresh token.
- `POST /auth/otp/request`: Request an OTP for phone authentication.
- `POST /auth/otp/verify`: Verify an OTP code and issue tokens.

### Citizen Profile (`/api/v1/me`)
- `GET /me`: Get current principal metadata.
- `GET /me/profile`: Retrieve citizen profile details.
- `PUT /me/profile`: Update progressive citizen profile fields.
- `GET /me/addresses`: List citizen addresses.
- `POST /me/addresses`: Add a new address.

### Agent Consents (`/api/v1/consents` & `/api/v1/me/consents`)
- `POST /me/consents`: Grant an agent assistance consent token.
- `GET /me/consents`: List granted consents.
- `POST /consents/verify`: Verify an active consent token for an agent operator.

### Schemes & Rules (`/api/v1/schemes` & `/api/v1/admin`)
- `GET /schemes`: Browse and search scheme catalog (paginated).
- `GET /schemes/{id}`: Get scheme detail and current published version.
- `POST /schemes`: Create a scheme (Admin).
- `POST /schemes/{id}/versions`: Create a draft scheme version (Admin).
- `POST /admin/scheme-versions/{id}/publish`: Publish a scheme version (Enforces Four-Eyes rule).
- `POST /scheme-versions/{id}/rules`: Set AST rules for a draft version (Admin).

### Eligibility Engine (`/api/v1/eligibility` & `/api/v1/admin`)
- `POST /eligibility/check`: Run deterministic eligibility check for a scheme.
- `POST /eligibility/check-all`: Check citizen eligibility against all active published schemes.
- `POST /admin/eligibility/simulate`: Simulate rule outcomes against synthetic profile facts (Admin).

### Documents (`/api/v1/documents`)
- `POST /documents`: Direct multipart upload convenience endpoint.
- `POST /documents/upload-init`: Initialize upload and request presigned S3 PUT URL.
- `POST /documents/{id}/complete`: Complete upload, triggering magic byte validation and OCR worker.
- `GET /documents`: List citizen documents.
- `GET /documents/{id}/download`: Request short-lived signed S3 GET URL.
- `DELETE /documents/{id}`: Soft-delete document record & purge private S3 object.

### Applications (`/api/v1/applications`)
- `POST /applications`: Create draft application with eligibility snapshot.
- `GET /applications`: List citizen/agent applications.
- `GET /applications/{id}`: Get application detail & checklist.
- `POST /applications/{id}/submit`: Submit application to government workflow.
- `PATCH /admin/applications/{id}/status`: Transition application status (Admin/Agent).

### RAG Assistant & Knowledge (`/api/v1/assistant` & `/api/v1/admin`)
- `POST /assistant/query`: Query AI assistant for scheme guidance and grounded vector citations.
- `GET /admin/knowledge/sources`: List knowledge sources.
- `POST /admin/knowledge/sources`: Ingest official government publication source.

### Notifications (`/api/v1/notifications`)
- `GET /notifications`: List in-app notifications.
- `PATCH /notifications/{id}/read`: Mark notification as read.
- `WS /ws/notifications`: Realtime WebSocket event stream.

### Health & Monitoring (`/api/v1/health`)
- `GET /health`: Liveness probe.
- `GET /health/ready`: Readiness probe (validates DB & Redis connectivity).
