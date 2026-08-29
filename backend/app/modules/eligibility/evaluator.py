"""Pure AST evaluator (eligibility-engine.md, prompt §8, §12).

Evaluates a compiled AST node against an EligibilityContext, producing a
pass/fail/unknown Outcome per node. This module contains the ONLY comparison
logic and it is a fixed match over the Operator enum — there is NO eval(),
NO exec(), NO dynamic attribute access, and NO database access.

Missing-fact rule (eligibility-engine.md §5): a field that is not known
(absent or conflicted) yields UNKNOWN, never a default pass/fail.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from app.modules.eligibility.context import EligibilityContext
from app.modules.eligibility.rule_types import (
    ConditionNode,
    GroupNode,
    GroupOperator,
    Operator,
    Outcome,
)


def _num(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, Decimal):
        return float(value)
    return None


def _as_date(value: Any) -> date | None:
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None
    return None


def evaluate_condition(node: ConditionNode, ctx: EligibilityContext) -> Outcome:
    fact = ctx.get(node.field_key)
    op = node.operator

    # EXISTS is special: it is about presence, not value.
    if op is Operator.EXISTS:
        return Outcome.PASS if fact.known else Outcome.FAIL

    # Any other operator on an unknown/conflicted fact => UNKNOWN.
    if not fact.known:
        return Outcome.UNKNOWN

    left = fact.value
    right = node.value

    if op is Operator.EQ:
        return _b(_eq(left, right))
    if op is Operator.NEQ:
        return _b(not _eq(left, right))
    if op in (Operator.GT, Operator.GTE, Operator.LT, Operator.LTE):
        return _compare(op, left, right)
    if op is Operator.IN:
        return _b(any(_eq(left, item) for item in right))
    if op is Operator.NOT_IN:
        return _b(not any(_eq(left, item) for item in right))
    if op is Operator.BETWEEN:
        return _between(left, right)

    return Outcome.UNKNOWN  # defensive; unreachable for validated rules


def _b(passed: bool) -> Outcome:
    return Outcome.PASS if passed else Outcome.FAIL


def _eq(left: Any, right: Any) -> bool:
    ln, rn = _num(left), _num(right)
    if ln is not None and rn is not None:
        return ln == rn
    # date-aware equality
    ld, rd = _as_date(left), _as_date(right)
    if ld is not None and rd is not None:
        return ld == rd
    return left == right


def _compare(op: Operator, left: Any, right: Any) -> Outcome:
    ln, rn = _num(left), _num(right)
    if ln is None or rn is None:
        ld, rd = _as_date(left), _as_date(right)
        if ld is None or rd is None:
            return Outcome.UNKNOWN
        ln, rn = ld.toordinal(), rd.toordinal()
    if op is Operator.GT:
        return _b(ln > rn)
    if op is Operator.GTE:
        return _b(ln >= rn)
    if op is Operator.LT:
        return _b(ln < rn)
    return _b(ln <= rn)  # LTE


def _between(left: Any, bounds: Any) -> Outcome:
    if not isinstance(bounds, (list, tuple)) or len(bounds) != 2:
        return Outcome.UNKNOWN
    low, high = bounds
    ln, lo, hi = _num(left), _num(low), _num(high)
    if None in (ln, lo, hi):
        ld, lod, hid = _as_date(left), _as_date(low), _as_date(high)
        if None in (ld, lod, hid):
            return Outcome.UNKNOWN
        ln, lo, hi = ld.toordinal(), lod.toordinal(), hid.toordinal()
    return _b(lo <= ln <= hi)


def evaluate_group(node: GroupNode, ctx: EligibilityContext) -> Outcome:
    """Three-valued AND/OR aggregation.

    AND: FAIL if any child FAILs; else UNKNOWN if any child UNKNOWN; else PASS.
    OR:  PASS if any child PASSes; else UNKNOWN if any child UNKNOWN; else FAIL.
    """
    child_outcomes = [evaluate_node(child, ctx) for child in node.children]
    if node.operator is GroupOperator.AND:
        if any(o is Outcome.FAIL for o in child_outcomes):
            return Outcome.FAIL
        if any(o is Outcome.UNKNOWN for o in child_outcomes):
            return Outcome.UNKNOWN
        return Outcome.PASS
    # OR
    if any(o is Outcome.PASS for o in child_outcomes):
        return Outcome.PASS
    if any(o is Outcome.UNKNOWN for o in child_outcomes):
        return Outcome.UNKNOWN
    return Outcome.FAIL


def evaluate_node(node: ConditionNode | GroupNode, ctx: EligibilityContext) -> Outcome:
    if isinstance(node, GroupNode):
        return evaluate_group(node, ctx)
    return evaluate_condition(node, ctx)
