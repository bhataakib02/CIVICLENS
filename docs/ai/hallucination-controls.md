# Hallucination Controls

Status: v1.0 draft
Related: rag-architecture.md, ai-architecture.md, threat-model.md #10, ADR-003, ADR-009

## 1. Structural Controls (prevent, not just detect)

1. **Eligibility decisions never come from generation** — routed to the
   deterministic engine (ADR-003). This eliminates the highest-stakes
   category of hallucination by construction, not by prompting.
2. **Closed-context generation** — the system prompt instructs the model
   to answer only using the provided retrieved chunks, and explicitly
   states that any claim not supported by the provided context must be
   phrased as "I don't have a verified answer to that" rather than
   answered from general knowledge.
3. **Mandatory citation** — every generated factual sentence about a
   scheme must carry a citation back to a specific retrieved chunk
   (NFR-AI-1). This is both a prompt instruction and a post-generation
   check.

## 2. Post-Generation Verification

After generation, a lightweight check verifies that every sentence making
a factual claim (as opposed to a purely conversational sentence) has an
associated citation. Sentences that fail this check trigger either a
regeneration attempt with a stricter prompt, or — if still unresolved — a
fallback refusal rather than shipping an uncited claim to the citizen.

## 3. Refusal Is a Feature, Not a Failure

The assistant is explicitly evaluated (ai-evaluation.md) on its rate of
*correct refusal* on genuinely unanswerable/unsupported questions, not
just its accuracy on answerable ones. A refusal that routes the citizen to
human/agent support (FR-ASSISTANT-3) is a successful outcome for questions
outside the knowledge base's coverage.

## 4. Guarding Against Retrieved-Content Manipulation

Because hallucination risk also includes the model being misled by
low-quality or manipulated retrieved content (not just inventing content
from nothing), this document's controls work together with
knowledge/source-verification.md (vetted publisher allowlist) and
threat-model.md #4 (RAG poisoning) — a citation to a bad source is still a
hallucination-adjacent failure from the citizen's point of view, so source
quality is treated as part of hallucination prevention, not a separate
concern.

## 5. Monitoring in Production

Citation rate and flagged-uncited-response rate are tracked as ongoing
metrics (NFR-OBS-3), not just a pre-deploy gate — a regression that only
shows up at production scale/traffic must still be caught.
