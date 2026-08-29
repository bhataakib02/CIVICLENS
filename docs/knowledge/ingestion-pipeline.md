# Ingestion Pipeline

Status: v1.0 draft
Related: knowledge-base.md, source-policy.md, ai/retrieval-pipeline.md §1-2, backend/background-jobs.md

## 1. Steps

```
Source registered (source-policy.md §2)
   → job enqueued to `ingestion` queue (ADR-006)
   → [worker] fetch document (PDF/HTML)
   → [worker] extract text, preserving page/section structure
   → [worker] chunk (ai/retrieval-pipeline.md §1: ~500 tokens, ~15% overlap,
     boundary-aware where possible)
   → [worker] generate embeddings per chunk (ai/retrieval-pipeline.md §2)
   → write knowledge_chunks rows (with page/char-offset provenance)
   → knowledge_source.ingestion_status = pending_review
   → human reviewer confirms accuracy/currency
   → knowledge_source.ingestion_status = ingested (now retrievable)
```

## 2. Failure Handling

Fetch failures, unparseable documents, or extraction producing
suspiciously low content volume mark `ingestion_status = failed` with a
reason, surfaced in the admin knowledge base monitor (FR-ADMIN-3) rather
than silently retrying forever or partially ingesting.

## 3. Human Review Gate

Automated ingestion produces a `pending_review` state, not an immediately
retrievable one — a human confirms the extracted/chunked content
genuinely reflects the source before it becomes part of what the
assistant can cite, closing the loop opened by source-policy.md's
allowlist requirement.

## 4. Re-Ingestion

Triggered manually (admin action) or automatically on a periodic schedule
per source-verification.md's staleness check; re-ingestion for a source
replaces its prior `knowledge_chunks` rather than accumulating duplicate
stale chunks alongside fresh ones.

## 5. Change Sensitivity

A change to the chunking strategy or embedding model (chunk size, overlap,
embedding dimension) requires re-ingesting the full corpus and is treated
as a retrieval-pipeline change subject to the AI evaluation gate
(ADR-009) before the new chunks replace the old ones in production
retrieval.
