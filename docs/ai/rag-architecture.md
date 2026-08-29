# RAG Architecture

Status: v1.0 draft
Related: ai-architecture.md, retrieval-pipeline.md, hallucination-controls.md, ADR-002, ADR-007

## 1. Pipeline

```
Citizen question
   │
   ▼
Query understanding (is this eligibility-shaped? → route to eligibility
   tool; otherwise → retrieval)
   │
   ▼
Hybrid retrieval (lexical + semantic, ADR-007) over knowledge_chunks
   │
   ▼
Re-rank + select top-k chunks
   │
   ▼
Prompt assembly: system instructions + retrieved chunks (delimited,
   marked as untrusted context) + conversation history + citizen question
   │
   ▼
Generation (Claude) — instructed to answer only from provided context,
   cite every factual claim, and explicitly refuse if context is
   insufficient
   │
   ▼
Response post-processing: verify every factual sentence has an attached
   citation; if not, either regenerate with a stricter prompt or fall back
   to a refusal
   │
   ▼
Response to citizen (answer + citations + any eligibility_tool_calls)
```

## 2. Storage

Embeddings and source text live together in PostgreSQL/pgvector (ADR-002),
so every retrieved chunk carries its `knowledge_source_id` and exact
character span for citation.

## 3. Eligibility Question Routing

Query understanding detects eligibility-shaped questions ("am I eligible
for X", "can I apply for X given Y") and routes them to the deterministic
eligibility engine as a tool call rather than answering from retrieved
prose — this is the architectural link back to ADR-003. Non-eligibility
factual questions ("what documents do I need", "what's the benefit
amount") go through standard retrieval + generation.

## 4. Conversation State

Multi-turn conversations are supported; prior turns are included in the
prompt context (bounded window) so follow-up questions ("what about my
brother, is he eligible too") retain context, but each turn's factual
claims are independently re-verified for citations — history doesn't
exempt a later turn from the citation requirement.

## 5. Fallback Behavior

If retrieval returns no chunks above a confidence threshold, or the LLM
provider is unavailable, the assistant returns an explicit "I don't have a
verified answer to that" response with an offer to route to human/agent
support (FR-ASSISTANT-3) — it never falls back to open-domain model
knowledge (NFR-AVAIL-2, NFR-AVAIL-3).
