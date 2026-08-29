# CivicLens — Database Design & Schema ERD

This document specifies the PostgreSQL relational schema, indexes, constraints, and entity-relationship diagram.

---

## Entity-Relationship Diagram (ERD)

```mermaid
erDiagram
    users ||--o| citizen_profiles : owns
    users ||--o{ refresh_tokens : has
    users ||--o{ audit_logs : generates
    
    citizen_profiles ||--o{ addresses : lives_at
    citizen_profiles ||--o{ citizen_profile_versions : snapshot
    citizen_profiles ||--o{ consent_records : grants
    citizen_profiles ||--o{ documents : uploads
    citizen_profiles ||--o{ applications : submits
    
    schemes ||--o{ scheme_versions : versions
    scheme_versions ||--o{ eligibility_rules : contains
    scheme_versions ||--o{ document_requirements : requires
    
    applications ||--o{ application_status_history : tracks
    applications ||--o{ application_submissions : records
    applications ||--o{ application_documents : attaches
    
    documents ||--o{ document_extractions : extracts
    documents ||--o{ document_verifications : verifies
    
    knowledge_sources ||--o{ knowledge_chunks : chunks
```

---

## Production Tables Summary

1. `users`: Core account identity, Argon2id `password_hash`, role (`citizen`, `agent`, `scheme_admin`, `admin`), status.
2. `citizen_profiles`: Demographics, `declared_annual_income`, `family_size`, disability status, profile completeness score.
3. `addresses`: State, district, pincode, line1, `is_primary` flag.
4. `schemes` & `scheme_versions`: Scheme metadata, effective date ranges, version status (`DRAFT`, `IN_REVIEW`, `PUBLISHED`, `SUPERSEDED`).
5. `eligibility_rules`: AST rule conditions, field keys, operators, values, parent group IDs, mandatory flags.
6. `applications`: `application_number`, status, eligibility snapshot JSON, deadline timestamps.
7. `documents`: Storage key, filename, mime type, size, SHA256 checksum, upload status.
8. `knowledge_chunks`: Text passages, section headings, HNSW vector embeddings (`pgvector`).
9. `outbox_events` & `notifications`: Transactional outbox event queue and notification feed.
