# AI Evaluation

Status: v1.0 draft
Related: hallucination-controls.md, ADR-009, testing/ai-testing.md

## 1. Evaluation Set

A held-out, versioned set of scheme Q&A pairs, covering:
- Answerable factual questions with a known-correct answer and expected
  citation(s).
- Eligibility-shaped questions that should route to the deterministic
  engine (verifying the routing itself, not just the final prose).
- Adversarial/unanswerable questions (asking about a non-existent scheme,
  asking for legal advice, asking a question outside the knowledge base's
  coverage) that should produce a refusal.
- Paraphrased/situation-described variants of the same underlying
  question, to stress-test retrieval recall (ADR-007's rationale).
- Prompt-injection probes embedded in synthetic "retrieved" content, to
  verify the model doesn't follow instructions embedded in context
  (threat-model.md #3).

## 2. Scored Metrics

| Metric | What it checks |
|---|---|
| Factual accuracy | Does the answer match the expected fact? |
| Citation presence | Does every factual sentence carry a citation? |
| Citation correctness | Does the citation actually support the claim (not just present, but relevant)? |
| Refusal correctness | Does the assistant refuse exactly the questions it should, and only those? |
| Eligibility routing accuracy | Does an eligibility-shaped question correctly invoke the engine tool? |

## 3. Gate (ADR-009)

Thresholds per metric are defined and versioned alongside the evaluation
set; a run below threshold blocks the corresponding prompt/retrieval/model
change from merging. Results are logged per run for trend tracking, not
just pass/fail.

## 4. Set Maintenance

The evaluation set is expanded as new schemes are onboarded and as new
question patterns are observed in production (via anonymized, PII-scrubbed
sampling of real assistant usage, with consent/privacy handling per
pii-handling.md) — an evaluation set that doesn't grow with the knowledge
base under-detects regressions on newer content (see ADR-009
consequences).
