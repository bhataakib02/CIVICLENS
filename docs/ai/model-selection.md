# Model Selection

Status: v1.0 draft
Related: ai-architecture.md §3, rag-architecture.md, product-self-knowledge (internal reference for current model names)

## 1. Current Provider/Model Matrix (v1.0 launch)

| Task | Provider | Notes |
|---|---|---|
| RAG generation, structured extraction, classification, query-intent routing | Anthropic Claude | Chosen for strong instruction-following on "answer only from context, cite sources, refuse if unsupported," and reliable tool-use for eligibility-engine invocation |
| Embeddings | Fixed embedding model, dimension matches `knowledge_chunks.embedding` column | Changing requires full re-embed (ADR-002) |
| OCR | Pluggable managed OCR provider behind an internal interface | Swappable without touching `documents` module logic |

Exact model versions are a deployment/config concern, not fixed in this
document — see the runtime configuration in `backend/app/core/config.py`
and the current model string tracked in deployment records, since pinning
a specific version number here would drift immediately.

## 2. Selection Criteria

- Instruction-following reliability on the specific "ground in context,
  cite, refuse" pattern this system depends on (measured via
  ai-evaluation.md, not vendor marketing claims).
- Tool-use reliability, since eligibility-question routing depends on the
  model correctly and consistently invoking the eligibility engine tool
  rather than answering from context alone.
- Support for the languages required at launch (Hindi + English,
  NFR-ACC-3).
- Data handling terms compatible with DPDP Act obligations for any PII
  that must pass through a provider (kept minimal per pii-handling.md §2).

## 3. Changing Models

Any model version or provider change for generation is treated as a
retrieval/generation pipeline change and must pass the evaluation gate
(ADR-009) before shipping to production — including "minor" version bumps,
since instruction-following behavior can shift in ways that matter for
this system's citation and refusal requirements.

## 4. Multi-Provider Resilience

The eligibility engine's independence from any LLM call (ADR-003) means a
generation-provider outage degrades only the assistant subsystem
(NFR-AVAIL-2), never core eligibility/application functionality
(NFR-AVAIL-3).
