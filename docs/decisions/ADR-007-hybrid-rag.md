# ADR-007: Hybrid Retrieval (Lexical + Semantic) for the RAG Assistant

Status: Accepted
Date: 2026-08-29
Related: ai/rag-architecture.md, ai/retrieval-pipeline.md, ai/hallucination-controls.md

## Context

Citizens ask questions in varied phrasing — sometimes matching a scheme's
exact terminology ("PM-KISAN"), sometimes describing their situation in
plain language with no scheme name at all. Pure semantic (embedding)
search handles paraphrase well but can miss exact-name/exact-figure
lookups; pure lexical (full-text) search handles exact terms well but
misses paraphrase and cross-lingual queries.

## Decision

Use hybrid retrieval: combine PostgreSQL full-text/trigram search over
`knowledge_chunks.content` with pgvector semantic similarity search, merge
and re-rank results (reciprocal rank fusion or an equivalent scoring
combination), and pass the top-k merged chunks to the generation step.

## Consequences

- Positive: better recall across both "exact scheme name" and "described
  situation, no scheme name" query patterns than either method alone.
- Positive: both retrieval paths query the same PostgreSQL instance
  (consistent with ADR-002), no added infrastructure.
- Negative: added query-time complexity (two retrieval paths + a merge
  step) versus a single retrieval method; mitigated by keeping the merge
  logic in one well-tested library function (`ai/` retrieval pipeline)
  shared by the assistant and any future batch-evaluation tooling.

## Alternatives Considered

- **Semantic-only retrieval**: rejected as the sole method — degrades on
  exact-name and exact-figure queries common in citizen questions
  ("what's the income limit for X").
- **Lexical-only retrieval**: rejected as the sole method — degrades on
  paraphrased, situation-described queries, which are expected to be
  common given CivicLens's target users often won't know scheme names.
