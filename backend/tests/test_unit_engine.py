"""Unit tests: evaluator (all operators + AND/OR + unknown) and engine
decisions (eligible/not_eligible/insufficient_data/likely_eligible +
conflict) + determinism/immutability (prompt §27, no DB)."""
from __future__ import annotations

import uuid
from datetime import date
from types import SimpleNamespace

import pytest

from app.modules.eligibility.compiler import compile_rows, flatten_rule_set
from app.modules.eligibility.context import ContextBuilder
from app.modules.eligibility.engine import evaluate
from app.modules.eligibility.rule_types import Decision, Outcome
from app.modules.eligibility.validator import validate_rule_set

pytestmark = pytest.mark.unit


def _compile(rules: list[dict]):
    root = validate_rule_set(rules)
    flat = flatten_rule_set(root)
    rows = []
    for i, r in enumerate(flat):
        d = dict(r)
        d["id"] = uuid.uuid4()
        d["sort_order"] = i
        d.setdefault("parent_group_id", None)
        rows.append(SimpleNamespace(**d))
    return compile_rows(rows)


def _profile(**over):
    base = dict(
        id=uuid.uuid4(),
        current_version_no=1,
        date_of_birth=date(2000, 1, 1),
        declared_annual_income=None,
        gender=None,
        category=None,
        occupation=None,
        disability_status=None,
        family_size=None,
    )
    base.update(over)
    return SimpleNamespace(**base)


def _ctx(profile, address=None, facts=None):
    return ContextBuilder().build(
        citizen_profile=profile,
        primary_address=address,
        evaluation_date=date(2026, 1, 1),
        scheme_version_id=uuid.uuid4(),
        extra_facts=facts,
    )


def _cond(field_key, operator, value=None, mandatory=True, code=None):
    c = {"type": "condition", "field_key": field_key, "operator": operator,
         "explanation_text": f"{field_key} {operator} {value}.", "mandatory": mandatory}
    if value is not None:
        c["value"] = value
    if code:
        c["rule_code"] = code
    return c


# ------------------------------ operators ----------------------------------- #
@pytest.mark.parametrize(
    "operator,value,income,expected",
    [
        ("eq", 100, 100, Outcome.PASS),
        ("eq", 100, 101, Outcome.FAIL),
        ("neq", 100, 101, Outcome.PASS),
        ("gt", 100, 101, Outcome.PASS),
        ("gt", 100, 100, Outcome.FAIL),
        ("gte", 100, 100, Outcome.PASS),
        ("lt", 100, 99, Outcome.PASS),
        ("lte", 100, 100, Outcome.PASS),
        ("lte", 100, 101, Outcome.FAIL),
        ("between", [100, 200], 150, Outcome.PASS),
        ("between", [100, 200], 250, Outcome.FAIL),
    ],
)
def test_numeric_operators(operator, value, income, expected):
    ast = _compile([_cond("declared_annual_income", operator, value)])
    res = evaluate(ast, _ctx(_profile(declared_annual_income=income)))
    assert res.rule_breakdown[0].outcome == expected.value


def test_in_and_not_in():
    ast_in = _compile([_cond("category", "in", ["SC", "ST"])])
    assert evaluate(ast_in, _ctx(_profile(category="SC"))).rule_breakdown[0].outcome == "pass"
    assert evaluate(ast_in, _ctx(_profile(category="OBC"))).rule_breakdown[0].outcome == "fail"
    ast_ni = _compile([_cond("category", "not_in", ["SC", "ST"])])
    assert evaluate(ast_ni, _ctx(_profile(category="OBC"))).rule_breakdown[0].outcome == "pass"


def test_exists():
    ast = _compile([_cond("declared_annual_income", "exists")])
    assert evaluate(ast, _ctx(_profile(declared_annual_income=1))).rule_breakdown[0].outcome == "pass"
    assert evaluate(ast, _ctx(_profile(declared_annual_income=None))).rule_breakdown[0].outcome == "fail"


def test_date_comparison():
    ast = _compile([_cond("date_of_birth", "lte", "2010-01-01")])
    # born 2000 -> dob <= 2010 -> pass
    assert evaluate(ast, _ctx(_profile(date_of_birth=date(2000, 1, 1)))).rule_breakdown[0].outcome == "pass"
    assert evaluate(ast, _ctx(_profile(date_of_birth=date(2015, 1, 1)))).rule_breakdown[0].outcome == "fail"


def test_unknown_when_fact_missing():
    ast = _compile([_cond("declared_annual_income", "lte", 250000)])
    res = evaluate(ast, _ctx(_profile(declared_annual_income=None)))
    assert res.rule_breakdown[0].outcome == "unknown"


