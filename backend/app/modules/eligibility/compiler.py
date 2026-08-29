"""Rule compiler (eligibility-engine.md §4).

Two directions:
1. flatten_rule_set(root) -> list[flat rule dicts] for persistence into
   eligibility_rules (one row per leaf condition; groups encoded via
   group_id/group_operator/parent_group_id).
2. compile_rows(rows) -> GroupNode AST for evaluation. Cached in-process per
   scheme_version_id (invalidated when a version's rules change / a new
   version is published).

Pure functions; no DB access, no eval/exec.
"""
from __future__ import annotations

import threading
import uuid
from typing import Any

from app.modules.eligibility.rule_types import (
    ConditionNode,
    GroupNode,
    GroupOperator,
    Operator,
)

# --------------------------------------------------------------------------- #
# Persistence direction: normalized AST -> flat rows.
# --------------------------------------------------------------------------- #
def flatten_rule_set(root: dict) -> list[dict]:
    """Flatten a validated root group into storable eligibility_rules rows.

    The root group is implicit (AND); its children are stored with a group_id
    that identifies each nested group. Auto-generates rule_code where absent.
    """
    rows: list[dict] = []
    counter = {"n": 0}

    # Root is AND; its direct children belong to the implicit root group (None).
    for child in root["children"]:
        _walk_child(child, None, "AND", None, rows, counter)

    for i, r in enumerate(rows):
        r["sort_order"] = i
    return rows


def _new_group_id(counter: dict) -> str:
    counter["n"] += 1
    return f"g{counter['n']}"


def _walk_child(
    node: dict,
    group_id: str | None,
    group_operator: str | None,
    parent_group_id: str | None,
    rows: list[dict],
    counter: dict,
) -> None:
    if node["type"] == "condition":
        rows.append(_condition_row(node, group_id, group_operator, counter))
    else:
        gid = _new_group_id(counter)
        for child in node["children"]:
            _walk_child(child, gid, node["operator"], group_id, rows, counter)


def _condition_row(node: dict, group_id: str | None, group_operator: str | None, counter: dict) -> dict:
    code = node.get("rule_code")
    if not code:
        counter["code"] = counter.get("code", 0) + 1
        code = f"{node['field_key'].upper()}_{node['operator'].upper()}_{counter['code']}"
    return {
        "rule_code": code,
        "field_key": node["field_key"],
        "operator": node["operator"],
        "value": node["value"],
        "mandatory": node["mandatory"],
        "group_id": group_id,
        "group_operator": group_operator if group_id is not None else None,
        "parent_group_id": None,
        "explanation_text": node["explanation_text"],
        "source_citation": node.get("source_citation"),
    }


# --------------------------------------------------------------------------- #
# Evaluation direction: flat rows -> AST.
# --------------------------------------------------------------------------- #
def compile_rows(rows: list[Any]) -> GroupNode:
    """Rebuild the evaluation AST from stored rule rows.

    Rows sharing a group_id form an OR/AND group (per their group_operator);
    rows with group_id=None are direct children of the implicit root AND-group.
    """
    root_children: list[ConditionNode | GroupNode] = []
    groups: dict[str, list[ConditionNode]] = {}
    group_ops: dict[str, str] = {}

    ordered = sorted(rows, key=lambda r: getattr(r, "sort_order", 0))
    for r in ordered:
        cond = ConditionNode(
            rule_id=str(r.id) if getattr(r, "id", None) is not None else None,
            rule_code=r.rule_code,
            field_key=r.field_key,
            operator=Operator(r.operator),
            value=r.value,
            mandatory=r.mandatory,
            explanation_text=r.explanation_text,
            source_citation=r.source_citation,
        )
        if r.group_id is None:
            root_children.append(cond)
        else:
            groups.setdefault(r.group_id, []).append(cond)
            if r.group_operator:
                group_ops[r.group_id] = r.group_operator

    for gid, conds in groups.items():
        op = GroupOperator(group_ops.get(gid, "AND"))
        mandatory = any(c.mandatory for c in conds)
        root_children.append(GroupNode(operator=op, children=tuple(conds), mandatory=mandatory))

    return GroupNode(operator=GroupOperator.AND, children=tuple(root_children), mandatory=True)


# --------------------------------------------------------------------------- #
# Per-scheme_version compiled-AST cache (eligibility-engine.md §4).
# --------------------------------------------------------------------------- #
class RuleCache:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._cache: dict[str, GroupNode] = {}

    def get_or_compile(self, scheme_version_id: uuid.UUID, rows: list[Any]) -> GroupNode:
        key = str(scheme_version_id)
        with self._lock:
            ast = self._cache.get(key)
            if ast is None:
                ast = compile_rows(rows)
                self._cache[key] = ast
            return ast

    def invalidate(self, scheme_version_id: uuid.UUID) -> None:
        with self._lock:
            self._cache.pop(str(scheme_version_id), None)

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()


rule_cache = RuleCache()
