"""Deterministic eligibility engine (eligibility-engine.md §2, prompt §14).

Pure function of (compiled AST, context) -> EngineResult. No randomness, no
network, no wall-clock branch except the explicit ctx.evaluation_date used by
date operators. Never calls an LLM. Never mutates its inputs.

Decision aggregation (eligibility-engine.md §2, reconciled with prompt §14):
- NOT_ELIGIBLE     if any MANDATORY leaf/group resolves FAIL.
- INSUFFICIENT_DATA if no mandatory FAIL, but a MANDATORY leaf/group is
  UNKNOWN (missing OR conflicting required facts). Conflicts are surfaced
  separately in `conflicts` (prompt §13) but, per the engine's "never guess"
  rule, still resolve the decision to INSUFFICIENT_DATA rather than a made-up
  CONFLICTING enum value that the contract does not define.
- LIKELY_ELIGIBLE  if all mandatory rules PASS but an OPTIONAL rule is UNKNOWN
  (FR-ELIGIBILITY-2: missing optional data).
- ELIGIBLE         if all rules resolved and all mandatory rules PASS and no
  optional rule is unknown.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.modules.eligibility.context import EligibilityContext
from app.modules.eligibility.evaluator import evaluate_node
from app.modules.eligibility.rule_types import (
    ENGINE_VERSION,
    ConditionNode,
    Decision,
    GroupNode,
    Operator,
    Outcome,
)


@dataclass
class RuleOutcomeRow:
    rule_id: str | None
    rule_code: str
    field_key: str
    operator: str
    value: Any
    citizen_value: Any
    outcome: str
    mandatory: bool
    explanation: str
    source_citation: dict | None


@dataclass
class EngineResult:
    decision: Decision
    engine_version: str
    rule_breakdown: list[RuleOutcomeRow]
    matched_rules: list[str]
    failed_rules: list[str]
    missing_information: list[dict]
    conflicts: list[dict]
    evidence: list[dict]


def _iter_conditions(node: ConditionNode | GroupNode):
    if isinstance(node, GroupNode):
        for child in node.children:
            yield from _iter_conditions(child)
    else:
        yield node


def evaluate(ast: GroupNode, ctx: EligibilityContext) -> EngineResult:
    breakdown: list[RuleOutcomeRow] = []
    matched: list[str] = []
    failed: list[str] = []
    missing_seen: dict[str, dict] = {}
    evidence: list[dict] = []
    evidence_seen: set[tuple] = set()

    # Per-leaf breakdown (deterministic order = sort_order from compile).
    for cond in _iter_conditions(ast):
        fact = ctx.get(cond.field_key)
        outcome = evaluate_node(cond, ctx)
        breakdown.append(
            RuleOutcomeRow(
                rule_id=cond.rule_id,
                rule_code=cond.rule_code,
                field_key=cond.field_key,
                operator=cond.operator.value,
                value=cond.value,
                citizen_value=_jsonable(fact.value) if fact.known else None,
                outcome=outcome.value,
                mandatory=cond.mandatory,
                explanation=cond.explanation_text,
                source_citation=cond.source_citation,
            )
        )
        if outcome is Outcome.PASS:
            matched.append(cond.rule_code)
        elif outcome is Outcome.FAIL:
            failed.append(cond.rule_code)
        elif outcome is Outcome.UNKNOWN and cond.operator is not Operator.EXISTS:
            # Record missing/unknown info (dedup by field).
            if cond.field_key not in missing_seen:
                reason = (
                    f"{_pretty(cond.field_key)} has conflicting values and must be resolved."
                    if fact.conflicted
                    else f"{_pretty(cond.field_key)} is required."
                )
                missing_seen[cond.field_key] = {"field": cond.field_key, "reason": reason}

        # Collect evidence from source citations (never fabricated; only what
        # the rule author provided). Empty when absent (prompt §20).
        if cond.source_citation:
            key = tuple(sorted(cond.source_citation.items()))
            if key not in evidence_seen:
                evidence_seen.add(key)
                evidence.append(dict(cond.source_citation))

    # --- Decision aggregation over the top-level (mandatory-aware) tree. ---
    mandatory_children = [c for c in ast.children if _is_mandatory(c)]
    optional_children = [c for c in ast.children if not _is_mandatory(c)]

    mandatory_outcomes = [evaluate_node(c, ctx) for c in mandatory_children]
    optional_outcomes = [evaluate_node(c, ctx) for c in optional_children]

    if any(o is Outcome.FAIL for o in mandatory_outcomes):
        decision = Decision.NOT_ELIGIBLE
    elif any(o is Outcome.UNKNOWN for o in mandatory_outcomes):
        decision = Decision.INSUFFICIENT_DATA
    elif any(o is Outcome.UNKNOWN for o in optional_outcomes):
        decision = Decision.LIKELY_ELIGIBLE
    else:
        decision = Decision.ELIGIBLE

    conflicts = [
        {"field": c.field_key, "values": list(c.values), "sources": list(c.sources)}
        for c in ctx.conflicts
    ]

    return EngineResult(
        decision=decision,
        engine_version=ENGINE_VERSION,
        rule_breakdown=breakdown,
        matched_rules=matched,
        failed_rules=failed,
        missing_information=list(missing_seen.values()),
        conflicts=conflicts,
        evidence=evidence,
    )


def _is_mandatory(node: ConditionNode | GroupNode) -> bool:
    if isinstance(node, GroupNode):
        return any(_is_mandatory(c) for c in node.children)
    return node.mandatory


def _pretty(field_key: str) -> str:
    return field_key.replace("_", " ").capitalize()


def _jsonable(value: Any) -> Any:
    from datetime import date
    from decimal import Decimal

    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, date):
        return value.isoformat()
    return value
