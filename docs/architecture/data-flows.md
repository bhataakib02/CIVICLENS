# CivicLens — Data Flow Sequence Specifications

This document details sequence flows across the major platform operations.

---

## 1. Authentication & Session Flow

```mermaid
sequenceDiagram
    autonumber
    actor C as Citizen
    participant API as FastAPI Router
    participant S as AuthService
    participant DB as PostgreSQL
    participant R as Redis

    C->>API: POST /auth/login {email, password}
    API->>S: authenticate_user(email, password)
    S->>DB: Query user record by email
    DB-->>S: User row (Argon2id password_hash)
    S->>S: verify_password(password, password_hash)
    alt Invalid Password
        S-->>C: 401 Unauthorized (INVALID_CREDENTIALS)
    else Valid Password
        S->>S: create_access_token(sub, role)
        S->>S: generate_refresh_token()
        S->>DB: Store hash_refresh_token()
        S-->>C: TokenPair {access_token, refresh_token, expires_in}
    end
```

---

## 2. Deterministic Eligibility Evaluation Flow

```mermaid
sequenceDiagram
    autonumber
    actor C as Citizen
    participant API as FastAPI Router
    participant E as EligibilityService
    participant Ctx as ContextBuilder
    participant Eng as Engine
    participant DB as PostgreSQL

    C->>API: POST /eligibility/check {scheme_version_id}
    API->>E: evaluate_eligibility(citizen_id, scheme_version_id)
    E->>DB: Fetch Citizen Profile, Addresses, & Document Facts
    DB-->>E: Facts data
    E->>Ctx: build(profile, address, doc_facts)
    Ctx-->>E: EvaluationContext
    E->>DB: Load compiled EligibilityRules
    DB-->>E: Rules AST
    E->>Eng: evaluate(compiled_rules, EvaluationContext)
    Eng-->>E: EvaluationResult (Decision: ELIGIBLE / NOT_ELIGIBLE)
    E->>DB: Store EligibilityCheck snapshot
    E-->>C: EligibilityCheckResponse (Decision + Rule Breakdown)
```

---

## 3. Document Upload & Magic Bytes Pipeline

```mermaid
sequenceDiagram
    autonumber
    actor C as Citizen
    participant API as FastAPI Router
    participant Doc as DocumentsService
    participant S3 as AWS S3 Storage
    participant W as Celery OCR Worker

    C->>API: POST /documents/upload-init {document_type, filename, mime_type, size_bytes}
    Doc->>Doc: Validate size <= 10MB and declared MIME
    Doc->>DB: Insert Document record (status=UPLOADING)
    Doc->>S3: Create presigned PUT URL
    Doc-->>C: {upload_url, document_id}
    
    C->>S3: PUT file bytes to presigned URL
    C->>API: POST /documents/{id}/complete
    API->>Doc: complete_upload(document_id)
    Doc->>S3: get_object(storage_key)
    S3-->>Doc: File bytes
    Doc->>Doc: _validate_magic_bytes(data, mime_type)
    Doc->>Doc: Calculate SHA256 & verify size
    Doc->>DB: Update Document (status=UPLOADED) & queue ProcessingJob
    Doc->>W: Enqueue OCR Extraction Task
```

---

## 4. Application Workflow & Outbox Event Flow

```mermaid
sequenceDiagram
    autonumber
    actor C as Citizen
    participant API as FastAPI Router
    participant Workflow as ApplicationWorkflow
    participant DB as PostgreSQL
    participant Outbox as OutboxWriter
    participant W as Celery Worker

    C->>API: POST /applications/{id}/submit
    API->>Workflow: submit(application_id, idempotency_key)
    Workflow->>DB: SELECT FOR UPDATE application row (Locking)
    Workflow->>Workflow: Assert transition DRAFT -> READY -> SUBMISSION_PENDING
    Workflow->>DB: Record ApplicationSubmission & ApplicationStatusHistory
    Workflow->>Outbox: enqueue_simple(APPLICATION_SUBMITTED)
    DB-->>Workflow: Transaction Commit (Atomic)
    Workflow-->>C: Application Response (status=SUBMISSION_PENDING)
    
    Outbox->>W: Process outbox event
    W->>W: Dispatch notification & update status
```
