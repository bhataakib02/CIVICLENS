# Data Flow

Status: v1.0 draft
Related: system-architecture.md, component-architecture.md §3

## 1. Scheme Discovery Flow

```
Citizen profile fields (client) → PATCH /me → citizen_profiles +
citizen_profile_versions (write)
   → POST /eligibility/check-all → eligibility.service loads active
     scheme_versions + rules, evaluates in-process → eligibility_checks
     (write, cached) → ranked results (response)
```

No AI call on this path — pure deterministic computation
(ai/eligibility-engine.md).

## 2. Document Upload Flow

```
Citizen uploads file → POST /documents (multipart) → documents row
(status=uploaded) → object storage write → job enqueued
   → [async] workers/ocr: OCR → entity-extraction → document_extractions
     (write, verified_by_citizen=false)
   → citizen notified/polls → reviews extracted fields
   → POST /documents/{id}/confirm → document_extractions.verified_by_citizen=true
   → data now usable to pre-fill profile/applications
```

## 3. Assistant Question Flow

```
Citizen message → POST /assistant/messages
   → query intent classification (ai/classification.md)
   → if eligibility-shaped: eligibility.service.evaluate() called as a tool
   → else: hybrid retrieval over knowledge_chunks (ai/retrieval-pipeline.md)
   → generation with citation verification (ai/hallucination-controls.md)
   → response (answer + citations [+ eligibility_tool_calls])
```

## 4. Application Submission Flow

```
POST /applications → checks current eligibility + required documents →
applications row (draft) + application_status_history (initial entry)
   → citizen completes scheme-specific answers + attaches verified documents
   → POST /applications/{id}/submit → completeness validation →
     status: submitted → application_status_history (write)
   → notification enqueued (workers/notifications) → SMS/in-app delivered
```

## 5. Knowledge Ingestion Flow

```
Admin registers knowledge_source (vetted publisher) → ingestion job
enqueued → workers/ingestion: fetch → chunk → embed → knowledge_chunks
(write) → knowledge_source.ingestion_status = ingested
   → scheme_version authored/reviewed referencing this source →
     eligibility_rules + document_requirements written, citing source
   → scheme_version published (four-eyes review) → live for eligibility
     evaluation and assistant retrieval
```
