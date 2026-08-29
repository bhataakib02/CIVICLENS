"""Rule DSL validator (rule-dsl.md §2-§4, ADR-008).

Validates untrusted rule definitions BEFORE they are stored or evaluated.
Accepts two input shapes and normalizes them:

1. Authoritative AST shape:
   {"type": "condition"|"group", ...}
2. Prompt shape:
   {"rule_code", "rule_type": "EQUALS"|"NUMERIC_COMPARISON"|"IN"|"NOT_IN"|
    "EXISTS"|"DATE_COMPARISON"|"ALL"|"ANY", "expression": {...}}

On success returns a list of normalized flat rule dicts (one per leaf
condition) ready for persistence + a normalized AST-ish structure. On failure
raises ValidationError with field_errors (never executes anything).

SECURITY: this is a pure structural validator. It NEVER calls eval/exec, never
imports rule-supplied names, and rejects any field_key outside FIELD_REGISTRY,
any operator outside the fixed set, and malformed value payloads (e.g. an
operator value of "DROP DATABASE").
"""
from __future__ import annotations

from typing import Any

from app.core.exceptions import ValidationError
from app.modules.eligibility.rule_types import (
    FIELD_REGISTRY,
    MAX_GROUP_DEPTH,
    MAX_LEAF_CONDITIONS,
    FieldType,
    GroupOperator,
    Operator,
    normalize_field_key,
    normalize_operator,
)

# Prompt rule_type -> handling.
_GROUP_RULE_TYPES = {"ALL": GroupOperator.AND, "ANY": GroupOperator.OR}
_CONDITION_RULE_TYPES = {
    "EQUALS",
    "NOT_EQUALS",
    "NUMERIC_COMPARISON",
    "DATE_COMPARISON",
    "IN",
    "NOT_IN",
    "EXISTS",
}

_NUMERIC_OPS = {Operator.GT, Operator.GTE, Operator.LT, Operator.LTE, Operator.BETWEEN}
_LIST_OPS = {Operator.IN, Operator.NOT_IN}


class RuleValidationError(ValidationError):
    code = "RULE_VALIDATION_ERROR"
    message = "One or more eligibility rules are invalid."


def _err(field_errors: list[dict]) -> None:
    raise RuleValidationError(
        "Eligibility rule failed validation.", field_errors=field_errors
    )


