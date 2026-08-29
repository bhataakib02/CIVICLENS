# Retrieval Pipeline

Status: v1.0 draft
Related: rag-architecture.md, ADR-002, ADR-007, database/erd.md (knowledge_chunks)

## 1. Chunking

Government source documents are split into overlapping chunks (target
~500 tokens, ~15% overlap) at semantically meaningful boundaries (section/
clause breaks preferred over arbitrary token cuts) during ingestion (see
knowledge/ingestion-pipeline.md). Each chunk retains `page_number`,
`char_start`, `char_end` for exact citation back to the source.

## 2. Embedding

Chunks are embedded with a fixed embedding model (see ai/model-selection.md)
at ingestion time and stored in `knowledge_chunks.embedding`
(pgvector). Changing the embedding model requires a full re-embedding
migration — documented as an operational runbook, not a casual config
change (ADR-002).

## 3. Hybrid Query-Time Retrieval (ADR-007)

- **Lexical**: PostgreSQL full-text search (+ pg_trgm for fuzzy matching)
  over `knowledge_chunks.content`, good for exact scheme names, figures,
  and terminology.
- **Semantic**: pgvector cosine similarity over the query embedding, good
  for paraphrased/situation-described questions.
- **Fusion**: both result sets are merged via reciprocal rank fusion (or
  equivalent weighted scoring) into a single ranked list.

## 4. Filtering

Retrieval is scoped to `knowledge_chunks` belonging to currently-effective
`scheme_versions` by default (respecting `effective_from`/`effective_to`),
so the assistant doesn't surface superseded policy text as current — an
explicit "as of" override is available for historical queries.

## 5. Top-k Selection

Default top-k = 8 chunks passed to generation, tuned against the
evaluation set in ai-evaluation.md; changing top-k, chunk size, or fusion
weighting is treated as a retrieval-pipeline change subject to the
evaluation gate (ADR-009).
