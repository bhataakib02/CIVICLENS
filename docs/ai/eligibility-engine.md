# CivicLens — Eligibility Engine

Status: v1.0 draft
Related: rule-dsl.md, ai-architecture.md, ADR-003, database/data-dictionary.md (eligibility_rules, eligibility_checks)

## 1. What It Is

A deterministic, in-process rule evaluator. Given a citizen profile
snapshot and a `scheme_version`'s set of `eligibility_rules`, it produces a
structured result. It is a pure function of (profile snapshot, rule set) —
no network call, no model inference, fully reproducible and unit-testable.

```
evaluate(profile_snapshot, rules: list[EligibilityRule]) -> EligibilityResult
```

## 2. Result Shape

```json
{
  "result": "likely_eligible",
  "rule_breakdown": [
    {
      "rule_id": "…",
      "field_key": "declared_annual_income",
      "operator": "lte",
      "value": 250000,
      "citizen_value": 180000,
      "outcome": "pass",
      "explanation": "Household annual income must not exceed ₹2,50,000.",
      "source_citation": {"knowledge_source_id": "…", "section": "Clause 4(a)"}
    },
    {
      "rule_id": "…",
      "field_key": "land_holding_acres",
      "operator": "lte",
      "value": 2,
      "citizen_value": null,
      "outcome": "unknown",
      "explanation": "Applicant's landholding must not exceed 2 acres.",
      "source_citation": {"knowledge_source_id": "…", "section": "Clause 4(b)"}
    }
  ]
}
```

`result` is derived from the breakdown:
- `not_eligible` if any **mandatory** rule outcome is `fail`.
- `insufficient_data` if any **mandatory** rule outcome is `unknown` (and no
  mandatory rule failed).
- `likely_eligible` if all mandatory rules pass but an **optional/advisory**
  rule is `unknown`.
- `eligible` if all rules resolved and passed.

## 3. Determinism & Auditability Requirements

- Same (profile snapshot, rule set) input always yields the same output —
  no randomness, no external calls, no wall-clock-dependent branches other
  than explicit date-comparison operators evaluated against a passed-in
  `as_of_date`.
- Every `eligibility_checks` row persists the full `rule_breakdown`, the
  exact `profile_version_no`, and `scheme_version_id` used, so a citizen
  or auditor can reconstruct exactly why a determination was made, even
  after the profile or the scheme has since changed (FR-PROFILE-5,
  NFR-OBS-2).
- The engine never calls out to an LLM. If a future version wants
  LLM-assisted rule *drafting*, that happens at authoring time in the admin
  console, producing a DSL rule a human reviews and publishes — never at
  evaluation time.

## 4. Performance

- Rules for a given `scheme_version` are compiled (parsed from JSONB into
  an in-memory AST) once and cached in-process/in-Redis, keyed by
  `scheme_version_id`, invalidated on new version publish.
- Bulk evaluation across the full catalog for one citizen batches rule sets
  and evaluates in a single pass over compiled ASTs — see NFR-PERF-4 for
  the latency target.

## 5. Handling Ambiguous or Missing Data

The engine never guesses. A missing `field_key` on the profile snapshot
always yields `unknown` for that rule (never `pass` or `fail` by default).
This is a deliberate conservative bias: it's safer to tell a citizen "we
need more information" than to falsely include or exclude them.

## 6. Simulation Mode

Scheme admins can run the engine against a sample of anonymized existing
profiles before publishing a new `scheme_version` (FR-ELIGIBILITY-5), to see
the distributional impact of a rule change (e.g., "raising the income
threshold from ₹2L to ₹2.5L moves 8% of previously-ineligible sampled
profiles to eligible"). This uses the same `evaluate()` function — no
separate simulation logic to keep in sync.

## 7. Testing Requirements

Every rule operator (eq, neq, gt, gte, lt, lte, in, not_in, exists,
between) has dedicated unit tests, plus property-based tests asserting: the
engine never returns `eligible` when a mandatory rule is `unknown`, and
never mutates its inputs. See testing/testing-strategy.md and
testing/ai-testing.md (which, despite the "ai" name, treats this component
as deterministic software, not as a model to be evaluated).
