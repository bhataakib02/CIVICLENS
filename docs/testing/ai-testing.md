# AI-Component Testing

Status: v1.0 draft
Related: testing-strategy.md §7, ai/ai-evaluation.md, ai/eligibility-engine.md §7, ADR-009

## 1. Not One Category — Three

CivicLens's AI-adjacent components have genuinely different testing needs
because they play different roles (ai/ai-architecture.md §1):

### 1.1 Eligibility Engine — deterministic software
Treated exactly like any other business-logic code: unit tests, property-
based tests, no "model evaluation" concept applies because there is no
model in this path (ai/eligibility-engine.md §7, unit-testing.md §2–3).

### 1.2 RAG Assistant — evaluated like a model
Held-out evaluation set scored on factual accuracy, citation presence/
correctness, and refusal correctness (ai/ai-evaluation.md), gated before
any prompt/retrieval/model change ships (ADR-009). This is genuine model
evaluation, not conventional unit testing — outputs are probabilistic and
graded against a rubric, not asserted for exact equality.

### 1.3 Document Intelligence (OCR + extraction) — evaluated against
labeled ground truth
A labeled sample of representative documents (varied quality, lighting,
language, document type) with known-correct field values; tracks
field-level extraction accuracy and confidence-calibration (does a 0.9
confidence score actually correspond to ~90% correctness empirically) —
recalibrated periodically as OCR provider or document population
characteristics shift.

## 2. Regression Testing

Both 1.2 and 1.3 run their respective evaluation sets on every relevant
change, with results tracked over time (not just pass/fail at a point in
time) so a gradual quality drift is visible before it crosses the gate
threshold.

## 3. Adversarial Testing

The RAG evaluation set includes adversarial cases specifically: prompt-
injection probes, unanswerable questions, and questions designed to tempt
the model into eligibility-adjudication language ("is this scheme good
for me" phrased to invite an opinion rather than a citation-backed fact)
— testing not just "does it get facts right" but "does it stay inside its
architecturally-assigned role" (ai/ai-architecture.md §1).

## 4. Ownership

The team owning the `ai/` package owns these evaluation sets and their
maintenance (ai/ai-evaluation.md §4) — evaluation-set upkeep is a
recurring engineering responsibility, not a one-time deliverable.
