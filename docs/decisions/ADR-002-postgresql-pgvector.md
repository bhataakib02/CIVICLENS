# ADR-002: PostgreSQL + pgvector over a Separate Vector Database

Status: Accepted
Date: 2026-08-29
Related: database/database-design.md, ai/rag-architecture.md, NFR-SCALE-3

## Context

The RAG assistant needs similarity search over `knowledge_chunks`
embeddings. A dedicated vector database (e.g. Pinecone, Weaviate, Qdrant)
is a common choice, but CivicLens's citation model requires every retrieved
chunk to join cleanly back to its `knowledge_source`, `scheme_version`, and
ultimately the eligibility rules and document requirements derived from it
— all relational data.

## Decision

Store embeddings in the same PostgreSQL instance using the `pgvector`
extension, in the `knowledge_chunks` table, alongside (and foreign-keyed
to) the relational knowledge/scheme schema.

## Consequences

- Positive: retrieval → citation joins are transactionally consistent and
  a single query away — no risk of a vector store and the relational store
  drifting out of sync.
- Positive: one database to operate, back up, and secure, rather than two
  systems with separate access-control and backup stories.
- Positive: sufficient performance at target scale (NFR-SCALE-3: ≤200ms p95
  top-k at 50,000 chunks) using an IVFFlat/HNSW index.
- Negative: at much larger scale (millions of chunks) a dedicated vector
  database would likely outperform pgvector; this is an accepted tradeoff
  for launch scale, revisit if knowledge base growth trajectory changes
  materially.
- Negative: embedding model changes require a full re-embedding migration
  of the `embedding` column (documented as a runbook).

## Alternatives Considered

- **Dedicated vector database**: rejected for v1.0 — adds an operational
  system and a cross-store consistency problem for a citation-critical
  feature, without a performance need at launch scale.
