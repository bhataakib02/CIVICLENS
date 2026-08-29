# ADR-008: Closed-Grammar Rule DSL, No Embedded Scripting or NL-at-Evaluation-Time

Status: Accepted
Date: 2026-08-29
Related: ai/rule-dsl.md, ai/eligibility-engine.md, security/threat-model.md #7

## Context

Eligibility rules need to be authored by many scheme administrators across
departments and evaluated safely against citizen data. Two tempting
alternatives were considered and rejected: an embedded scripting language
for maximum authoring flexibility, and having an LLM interpret natural
language policy text directly at evaluation time for maximum authoring
speed.

## Decision

Rules are represented as a closed-grammar JSON AST (see rule-dsl.md):
fixed operator set, a whitelisted field registry, bounded nesting depth,
no function calls, no external references, no code execution of any kind.
Authoring happens through a structured admin UI, not hand-written JSON in
production, with mandatory two-person review before publish.

## Consequences

- Positive: a malicious or buggy rule can at worst produce an incorrect
  but inert data structure — there is no code-execution attack surface
  to defend, directly addressing threat-model.md #7 (eligibility-rule
  tampering).
- Positive: the same AST renders three ways from one source (engine
  evaluation, admin editor, citizen-facing explanation) with no risk of
  the three diverging.
- Negative: genuinely novel eligibility logic that doesn't fit the grammar
  requires a grammar extension (a deliberate, reviewed schema change) or
  admission that a case needs human judgment routed to an agent — no
  fully generic escape hatch exists by design.

## Alternatives Considered

- **Embedded scripting language (e.g., a Python/JS sandbox)**: rejected —
  sandboxing is a hard, ongoing security problem, and rules become harder
  to render safely in an admin UI or explain to a citizen.
- **LLM interprets natural-language policy text at evaluation time**:
  rejected — non-deterministic, not reliably auditable, and conflicts
  directly with ADR-003's requirement that eligibility be decided
  deterministically.
