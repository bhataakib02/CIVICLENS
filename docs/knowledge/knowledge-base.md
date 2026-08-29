# Knowledge Base

Status: v1.0 draft
Related: source-policy.md, ingestion-pipeline.md, source-verification.md, document-versioning.md, ai/rag-architecture.md, database/erd.md

## 1. What It Is

The corpus of government source documents (`knowledge_sources`) and their
chunked, embedded representations (`knowledge_chunks`) that back both the
RAG assistant's retrieval and the citations attached to
`eligibility_rules` and `scheme_versions`. It is the single evidentiary
backbone the whole system's "explainable and citable" promise rests on —
see product-requirements.md §2, goal 5.

## 2. Content Types

Official scheme notifications/circulars, eligibility criteria documents,
benefit schedules, application procedure guides, and amendment notices —
all sourced from a vetted publisher allowlist (source-policy.md), never
from unmoderated third-party summaries or citizen-submitted content.

## 3. Lifecycle

```
Source registered (admin, vetted publisher only)
   → ingested (chunked + embedded, ingestion-pipeline.md)
   → referenced by one or more scheme_versions (as provenance for rules
     and benefit summaries)
   → periodically re-verified for currency (source-verification.md)
   → superseded by a newer version when policy changes (document-versioning.md),
     old version retained for historical explainability (ADR-004's logic
     extended to knowledge sources)
```

## 4. Quality Bar

A source only becomes retrievable by the assistant once its
`ingestion_status` is `ingested` (post-review) — see
knowledge/source-policy.md for what "vetted" requires before that gate
opens.

## 5. Relationship to Eligibility Rules

`eligibility_rules.source_citation` and `scheme_versions.knowledge_source_id`
tie the deterministic rule engine's output back to this same knowledge
base, so a citizen's eligibility explanation and the assistant's free-text
answers are always ultimately traceable to the same underlying government
documents — one knowledge base, two consumers (engine citations and RAG
retrieval), never two divergent copies of "what the policy says."
