# CivicLens — Eligibility Rule DSL

Status: v1.0 draft
Related: eligibility-engine.md, database/data-dictionary.md (eligibility_rules), ADR-008

## 1. Purpose

A constrained, declarative representation of eligibility logic that is:
safe to store as data (JSONB), safe to evaluate without a sandboxing
concern (no arbitrary code execution — ADR-008), renderable in the admin
rule editor, and renderable as a citizen-facing plain-language explanation.
It is explicitly **not** a general-purpose expression language — no
function calls, no loops, no references to anything outside a fixed field
whitelist.

## 2. Grammar

A rule set for a `scheme_version` is a tree of nodes:

```
RuleNode := Condition | Group

Condition := {
  "type": "condition",
  "field_key": <string, must be in FIELD_REGISTRY>,
  "operator": "eq" | "neq" | "gt" | "gte" | "lt" | "lte"
            | "in" | "not_in" | "exists" | "between",
  "value": <literal | [literal, literal] for "between">,
  "mandatory": <boolean, default true>,
  "explanation_text": <string, citizen-facing>,
  "source_citation": { "knowledge_source_id": <uuid>, "section": <string> }
}

Group := {
  "type": "group",
  "operator": "AND" | "OR",
  "children": [RuleNode, ...]   // max depth 4, max 20 leaf conditions
}
```

## 3. Field Registry

`field_key` values are restricted to a fixed, versioned whitelist mapping
to actual `citizen_profiles` / `addresses` columns (e.g.
`declared_annual_income`, `age`, `state`, `category`, `disability_status`,
`land_holding_acres`, `family_size`, `occupation`). Adding a new field_key
requires a schema migration (new profile column) plus a registry update —
it is not free-form, precisely to prevent rules referencing data that
doesn't exist or was typo'd (a common source of silent `unknown` results in
early prototyping).

## 4. Explicit Prohibitions (ADR-008)

The DSL **must never** support:
- Arbitrary Python, JavaScript, SQL, or shell expressions supplied as
  policy data.
- References to fields outside the FIELD_REGISTRY.
- External calls (HTTP, DB lookups) during evaluation.
- Non-deterministic values (e.g., "now()") except through the engine's
  single, explicit `as_of_date` parameter for date comparisons.

This is a security boundary, not just a style preference: `eligibility_rules`
are authored by many scheme administrators across departments, and a rule
set is effectively untrusted-ish input from the engine's point of view — it
must be safe to evaluate no matter who wrote it (see
security/threat-model.md, "Eligibility-rule tampering").

## 5. Example: PM Scholarship Scheme (illustrative)

```json
{
  "type": "group",
  "operator": "AND",
  "children": [
    {
      "type": "condition",
      "field_key": "declared_annual_income",
      "operator": "lte",
      "value": 250000,
      "mandatory": true,
      "explanation_text": "Household annual income must not exceed ₹2,50,000.",
      "source_citation": {"knowledge_source_id": "…", "section": "Clause 4(a)"}
    },
    {
      "type": "group",
      "operator": "OR",
      "children": [
        {
          "type": "condition",
          "field_key": "category",
          "operator": "in",
          "value": ["SC", "ST", "OBC"],
          "mandatory": false,
          "explanation_text": "Priority category (not required, but improves benefit tier).",
          "source_citation": {"knowledge_source_id": "…", "section": "Clause 4(c)"}
        },
        {
          "type": "condition",
          "field_key": "disability_status",
          "operator": "eq",
          "value": true,
          "mandatory": false,
          "explanation_text": "Priority for applicants with disability status.",
          "source_citation": {"knowledge_source_id": "…", "section": "Clause 4(d)"}
        }
      ]
    }
  ]
}
```

## 6. Authoring & Review Flow

Rules are authored through the admin console's structured rule builder
(never as raw hand-edited JSON in production), which validates against the
grammar and field registry before allowing save-as-draft, and requires a
second reviewer to approve before a `scheme_version` moves from
`in_review` to `published` (FR-ADMIN-2). See ADR-008 for the decision
record and rejected alternatives (embedded scripting language, natural
language rules interpreted by an LLM at evaluation time).

## 7. Rendering

The same AST is rendered three ways from one source of truth:
1. **Engine evaluation** — eligibility-engine.md.
2. **Admin rule editor UI** — a structured form matching the grammar.
3. **Citizen-facing explanation** — `explanation_text` per condition, shown
   pass/fail/unknown per FR-ELIGIBILITY-2, with the `source_citation`
   linked to the underlying government document.
