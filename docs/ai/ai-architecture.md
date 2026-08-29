# CivicLens — AI Architecture

Status: v1.0 draft
Related: eligibility-engine.md, rule-dsl.md, rag-architecture.md, retrieval-pipeline.md, hallucination-controls.md, ai-evaluation.md, ADR-003, ADR-007, ADR-009

## 1. Governing Principle

CivicLens uses AI for **language tasks**, never for **adjudication**. This
split is the single most important architectural decision in the system
(ADR-003):

| Task | Who decides | Why |
|---|---|---|
| "Is this citizen eligible for scheme X?" | Deterministic rule engine | Must be reproducible, auditable, appealable |
| "Explain in Hindi why this citizen is eligible" | LLM, grounded in the engine's rule_breakdown | Language generation, not a decision |
| "What documents does scheme X require?" | Retrieval from knowledge_chunks | Factual lookup, must cite source |
| "Turn this citizen's free-text answer into a profile field" | LLM structured extraction, citizen confirms before it's saved | Assistive parsing, human-in-the-loop |
| "Read this uploaded income certificate and extract the income figure" | OCR + extraction model, citizen confirms before use | Assistive parsing, human-in-the-loop |

No component may let free-generation model output become an eligibility
determination or a claimed factual statement about a scheme without a
citation (NFR-AI-1, NFR-AI-2).

## 2. AI Subsystems

### 2.1 Eligibility Engine (deterministic, not ML)
See eligibility-engine.md and rule-dsl.md. Included here only because it is
the component every other AI subsystem must defer to for eligibility
questions.

### 2.2 RAG Assistant
Answers free-text citizen questions using retrieval over `knowledge_chunks`
plus generation, with mandatory citations. See rag-architecture.md,
retrieval-pipeline.md, hallucination-controls.md. When a question is
eligibility-shaped, the assistant calls the eligibility engine as a tool
rather than answering from retrieved prose (see 3.3 in
architecture/component-architecture.md).

### 2.3 Document Intelligence
OCR + structured field extraction from uploaded documents. See
document-intelligence.md, entity-extraction.md. Output is always shown to
the citizen for confirmation (FR-DOCS-3) before being used elsewhere.

### 2.4 Profile Assistant (structured extraction from free text)
Lets a citizen describe their situation in a sentence ("I'm a farmer in
Bihar with 2 acres and three kids") and have it proposed as structured
profile fields, which the citizen must confirm before they're saved and
used in eligibility evaluation. This is extraction, not eligibility
reasoning — the LLM never infers eligibility from the sentence, only
structured facts.

### 2.5 Knowledge Ingestion
Pipeline that chunks government source documents, generates embeddings, and
maintains source-verification/staleness metadata. See
knowledge/ingestion-pipeline.md, knowledge/source-verification.md.

## 3. Model Selection

See model-selection.md for the current provider/model matrix. Summary
constraints:
- Generation (RAG answers, extraction): Anthropic Claude, selected for
  strong instruction-following on "answer only from context, cite
  sources, refuse if unsupported" prompting and tool-use reliability
  (calling the eligibility engine as a tool).
- Embeddings: a fixed embedding model per pgvector column dimension;
  changing embedding models requires re-embedding the full knowledge base
  (documented as a runbook, not a casual config change).
- OCR: pluggable managed OCR provider behind an internal interface, so the
  provider can be swapped without touching `documents` module logic.

## 4. Evaluation & Safety Gates

Per ADR-009, no change to prompts, retrieval configuration, or model
version reaches production without passing the held-out evaluation set
described in ai-evaluation.md — factual accuracy, citation presence, and
refusal-when-unsupported are all scored, not just "does it sound right."
See ai-safety.md for the broader safety posture (prompt injection handling
from ingested government documents, output filtering, escalation to human
support).

## 5. What This System Deliberately Does Not Do

- Does not let the LLM's own knowledge answer scheme-specific factual
  questions, even when the LLM is "probably right" — the risk of an
  authoritative-sounding wrong answer about eligibility for a welfare
  scheme is judged too high (see ai-safety.md, hallucination-controls.md).
- Does not auto-apply extracted document/profile data without citizen
  confirmation.
- Does not use the LLM to generate or modify `eligibility_rules` directly
  in production — rule authoring is a human (scheme admin) task, with the
  DSL as the interface; AI assistance in drafting rules, if added later, is
  a suggestion a human must review and publish (see rule-dsl.md).
