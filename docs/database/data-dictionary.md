# CivicLens — Data Dictionary

Status: v1.0 draft
Related: database-design.md, erd.md, security/pii-handling.md

Legend: **PII** = column requires encryption-at-rest + redaction from logs
per `security/pii-handling.md`. **Immutable** = never updated after insert.

## users
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| phone_number | varchar, unique | **PII** |
| email | varchar, unique, nullable | **PII** |
| password_hash | varchar, nullable | null if phone+OTP only account |
| role | enum(citizen, agent, scheme_admin, admin) | |
| created_at | timestamptz | |

## citizen_profiles
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| user_id | uuid FK → users, unique | 1:1 with users |
| date_of_birth | date | **PII** |
| gender | varchar | |
| category | varchar | caste/social category, used in eligibility rules |
| occupation | varchar | |
| declared_annual_income | numeric | **PII**, self-declared, distinct from document-verified income |
| disability_status | boolean | |
| family_size | int | |
| current_version_no | int | denormalized pointer to latest citizen_profile_versions row |
| updated_at | timestamptz | |

## citizen_profile_versions
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| citizen_profile_id | uuid FK | |
| version_no | int | monotonic per profile |
| snapshot | jsonb | **PII** (full profile snapshot), **Immutable** |
| created_at | timestamptz | |

## addresses
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| citizen_profile_id | uuid FK | |
| type | enum(permanent, current) | |
| state | varchar | used directly in eligibility rules (state-scoped schemes) |
| district | varchar | |
| pincode | varchar(6) | |
| line1 | text | **PII** |

## consents
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| user_id | uuid FK | |
| scope | enum(agent_assist, document_processing, portal_export) | |
| granted | boolean | |
| granted_at | timestamptz | |
| revoked_at | timestamptz, nullable | |

## schemes
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| canonical_name | varchar | stable identity across versions |
| category | varchar | education/health/agriculture/... |
| administering_dept | varchar | |
| scope | enum(central, state) | |
| created_at | timestamptz | |

## scheme_versions
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| scheme_id | uuid FK | |
| version_no | int | monotonic per scheme |
| status | enum(draft, in_review, published, superseded, archived) | |
| benefits_summary | text | |
| effective_from | date | |
| effective_to | date, nullable | null = currently effective |
| knowledge_source_id | uuid FK | provenance |
| published_at | timestamptz, nullable | |

## eligibility_rules
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| scheme_version_id | uuid FK | |
| field_key | varchar | maps to a citizen_profile / address field |
| operator | enum(eq, neq, gt, gte, lt, lte, in, not_in, exists, between) | |
| value | jsonb | operand(s) |
| group_id | varchar | groups rules into AND/OR nodes (see ai/rule-dsl.md) |
| explanation_text | text | citizen-facing plain-language rendering of this rule |

## document_requirements
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| scheme_version_id | uuid FK | |
| document_type | varchar | enumerated document type (see documents.document_type) |
| is_mandatory | boolean | |
| notes | text | |

## knowledge_sources
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| title | varchar | |
| url | text | |
| publisher | varchar | e.g. "Ministry of Rural Development" |
| published_date | date | |
| ingestion_status | enum(pending, ingested, failed, stale) | |
| last_verified_at | timestamptz | drives knowledge staleness alerting |

## knowledge_chunks
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| knowledge_source_id | uuid FK | |
| content | text | |
| embedding | vector(1536) | pgvector column, dimension per embedding model in use |
| page_number | int, nullable | |
| char_start | int | source-span offset, for exact citation |
| char_end | int | |

## documents
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| citizen_profile_id | uuid FK | |
| document_type | enum(aadhaar, income_certificate, residence_proof, caste_certificate, disability_certificate, other) | |
| storage_key | varchar | object storage key, **never a public URL** |
| status | enum(uploaded, processing, verified, rejected) | |
| uploaded_at | timestamptz | |

## document_extractions
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| document_id | uuid FK | |
| extracted_fields | jsonb | **PII** |
| confidence | numeric(3,2) | 0.00–1.00 |
| verified_by_citizen | boolean | citizen confirmed extracted fields (FR-DOCS-3) |
| extracted_at | timestamptz | |

## eligibility_checks
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| citizen_profile_id | uuid FK | |
| profile_version_no | int | snapshot reference, not FK (denormalized for history stability) |
| scheme_version_id | uuid FK | |
| result | enum(eligible, not_eligible, likely_eligible, insufficient_data) | |
| rule_breakdown | jsonb | **Immutable**, per-rule pass/fail/unknown + explanation + citation |
| computed_at | timestamptz | |

## applications
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| citizen_profile_id | uuid FK | |
| scheme_version_id | uuid FK | |
| status | enum(draft, submitted, under_review, info_requested, approved, rejected, withdrawn) | |
| scheme_specific_answers | jsonb | |
| created_at | timestamptz | |
| submitted_at | timestamptz, nullable | |

## application_documents (join table)
| Column | Type | Notes |
|---|---|---|
| application_id | uuid FK | |
| document_id | uuid FK | |
| PRIMARY KEY | (application_id, document_id) | |

## application_status_history
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| application_id | uuid FK | |
| from_status | varchar, nullable | |
| to_status | varchar | |
| actor_user_id | uuid FK | |
| note | text, nullable | |
| created_at | timestamptz | **Immutable** |

## notifications
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| citizen_profile_id | uuid FK | |
| channel | enum(sms, email, in_app) | |
| category | enum(scheme_match, status_change, doc_reverification, deadline_reminder) | |
| status | enum(queued, sent, failed) | |
| sent_at | timestamptz, nullable | |

## audit_logs
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| actor_user_id | uuid FK, nullable | null = system action |
| action | varchar | e.g. "scheme_version.publish" |
| entity_type | varchar | |
| entity_id | uuid | |
| diff | jsonb, nullable | |
| created_at | timestamptz | **Immutable** |

## case_notes
| Column | Type | Notes |
|---|---|---|
| id | uuid PK | |
| application_id | uuid FK | |
| author_user_id | uuid FK | must be role in (agent, admin) |
| note | text | staff-only visibility |
| created_at | timestamptz | |
