# CivicLens — Requirements Traceability Matrix

This matrix maps high-level product requirements across the full implementation stack: Backend Service -> Database Model -> API Endpoint -> Citizen UI -> Admin UI -> Test Suite -> Documentation.

---

## Traceability Mapping

### 1. Citizen Registration & Authentication
- **Backend Service**: `app.modules.auth.service.AuthService`
- **Database Tables**: `users`, `refresh_tokens`, `otp_requests`
- **API Endpoints**: `POST /auth/register`, `POST /auth/login`, `POST /auth/otp/request`, `POST /auth/otp/verify`
- **Citizen UI**: `/login` (Email + OTP login flow)
- **Admin UI**: `/login` (Console credentials login)
- **Test Suite**: `tests/test_integration_auth_flow.py`, `tests/test_security_otp.py`
- **Documentation**: `docs/security/authentication-security.md`

---

### 2. Progressive Citizen Profile & Versioning
- **Backend Service**: `app.modules.citizens.service.CitizensService`
- **Database Tables**: `citizen_profiles`, `citizen_profile_versions`, `addresses`
- **API Endpoints**: `GET /me/profile`, `PUT /me/profile`, `POST /me/addresses`
- **Citizen UI**: `/profile`, `/settings`
- **Admin UI**: `/citizens/[id]`
- **Test Suite**: `tests/test_integration_auth_flow.py`
- **Documentation**: `docs/architecture/system-architecture.md`

---

### 3. Agent Assistance & Consent Scoping
- **Backend Service**: `app.modules.consents.service.ConsentService`
- **Database Tables**: `consent_records`
- **API Endpoints**: `POST /me/consents`, `GET /me/consents`, `POST /consents/verify`
- **Citizen UI**: `/settings` (Consent manager)
- **Admin UI**: `/assisted-citizens` (CSC Operator view)
- **Test Suite**: `tests/test_integration_consents.py`, `tests/test_security_suite.py`
- **Documentation**: `docs/security/authorization-matrix.md`

---

### 4. Scheme Catalog & Four-Eyes Governance
- **Backend Service**: `app.modules.schemes.service.SchemesService`
- **Database Tables**: `schemes`, `scheme_versions`, `eligibility_rules`
- **API Endpoints**: `GET /schemes`, `POST /schemes`, `POST /admin/scheme-versions/{id}/publish`
- **Citizen UI**: `/schemes`, `/schemes/[id]`
- **Admin UI**: `/schemes`, `/schemes/new`, `/schemes/[id]`
- **Test Suite**: `tests/test_integration_schemes_eligibility.py`, `tests/test_security_suite.py`
- **Documentation**: `docs/security/authorization-matrix.md`

---

### 5. Deterministic Eligibility Engine & Simulation
- **Backend Service**: `app.modules.eligibility.engine` & `simulation.RuleSimulationService`
- **Database Tables**: `eligibility_rules`, `eligibility_checks`
- **API Endpoints**: `POST /eligibility/check`, `POST /admin/eligibility/simulate`
- **Citizen UI**: `/eligibility`
- **Admin UI**: `/schemes/[id]/simulate`
- **Test Suite**: `tests/test_unit_engine.py`, `tests/test_performance_suite.py`
- **Documentation**: `docs/architecture/ai-architecture.md`

---

### 6. Document Upload, Magic Bytes & OCR Extraction
- **Backend Service**: `app.modules.documents.service.DocumentsService`
- **Database Tables**: `documents`, `document_processing_jobs`, `document_extractions`
- **API Endpoints**: `POST /documents/upload-init`, `POST /documents/{id}/complete`, `GET /documents/{id}/download`
- **Citizen UI**: `/documents`
- **Admin UI**: `/documents/[id]`
- **Test Suite**: `tests/test_unit_documents.py`, `tests/test_security_suite.py`
- **Documentation**: `docs/architecture/document-intelligence.md`

---

### 7. RAG Knowledge Ingestion & AI Assistant
- **Backend Service**: `app.modules.knowledge.service.KnowledgeService`
- **Database Tables**: `knowledge_sources`, `knowledge_chunks` (pgvector)
- **API Endpoints**: `POST /assistant/query`, `POST /admin/knowledge/sources`
- **Citizen UI**: `/assistant`
- **Admin UI**: `/knowledge`
- **Test Suite**: `tests/test_unit_knowledge.py`, `tests/test_integration_knowledge.py`
- **Documentation**: `docs/architecture/ai-architecture.md`

---

### 8. Application Workflow & State Machine
- **Backend Service**: `app.modules.applications.service.ApplicationsService`
- **Database Tables**: `applications`, `application_status_history`, `application_submissions`
- **API Endpoints**: `POST /applications`, `POST /applications/{id}/submit`, `PATCH /admin/applications/{id}/status`
- **Citizen UI**: `/applications`, `/applications/[id]`
- **Admin UI**: `/applications`, `/applications/[id]`
- **Test Suite**: `tests/test_unit_application_state_machine.py`, `tests/test_reliability_suite.py`
- **Documentation**: `docs/architecture/data-flows.md`

---

### 9. Transactional Outbox & Realtime Eventing
- **Backend Service**: `app.modules.notifications.service` & WebSocket Manager
- **Database Tables**: `outbox_events`, `notifications`, `dead_letter_events`
- **API Endpoints**: `GET /notifications`, `WS /ws/notifications`
- **Citizen UI**: `/notifications` (Live toast & feed)
- **Admin UI**: `/notifications` (System operations log)
- **Test Suite**: `tests/test_unit_notifications.py`, `tests/test_realtime_notifications.py`
- **Documentation**: `docs/architecture/event-driven-system.md`
