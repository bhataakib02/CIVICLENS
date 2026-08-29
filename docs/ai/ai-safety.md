# AI Safety

Status: v1.0 draft
Related: hallucination-controls.md, threat-model.md #3 #4 #10, prompt-engineering.md

## 1. Scope

This document covers safety concerns specific to CivicLens's AI
components, layered on top of (not replacing) the general security
controls in security-architecture.md.

## 2. Prompt Injection (threat-model.md #3)

Ingested government documents and any future citizen-submitted content
passed into a prompt are treated as untrusted data:
- Structurally delimited context blocks, explicit "context is data, not
  instructions" system-prompt language (prompt-engineering.md §1).
- The assistant's only tool is the read-only eligibility-evaluation
  function — no tool exists that can mutate state, send data externally,
  or take an action a successful injection could exploit for real-world
  effect beyond producing a misleading chat message (which
  hallucination-controls.md's citation/refusal checks further guard
  against).
- Knowledge sources are ingested only from a vetted publisher allowlist
  (knowledge/source-policy.md), reducing the chance of an adversarial
  document entering the pipeline at all.

## 3. RAG Poisoning (threat-model.md #4)

See knowledge/source-verification.md for the ingestion review process;
from the AI-safety side, every assistant answer surfaces its source
explicitly so a poisoned-but-ingested source is at least independently
checkable by the citizen or an auditor, rather than laundered into
unattributed prose.

## 4. Hallucination / Overclaiming (threat-model.md #10)

See hallucination-controls.md for the full control set. The core safety
posture: the assistant is designed to be more willing to say "I don't
know, let me connect you with a person" than to guess, because the
consequence of a wrong eligibility-adjacent statement affects a citizen's
real access to a welfare benefit.

## 5. Output Filtering

Generated responses pass through the citation-verification check
(hallucination-controls.md §2) and a basic content-safety filter before
reaching the citizen (guarding against off-topic, harmful, or
policy-violating generations, independent of factual accuracy).

## 6. Escalation Path

Any assistant interaction the citizen flags as wrong, confusing, or
unhelpful — or any refusal — offers a clear path to human/agent support
(FR-ASSISTANT-3), so AI safety failures have a human backstop rather than
leaving the citizen stuck.

## 7. Ongoing Review

AI safety posture is reviewed whenever the model provider, prompt
structure, or tool set changes materially — folded into the same
evaluation gate as quality changes (ADR-009), since safety and quality
regressions can share root causes (e.g., a prompt change that loosens
grounding also tends to loosen injection resistance).