# ------------------------------ AND / OR ------------------------------------- #
def test_and_group_semantics():
    rules = [{
        "type": "group", "operator": "AND",
        "children": [_cond("age", "gte", 18), _cond("declared_annual_income", "lte", 250000)],
    }]
    ast = _compile(rules)
    # both pass
    r = evaluate(ast, _ctx(_profile(date_of_birth=date(2000, 1, 1), declared_annual_income=1000)))
    assert r.decision is Decision.ELIGIBLE
    # one fails -> not eligible
    r2 = evaluate(ast, _ctx(_profile(date_of_birth=date(2000, 1, 1), declared_annual_income=999999)))
    assert r2.decision is Decision.NOT_ELIGIBLE


def test_or_group_semantics():
    rules = [{
        "type": "group", "operator": "OR",
        "children": [_cond("category", "in", ["SC"]), _cond("disability_status", "eq", True)],
    }]
    ast = _compile(rules)
    r = evaluate(ast, _ctx(_profile(category="SC", disability_status=False)))
    assert r.decision is Decision.ELIGIBLE
    r2 = evaluate(ast, _ctx(_profile(category="OBC", disability_status=False)))
    assert r2.decision is Decision.NOT_ELIGIBLE


# ------------------------------ decisions ------------------------------------ #
def _scheme_a():
    return _compile([
        _cond("age", "gte", 18, code="AGE"),
        _cond("declared_annual_income", "lte", 250000, code="INCOME"),
        _cond("state", "eq", "West Bengal", code="STATE"),
    ])


def _addr(state="West Bengal"):
    return SimpleNamespace(state=state, district="D", pincode="700001")


def test_decision_eligible():
    ast = _scheme_a()
    res = evaluate(ast, _ctx(_profile(date_of_birth=date(2000, 1, 1), declared_annual_income=100000), _addr()))
    assert res.decision is Decision.ELIGIBLE
    assert set(res.matched_rules) == {"AGE", "INCOME", "STATE"}
    assert res.failed_rules == []


def test_decision_not_eligible():
    ast = _scheme_a()
    res = evaluate(ast, _ctx(_profile(date_of_birth=date(2000, 1, 1), declared_annual_income=999999), _addr()))
    assert res.decision is Decision.NOT_ELIGIBLE
    assert "INCOME" in res.failed_rules


def test_decision_insufficient_data():
    ast = _scheme_a()
    res = evaluate(ast, _ctx(_profile(date_of_birth=date(2000, 1, 1), declared_annual_income=None), _addr()))
    assert res.decision is Decision.INSUFFICIENT_DATA
    assert any(m["field"] == "declared_annual_income" for m in res.missing_information)


def test_decision_likely_eligible_optional_unknown():
    # mandatory age passes; optional category unknown -> likely_eligible
    ast = _compile([
        _cond("age", "gte", 18, mandatory=True, code="AGE"),
        _cond("category", "in", ["SC", "ST"], mandatory=False, code="CAT"),
    ])
    res = evaluate(ast, _ctx(_profile(date_of_birth=date(2000, 1, 1), category=None)))
    assert res.decision is Decision.LIKELY_ELIGIBLE


def test_conflict_detected_and_insufficient():
    ast = _scheme_a()
    # profile income 200000 vs request fact 350000 -> conflict on income
    res = evaluate(
        ast,
        _ctx(_profile(date_of_birth=date(2000, 1, 1), declared_annual_income=200000), _addr(),
             facts={"citizen.annual_income": 350000}),
    )
    assert res.decision is Decision.INSUFFICIENT_DATA
    assert any(c["field"] == "declared_annual_income" for c in res.conflicts)


# ------------------------------ determinism ---------------------------------- #
def test_determinism_repeated_runs_identical():
    ast = _scheme_a()
    prof = _profile(date_of_birth=date(2000, 1, 1), declared_annual_income=100000)
    results = [evaluate(ast, _ctx(prof, _addr())) for _ in range(5)]
    decisions = {r.decision for r in results}
    matched = {tuple(r.matched_rules) for r in results}
    assert len(decisions) == 1
    assert len(matched) == 1


def test_engine_does_not_mutate_context():
    ast = _scheme_a()
    ctx = _ctx(_profile(date_of_birth=date(2000, 1, 1), declared_annual_income=100000), _addr())
    facts_before = dict(ctx.facts)
    evaluate(ast, ctx)
    assert ctx.facts == facts_before


def test_no_eval_exec_in_engine_sources():
    # Static guard: the engine modules must not CALL eval/exec. Uses AST so
    # that the words appearing in docstrings/comments don't false-positive.
    import ast
    import pathlib

    base = pathlib.Path(__file__).resolve().parent.parent / "app" / "modules" / "eligibility"
    banned = {"eval", "exec", "compile", "__import__"}
    for fname in ("evaluator.py", "engine.py", "validator.py", "compiler.py", "context.py"):
        tree = ast.parse((base / fname).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in banned, f"{fname} calls {node.func.id}()"
