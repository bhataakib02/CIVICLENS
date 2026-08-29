# Scalability

Status: v1.0 draft
Related: system-architecture.md, deployment-architecture.md, NFR-SCALE-*

## 1. Scaling Dimensions

| Dimension | Approach | Trigger |
|---|---|---|
| API request volume | Horizontal autoscaling, stateless FastAPI instances behind ALB | Request concurrency / CPU |
| Async workload volume (OCR, embeddings, notifications) | Horizontal autoscaling of Celery workers | Queue depth |
| Knowledge base size (vector search) | pgvector IVFFlat/HNSW index, tuned lists/probes; read replica if needed | Chunk count, p95 query latency |
| Scheme catalog size | Rule-set compilation cache keyed by scheme_version_id | Catalog size, eligibility check latency |
| Citizen data volume | Standard relational scaling (indexing, eventual read replicas) | Row counts, query latency |

## 2. Known Future Bottlenecks (tracked, not yet hit)

- `knowledge_chunks` similarity search at multi-hundred-thousand-chunk
  scale may need a dedicated vector store (revisits ADR-002) or
  index-tuning beyond default IVFFlat settings.
- Bulk eligibility check (`/eligibility/check-all`) cost scales with
  active scheme count; the compiled-rule-set cache (ai/eligibility-engine.md
  §4) is the primary mitigation, revisit if scheme count grows an order of
  magnitude beyond the ~500-scheme launch target.
- Document OCR throughput during high-traffic campaign periods (e.g., a
  scheme deadline driving a surge in uploads) — worker autoscaling plus
  provider-side rate limits are the binding constraints to monitor.

## 3. Load Testing

Scalability assumptions are validated, not just assumed, via
testing/load-testing.md before major releases.
