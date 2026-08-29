# CivicLens — Master Gap Register

This document maintains the canonical gap register tracking all requirements, verification states, and remediation status across the CivicLens codebase.

---

| ID | Area | Requirement | Current Implementation | Evidence | Severity | Status | Fix | Regression Test |
|---|---|---|---|---|---|---|---|---|
| GAP-001 | Infrastructure | Multi-node Redis fallback handling | Single-node fallback active in dev | `app/core/config.py` | LOW | PROVIDER-DEPENDENT | Configured optional Redis connection wrapper with in-memory fallback | `test_reliability_suite.py` |
| GAP-002 | Integrations | External SMS/Email provider sandbox | Mock providers used in local dev | `app/modules/notifications/` | MEDIUM | PROVIDER-DEPENDENT | Implemented configurable SMS/Email gateway interfaces | `test_integration_notifications.py` |
| GAP-003 | AI | LLM Policy grounding verification | Prompt injection isolated with `<untrusted_context>` | `app/modules/knowledge/assistant.py` | MEDIUM | COMPLETE | Enforced AST validation & non-authoritative AI boundaries | `test_integration_assistant.py` |
| GAP-004 | Security | Four-Eyes Governance for Scheme publishing | Implemented server-side check preventing self-approval | `app/modules/schemes/service.py` | HIGH | COMPLETE | Enforced `creator_id != reviewer_id` on publish | `test_security_suite.py` |
| GAP-005 | Security | Magic Bytes Header Document Inspection | Validates `%PDF-`, `\x89PNG`, `\xFF\xD8` headers | `app/modules/documents/service.py` | HIGH | COMPLETE | Added header magic byte check before OCR processing | `test_security_documents.py` |
| GAP-006 | Governance | Application State Machine illegal transition rejection | Strict DB-level enum and transition map enforced | `app/modules/applications/service.py` | CRITICAL | COMPLETE | Implemented atomic state transition state machine with row locks | `test_unit_application_state_machine.py` |
| GAP-007 | Database | Alembic migration zero-to-head clean execution | 7 migrations executing sequentially without errors | `backend/alembic/versions/` | CRITICAL | COMPLETE | Validated schema generation on fresh PostgreSQL instance | `verify_e2e_p5.py` |

---

## Status Legend
- **COMPLETE**: Fully implemented, verified against source code, database, and test suite.
- **PARTIAL**: Partially implemented with minor pending non-critical enhancements.
- **PROVIDER-DEPENDENT**: Depends on third-party live credentials or environment setup (e.g. production AWS/SMS).
- **BLOCKED**: Implementation blocked by external dependency.
- **NOT IMPLEMENTED**: Feature not currently in codebase.
