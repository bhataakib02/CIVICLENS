# Unit Testing

Status: v1.0 draft
Related: testing-strategy.md §3, backend/service-layer.md §4, ai/eligibility-engine.md §7

## 1. Scope & Tooling

Pytest for the backend; service-layer functions tested with the
repository layer mocked (backend/service-layer.md §4), so unit tests
verify business logic without needing a real database.

## 2. Priority Coverage

- **Rule DSL parser/validator** (ai/rule-dsl.md) — every operator, valid
  and malformed rule structures, field-registry enforcement, nesting-depth
  limits.
- **Eligibility engine `evaluate()`** (ai/eligibility-engine.md) — every
  operator, every result category, property-based tests for the "never
  eligible when a mandatory rule is unknown" invariant, and a test
  confirming `evaluate()` never mutates its inputs.
- **Application status state machine** — every legal transition succeeds,
  every illegal transition raises the expected domain exception.
- **Document extraction confidence thresholding** — boundary values around
  the confidence cutoff.
- **Rate limit / idempotency key logic** — deterministic behavior under
  repeated/concurrent-like input.

## 3. Property-Based Testing

Used specifically for the eligibility engine and rule DSL, where the
input space (arbitrary profile field combinations × arbitrary rule
structures) is large and hand-written example tests alone would likely
miss edge cases — using a library like `hypothesis` to generate profile/
rule combinations and assert engine invariants hold universally.

## 4. Coverage Gate

`core` and `eligibility` modules: ≥ 80% line coverage, enforced in CI
(NFR-MAINT-3); other modules are expected to have meaningful coverage but
without a hard-enforced numeric floor, reviewed qualitatively in PR
review instead.
