"""Unit tests: rule DSL validator (prompt §27, no DB)."""
from __future__ import annotations

import pytest

from app.core.exceptions import ValidationError
from app.modules.eligibility.validator import validate_rule_node, validate_rule_set

pytestmark = pytest.mark.unit


def _cond(**over):
    base = {
        "type": "condition",
        "field_key": "age",
        "operator": "gte",
        "value": 18,
        "explanation_text": "Must be 18+.",
    }
    base.update(over)
    return base


def test_valid_equals():
    node = validate_rule_node(_cond(field_key="state", operator="eq", value="West Bengal"))
    assert node["operator"] == "eq"
    assert node["field_key"] == "state"


def test_valid_equals_prompt_shape():
    node = validate_rule_node(
        {
            "rule_code": "STATE",
            "rule_type": "EQUALS",
            "expression": {"field": "citizen.address.state", "operator": "==", "value": "West Bengal"},
            "explanation_text": "Must live in WB.",
        }
    )
    assert node["field_key"] == "state"
    assert node["operator"] == "eq"


def test_invalid_equals_wrong_value_type():
    with pytest.raises(ValidationError):
        validate_rule_node(_cond(field_key="state", operator="eq", value=123))


def test_valid_numeric_comparison():
    node = validate_rule_node(_cond(field_key="declared_annual_income", operator="lte", value=250000))
    assert node["operator"] == "lte"


def test_invalid_operator_rejected():
    with pytest.raises(ValidationError):
        validate_rule_node(_cond(operator="DROP DATABASE"))


def test_injection_shaped_rule_rejected():
    # The prompt's explicit malformed example: operator "DROP DATABASE", no value.
    with pytest.raises(ValidationError):
        validate_rule_node(
            {
                "rule_type": "NUMERIC_COMPARISON",
                "expression": {"field": "citizen.age", "operator": "DROP DATABASE"},
                "explanation_text": "x",
            }
        )


def test_invalid_field_rejected():
    with pytest.raises(ValidationError):
        validate_rule_node(_cond(field_key="citizen.secret_field"))


def test_unknown_dotted_field_rejected():
    with pytest.raises(ValidationError):
        validate_rule_node(_cond(field_key="citizen.address.gps_coordinates"))


def test_missing_expression_rejected():
    with pytest.raises(ValidationError):
        validate_rule_node({"rule_type": "EQUALS", "explanation_text": "x"})


def test_missing_explanation_rejected():
    with pytest.raises(ValidationError):
        validate_rule_node({"type": "condition", "field_key": "age", "operator": "gte", "value": 18})


def test_numeric_operator_on_string_field_rejected():
    with pytest.raises(ValidationError):
        validate_rule_node(_cond(field_key="state", operator="gte", value=5))


def test_in_requires_list():
    with pytest.raises(ValidationError):
        validate_rule_node(_cond(field_key="category", operator="in", value="SC"))


def test_between_requires_two_bounds():
    with pytest.raises(ValidationError):
        validate_rule_node(_cond(field_key="age", operator="between", value=[18]))


def test_valid_between():
    node = validate_rule_node(_cond(field_key="age", operator="between", value=[18, 60]))
    assert node["operator"] == "between"


def test_exists_ignores_value():
    node = validate_rule_node(
        {"type": "condition", "field_key": "declared_annual_income", "operator": "exists",
         "explanation_text": "Income must be declared."}
    )
    assert node["operator"] == "exists"
    assert node["value"] is None


def test_valid_nested_group_all_any():
    rule = {
        "type": "group",
        "operator": "AND",
        "children": [
            _cond(field_key="age", operator="gte", value=18),
            {
                "type": "group",
                "operator": "OR",
                "children": [
                    _cond(field_key="category", operator="in", value=["SC", "ST"]),
                    _cond(field_key="disability_status", operator="eq", value=True),
                ],
            },
        ],
    }
    node = validate_rule_node(rule)
    assert node["type"] == "group"
    assert len(node["children"]) == 2


def test_prompt_all_group_shape():
    rule = {
        "rule_code": "COMBINED",
        "rule_type": "ALL",
        "expression": {
            "rules": [
                {"rule_type": "EQUALS", "expression": {"field": "citizen.employment_status", "operator": "==", "value": "UNEMPLOYED"}, "explanation_text": "Unemployed."},
                {"rule_type": "NUMERIC_COMPARISON", "expression": {"field": "citizen.age", "operator": ">=", "value": 18}, "explanation_text": "18+."},
            ]
        },
    }
    node = validate_rule_node(rule)
    assert node["type"] == "group"
    assert node["operator"] == "AND"


def test_deep_nesting_beyond_max_depth_rejected():
    # depth 5 groups > MAX_GROUP_DEPTH (4)
    node = _cond()
    for _ in range(5):
        node = {"type": "group", "operator": "AND", "children": [node]}
    with pytest.raises(ValidationError):
        validate_rule_node(node)


def test_rule_set_leaf_limit_enforced():
    rules = [_cond(field_key="age", operator="gte", value=18) for _ in range(21)]
    with pytest.raises(ValidationError):
        validate_rule_set(rules)


def test_empty_rule_set_rejected():
    with pytest.raises(ValidationError):
        validate_rule_set([])
