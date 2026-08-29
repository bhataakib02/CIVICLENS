# CivicLens — Entity Relationship Diagram

Status: v1.0 draft
Related: database-design.md, data-dictionary.md

This is the authoritative ERD. `backend/app/db` SQLAlchemy models and
Alembic migrations must match this diagram; any drift is a bug, not a
documentation lag (see database-design.md §2).

```mermaid
erDiagram
    USERS ||--o| CITIZEN_PROFILES : has
    USERS ||--o{ CONSENTS : grants
    CITIZEN_PROFILES ||--o{ CITIZEN_PROFILE_VERSIONS : "versioned by"
    CITIZEN_PROFILES ||--o{ ADDRESSES : has
    CITIZEN_PROFILES ||--o{ DOCUMENTS : uploads
    CITIZEN_PROFILES ||--o{ ELIGIBILITY_CHECKS : "evaluated for"
    CITIZEN_PROFILES ||--o{ APPLICATIONS : submits
    CITIZEN_PROFILES ||--o{ NOTIFICATIONS : receives

    DOCUMENTS ||--o| DOCUMENT_EXTRACTIONS : produces
    DOCUMENTS }o--o{ APPLICATIONS : "attached via application_documents"

    SCHEMES ||--o{ SCHEME_VERSIONS : "versioned by"
    SCHEME_VERSIONS ||--o{ ELIGIBILITY_RULES : defines
    SCHEME_VERSIONS ||--o{ DOCUMENT_REQUIREMENTS : defines
    SCHEME_VERSIONS ||--o{ ELIGIBILITY_CHECKS : "evaluated against"
    SCHEME_VERSIONS ||--o{ APPLICATIONS : "applied under"
    SCHEME_VERSIONS }o--|| KNOWLEDGE_SOURCES : "sourced from"

    KNOWLEDGE_SOURCES ||--o{ KNOWLEDGE_CHUNKS : "chunked into"

    APPLICATIONS ||--o{ APPLICATION_STATUS_HISTORY : tracks
    APPLICATIONS ||--o{ CASE_NOTES : "annotated by"

    USERS ||--o{ AUDIT_LOGS : "acts, logged in"

    USERS {
        uuid id PK
        string phone_number UK
        string email UK
        string password_hash
        string role
        timestamptz created_at
    }

    CITIZEN_PROFILES {
        uuid id PK
        uuid user_id FK
        date date_of_birth
        string gender
        string category
        string occupation
        numeric declared_annual_income
        boolean disability_status
        int family_size
        int current_version_no
        timestamptz updated_at
    }

    CITIZEN_PROFILE_VERSIONS {
        uuid id PK
        uuid citizen_profile_id FK
        int version_no
        jsonb snapshot
        timestamptz created_at
    }

    ADDRESSES {
        uuid id PK
        uuid citizen_profile_id FK
        string type
        string state
        string district
        string pincode
        string line1
    }

    CONSENTS {
        uuid id PK
        uuid user_id FK
        string scope
        boolean granted
        timestamptz granted_at
        timestamptz revoked_at
    }

    SCHEMES {
        uuid id PK
        string canonical_name
        string category
        string administering_dept
        string scope
        timestamptz created_at
    }

    SCHEME_VERSIONS {
        uuid id PK
        uuid scheme_id FK
        int version_no
        string status
        text benefits_summary
        date effective_from
        date effective_to
        uuid knowledge_source_id FK
        timestamptz published_at
    }

    ELIGIBILITY_RULES {
        uuid id PK
        uuid scheme_version_id FK
        string field_key
        string operator
        jsonb value
        string group_id
        text explanation_text
    }

    DOCUMENT_REQUIREMENTS {
        uuid id PK
        uuid scheme_version_id FK
        string document_type
        boolean is_mandatory
        text notes
    }

    KNOWLEDGE_SOURCES {
        uuid id PK
        string title
        string url
        string publisher
        date published_date
        string ingestion_status
        timestamptz last_verified_at
    }

    KNOWLEDGE_CHUNKS {
        uuid id PK
        uuid knowledge_source_id FK
        text content
        vector embedding
        int page_number
        int char_start
        int char_end
    }

    DOCUMENTS {
        uuid id PK
        uuid citizen_profile_id FK
        string document_type
        string storage_key
        string status
        timestamptz uploaded_at
    }

    DOCUMENT_EXTRACTIONS {
        uuid id PK
        uuid document_id FK
        jsonb extracted_fields
        numeric confidence
        boolean verified_by_citizen
        timestamptz extracted_at
    }

    ELIGIBILITY_CHECKS {
        uuid id PK
        uuid citizen_profile_id FK
        int profile_version_no
        uuid scheme_version_id FK
        string result
        jsonb rule_breakdown
        timestamptz computed_at
    }

    APPLICATIONS {
        uuid id PK
        uuid citizen_profile_id FK
        uuid scheme_version_id FK
        string status
        jsonb scheme_specific_answers
        timestamptz created_at
        timestamptz submitted_at
    }

    APPLICATION_STATUS_HISTORY {
        uuid id PK
        uuid application_id FK
        string from_status
        string to_status
        uuid actor_user_id FK
        text note
        timestamptz created_at
    }

    NOTIFICATIONS {
        uuid id PK
        uuid citizen_profile_id FK
        string channel
        string category
        string status
        timestamptz sent_at
    }

    AUDIT_LOGS {
        uuid id PK
        uuid actor_user_id FK
        string action
        string entity_type
        uuid entity_id
        jsonb diff
        timestamptz created_at
    }

    CASE_NOTES {
        uuid id PK
        uuid application_id FK
        uuid author_user_id FK
        text note
        timestamptz created_at
    }
```

## Notes on relationships not fully expressible in the diagram

- `applications` ↔ `documents` is many-to-many through an
  `application_documents` join table (which document instances were
  attached to which application) — omitted above for diagram readability,
  documented fully in data-dictionary.md.
- `eligibility_rules.group_id` supports nested AND/OR rule groups (see
  ai/rule-dsl.md) — the DSL structure, not the flat table, is the actual
  logical grouping; the table is a normalized encoding of the DSL AST.
