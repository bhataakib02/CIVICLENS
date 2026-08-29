# ADR-003: Eligibility Determined by a Deterministic Rule Engine, Never by the LLM

Status: Accepted
Date: 2026-08-29
Related: ai/ai-architecture.md, ai/eligibility-engine.md, ai/rule-dsl.md, NFR-AI-2, threat-model.md #10

## Context

CivicLens could plausibly let an LLM read a scheme's eligibility text and a
citizen's profile and directly answer "are they eligible?" This is faster
to build and more flexible to changes in scheme wording. But eligibility
for a welfare scheme is a decision with real consequences for a citizen,
and LLM output is not reproducible, not fully explainable at the
rule-by-rule level, and can hallucinate confident-sounding wrong answers.

## Decision

All eligibility determinations are computed by a deterministic, in-process
rule engine evaluating structured `eligibility_rules` (see rule-dsl.md)
against a citizen profile snapshot. The LLM may assist humans in authoring
rules (with review) and may explain a determination's rule_breakdown in
natural language, but never itself decides pass/fail/eligible.

## Consequences

- Positive: every determination is reproducible, auditable, and
  explainable at the rule level (FR-ELIGIBILITY-2); appeals/disputes can be
  investigated by re-running the exact rule set against the exact profile
  snapshot used.
- Positive: no single LLM provider outage or model-version change can alter
  or take down eligibility determination (NFR-AVAIL-3).
- Negative: scheme rules must be translated from free-text government
  policy into the structured DSL by a human (or human-reviewed AI
  assistance) before they're usable — this is real authoring effort,
  not automatic.
- Negative: the DSL cannot express every conceivable eligibility nuance;
  edge cases that genuinely require judgment are flagged as
  `insufficient_data` and routed to human/agent support rather than forced
  into the DSL awkwardly.

## Alternatives Considered

- **LLM directly evaluates eligibility from scheme text + profile**:
  rejected — not reproducible, not reliably explainable, and the risk
  profile of a wrong welfare-eligibility answer is judged too high for
  free-generation output (see ai-architecture.md §1, threat-model.md #10).
- **Hybrid: LLM proposes, engine validates**: rejected for the
  determination path itself, but adopted for rule *authoring* assistance
  (a human-reviewed suggestion, not an evaluation-time decision).
