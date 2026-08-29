# Classification

Status: v1.0 draft
Related: entity-extraction.md, document-intelligence.md, rag-architecture.md

## 1. Where Classification Is Used

- **Document type classification**: when a citizen uploads a document
  without explicitly tagging its type (or to verify a self-tagged type),
  the pipeline classifies it into one of the supported document types
  (document-intelligence.md §2) before running type-specific extraction.
- **Query intent classification**: the assistant classifies an incoming
  citizen message as eligibility-shaped (→ route to the eligibility engine
  tool), factual/informational (→ standard RAG), or out-of-scope
  (→ refusal/human handoff) (rag-architecture.md §3).
- **Scheme categorization**: at ingestion/authoring time, schemes are
  classified into the catalog's browse categories (education, health,
  agriculture, etc.) to support FR-SCHEME-1.

## 2. Method

Lightweight classification is handled by the same LLM used for other
language tasks, constrained to a fixed label set via prompt structure —
no separate classifier model is deployed for v1.0, to keep the model
surface area small and centrally evaluable. If classification accuracy or
latency needs diverge significantly from generation needs, a dedicated
lightweight classifier is a candidate for a later iteration.

## 3. Confidence & Fallback

- Document type misclassification defaults to asking the citizen to
  confirm/select the type rather than guessing silently.
- Query intent misclassification is mitigated by the eligibility engine
  tool being safe to call speculatively — if a question is ambiguously
  eligibility-shaped, routing to the tool and including its result
  alongside retrieved context is preferred over a wrong guess either way.

## 4. Evaluation

Query intent routing accuracy is part of the ai-evaluation.md metric set
(see "Eligibility routing accuracy"); document type classification
accuracy is tracked against the labeled document sample in
testing/ai-testing.md.