def _is_number(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def validate_rule_node(node: Any, *, path: str = "root", depth: int = 0) -> dict:
    """Validate a single node (condition or group). Returns a normalized node.

    Raises RuleValidationError on the first structural problem, with a
    field-path pointer so the admin UI can show exactly what's wrong.
    """
    if not isinstance(node, dict):
        _err([{"field": path, "message": "Rule node must be an object."}])

    node_type, expression = _classify(node, path)

    if node_type == "group":
        return _validate_group(node, expression, path=path, depth=depth)
    return _validate_condition(node, expression, path=path)


def _classify(node: dict, path: str) -> tuple[str, dict]:
    """Determine whether a node is a group or condition, across both shapes."""
    # Authoritative shape.
    if "type" in node:
        t = node.get("type")
        if t == "group":
            return "group", node
        if t == "condition":
            return "condition", node
        _err([{"field": f"{path}.type", "message": "type must be 'condition' or 'group'."}])

    # Prompt shape.
    rt = node.get("rule_type")
    if rt in _GROUP_RULE_TYPES:
        expr = node.get("expression")
        if not isinstance(expr, dict) or not isinstance(expr.get("rules"), list):
            _err([{"field": f"{path}.expression.rules", "message": "Group requires expression.rules[]."}])
        return "group", {"operator": _GROUP_RULE_TYPES[rt].value, "children": expr["rules"]}
    if rt in _CONDITION_RULE_TYPES:
        expr = node.get("expression")
        if not isinstance(expr, dict):
            _err([{"field": f"{path}.expression", "message": "Condition requires an expression object."}])
        merged = {
            "type": "condition",
            "field_key": expr.get("field"),
            "operator": expr.get("operator", "exists" if rt == "EXISTS" else None),
            "value": expr.get("value"),
            "mandatory": node.get("mandatory", True),
            "explanation_text": node.get("explanation_text", ""),
            "source_citation": node.get("source_citation"),
            "rule_code": node.get("rule_code"),
        }
        return "condition", merged

    _err([{"field": f"{path}", "message": "Node must declare a valid 'type' or 'rule_type'."}])
    raise AssertionError  # unreachable


def _validate_group(node: dict, expr: dict, *, path: str, depth: int) -> dict:
    if depth + 1 > MAX_GROUP_DEPTH:
        _err([{"field": path, "message": f"Group nesting exceeds max depth {MAX_GROUP_DEPTH}."}])

    op_raw = expr.get("operator")
    try:
        group_op = GroupOperator(op_raw) if op_raw in ("AND", "OR") else GroupOperator[op_raw]
    except (KeyError, ValueError):
        _err([{"field": f"{path}.operator", "message": "Group operator must be AND/OR (or ALL/ANY)."}])

    children = expr.get("children")
    if not isinstance(children, list) or not children:
        _err([{"field": f"{path}.children", "message": "Group must have a non-empty children list."}])

    norm_children = [
        validate_rule_node(child, path=f"{path}.children[{i}]", depth=depth + 1)
        for i, child in enumerate(children)
    ]
    return {"type": "group", "operator": group_op.value, "children": norm_children}


def _validate_condition(node: dict, cond: dict, *, path: str) -> dict:
    field_errors: list[dict] = []

    raw_field = cond.get("field_key", cond.get("field"))
    field_key = normalize_field_key(raw_field) if raw_field is not None else None
    if field_key is None:
        field_errors.append(
            {"field": f"{path}.field_key", "message": f"Unknown or missing field '{raw_field}'."}
        )

    raw_op = cond.get("operator")
    operator = normalize_operator(raw_op) if raw_op is not None else None
    if operator is None:
        field_errors.append(
            {"field": f"{path}.operator", "message": f"Unsupported or missing operator '{raw_op}'."}
        )

    # If either fundamental piece is bad, stop here — value checks need them.
    if field_errors:
        _err(field_errors)

    value = cond.get("value")
    spec = FIELD_REGISTRY[field_key]

    # Value/operator/type consistency.
    if operator is Operator.EXISTS:
        value = None  # exists ignores value
    elif operator in _LIST_OPS:
        if not isinstance(value, list) or not value:
            field_errors.append({"field": f"{path}.value", "message": "in/not_in require a non-empty list."})
        else:
            for i, item in enumerate(value):
                if not _value_matches_type(item, spec.type):
                    field_errors.append(
                        {"field": f"{path}.value[{i}]", "message": f"Value must be {spec.type.value}."}
                    )
    elif operator is Operator.BETWEEN:
        if not isinstance(value, list) or len(value) != 2:
            field_errors.append({"field": f"{path}.value", "message": "between requires [low, high]."})
        elif spec.type not in (FieldType.NUMBER, FieldType.INTEGER, FieldType.DATE):
            field_errors.append({"field": f"{path}.field_key", "message": "between requires a numeric/date field."})
        else:
            for i, item in enumerate(value):
                if not _value_matches_type(item, spec.type):
                    field_errors.append(
                        {"field": f"{path}.value[{i}]", "message": f"Bound must be {spec.type.value}."}
                    )
    else:
        # scalar operators eq/neq/gt/gte/lt/lte
        if operator in _NUMERIC_OPS and spec.type not in (FieldType.NUMBER, FieldType.INTEGER, FieldType.DATE):
            field_errors.append(
                {"field": f"{path}.operator", "message": f"Operator '{operator.value}' not valid for {spec.type.value} field."}
            )
        if value is None:
            field_errors.append({"field": f"{path}.value", "message": "A value is required for this operator."})
        elif not _value_matches_type(value, spec.type):
            field_errors.append(
                {"field": f"{path}.value", "message": f"Value must be {spec.type.value} for field '{field_key}'."}
            )

    explanation = cond.get("explanation_text")
    if not isinstance(explanation, str) or not explanation.strip():
        field_errors.append(
            {"field": f"{path}.explanation_text", "message": "explanation_text is required (citizen-facing)."}
        )

    citation = cond.get("source_citation")
    if citation is not None and not isinstance(citation, dict):
        field_errors.append(
            {"field": f"{path}.source_citation", "message": "source_citation must be an object if present."}
        )

    if field_errors:
        _err(field_errors)

    return {
        "type": "condition",
        "rule_code": cond.get("rule_code"),
        "field_key": field_key,
        "operator": operator.value,
        "value": value,
        "mandatory": bool(cond.get("mandatory", True)),
        "explanation_text": explanation.strip(),
        "source_citation": citation,
    }


def _value_matches_type(value: Any, ftype: FieldType) -> bool:
    if ftype in (FieldType.NUMBER,):
        return _is_number(value)
    if ftype is FieldType.INTEGER:
        return isinstance(value, int) and not isinstance(value, bool)
    if ftype is FieldType.BOOLEAN:
        return isinstance(value, bool)
    if ftype is FieldType.STRING:
        return isinstance(value, str)
    if ftype is FieldType.DATE:
        # Accept ISO date strings; reject anything else (no code, no injection).
        if not isinstance(value, str):
            return False
        from datetime import date

        try:
            date.fromisoformat(value)
            return True
        except ValueError:
            return False
    return False


def _count_leaves(node: dict) -> int:
    if node.get("type") == "group":
        return sum(_count_leaves(c) for c in node["children"])
    return 1


def validate_rule_set(rules: Any) -> dict:
    """Validate a full rule set (a list of top-level nodes or a single node).

    Returns a normalized root group node. Enforces the max-leaf-conditions
    bound across the whole set (rule-dsl.md §2).
    """
    if isinstance(rules, dict):
        top_nodes = [rules]
    elif isinstance(rules, list):
        top_nodes = rules
    else:
        _err([{"field": "rules", "message": "Rule set must be an object or a list of nodes."}])

    if not top_nodes:
        _err([{"field": "rules", "message": "Rule set must contain at least one rule."}])

    normalized = [validate_rule_node(n, path=f"rules[{i}]", depth=0) for i, n in enumerate(top_nodes)]
    root = {"type": "group", "operator": "AND", "children": normalized}

    leaves = _count_leaves(root)
    if leaves > MAX_LEAF_CONDITIONS:
        _err([{"field": "rules", "message": f"Rule set has {leaves} conditions; max is {MAX_LEAF_CONDITIONS}."}])

    return root
