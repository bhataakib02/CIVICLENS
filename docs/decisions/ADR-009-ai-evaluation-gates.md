# ADR-009: Mandatory Evaluation Gate Before Any RAG/Prompt Change Ships

Status: Accepted
Date: 2026-08-29
Related: ai/ai-evaluation.md, ai/hallucination-controls.md, testing/ai-testing.md, NFR-AI-3

## Context

Prompt wording, retrieval configuration (chunk size, top-k, hybrid-search
weighting), and model version changes can each silently degrade answer
quality or citation reliability in ways that are easy to miss in ad hoc
manual testing, especially regressions that only show up on
underrepresented question types.

## Decision

Maintain a held-out evaluation set of scheme Q&A pairs (including
adversarial/unanswerable questions that should trigger a refusal). No
change to the assistant's prompt, retrieval pipeline configuration, or
underlying model may ship to production without first passing this
evaluation set against defined thresholds for: factual accuracy, citation
presence on every factual claim, and correct refusal on unsupported
questions. Evaluation runs are automated and wired into CI/CD for the `ai/`
package (see infrastructure/ci-cd.md).

## Consequences

- Positive: prevents silent quality regressions from shipping; makes AI
  pipeline changes subject to the same "must pass tests" discipline as any
  other code change.
- Positive: the refusal-rate metric specifically guards against the
  hallucination risk called out in ai-architecture.md and
  threat-model.md #10.
- Negative: adds latency to the AI pipeline's change/deploy cycle
  (running the eval set takes time and, depending on set size, some LLM
  API cost) — accepted as a necessary cost given the domain
  (welfare-eligibility information).
- Negative: the evaluation set itself requires ongoing maintenance
  (expanding coverage as new schemes/question patterns emerge) or it will
  under-detect regressions on newer content — owned as an explicit,
  recurring task, not a one-time artifact.

## Alternatives Considered

- **Manual QA review only**: rejected — doesn't scale, inconsistent
  coverage, easy to skip under deadline pressure.
- **Post-deploy monitoring only (no pre-deploy gate)**: rejected as the
  sole safeguard — for welfare-eligibility information, a citizen
  receiving a wrong or uncited answer even briefly in production is a
  real-world harm, not just a metric dip to notice after the fact;
  monitoring is retained as a complement, not a replacement (see
  operations/alerting.md).
