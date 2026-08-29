"""Eligibility DSL core types — the closed grammar (ADR-008, rule-dsl.md).

This module is pure data/type definitions and small helpers. It contains NO
evaluation logic and NO database access. Rules are DATA; nothing here (or
anywhere in this module) uses eval/exec or dynamic code execution.

Vocabulary reconciliation (authoritative contract vs. Prompt 2 wording):
- Operators use the authoritative set (eq/neq/gt/gte/lt/lte/in/not_in/exists/
  between). The prompt's rule_type names (EQUALS, NUMERIC_COMPARISON, IN,
  NOT_IN, EXISTS, DATE_COMPARISON, ALL, ANY) and Python-style operator symbols
  (==, >=, <=, ...) are accepted at the validator/compiler boundary and
  normalized to this set; ALL->AND group, ANY->OR group.
- Field keys use the whitelist that maps to real citizen_profiles/addresses
  columns (data-dictionary + rule-dsl.md §3). Prompt-style dotted aliases
  (citizen.age, citizen.address.state, ...) are accepted and normalized here.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import date
from typing import Any

# --------------------------------------------------------------------------- #
# Engine version — single source of truth (prompt §22). Persisted on every
# eligibility_checks row; future engine behavior changes bump this.
# --------------------------------------------------------------------------- #
ENGINE_VERSION = "1.0.0"

# Grammar bounds (rule-dsl.md §2).
MAX_GROUP_DEPTH = 4
MAX_LEAF_CONDITIONS = 20


class Operator(str, enum.Enum):
    EQ = "eq"
    NEQ = "neq"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    IN = "in"
    NOT_IN = "not_in"
    EXISTS = "exists"
    BETWEEN = "between"


class GroupOperator(str, enum.Enum):
    AND = "AND"
    OR = "OR"


class Outcome(str, enum.Enum):
    """Per-rule evaluation outcome."""

    PASS = "pass"
    FAIL = "fail"
    UNKNOWN = "unknown"


class Decision(str, enum.Enum):
    """Aggregate result (matches openapi EligibilityResult enum)."""

    ELIGIBLE = "eligible"
    NOT_ELIGIBLE = "not_eligible"
    LIKELY_ELIGIBLE = "likely_eligible"
    INSUFFICIENT_DATA = "insufficient_data"


# --------------------------------------------------------------------------- #
# Field registry: field_key -> type descriptor. The engine rejects any
# field_key not present here (rule-dsl.md §3 — no arbitrary object traversal).
# --------------------------------------------------------------------------- #
class FieldType(str, enum.Enum):
    NUMBER = "number"
    STRING = "string"
    BOOLEAN = "boolean"
    DATE = "date"
    INTEGER = "integer"


@dataclass(frozen=True)
class FieldSpec:
    key: str
    type: FieldType
    # source: "profile" | "address" | "derived" | "document"
    source: str
    description: str


# Canonical whitelist. Keys are the canonical field_key values stored in
# eligibility_rules.field_key.
FIELD_REGISTRY: dict[str, FieldSpec] = {
    "age": FieldSpec("age", FieldType.INTEGER, "derived", "Citizen age in whole years (from date_of_birth)."),
    "date_of_birth": FieldSpec("date_of_birth", FieldType.DATE, "profile", "Citizen date of birth."),
    "declared_annual_income": FieldSpec(
        "declared_annual_income", FieldType.NUMBER, "profile", "Self-declared annual household income."
    ),
    "gender": FieldSpec("gender", FieldType.STRING, "profile", "Citizen gender."),
    "category": FieldSpec("category", FieldType.STRING, "profile", "Social/caste category."),
    "occupation": FieldSpec("occupation", FieldType.STRING, "profile", "Citizen occupation."),
    "employment_status": FieldSpec(
        "employment_status", FieldType.STRING, "profile", "Employment status (mapped to occupation)."
    ),
    "education_level": FieldSpec(
        "education_level", FieldType.STRING, "profile", "Highest education level."
    ),
    "disability_status": FieldSpec(
        "disability_status", FieldType.BOOLEAN, "profile", "Whether the citizen has a disability status."
    ),
    "family_size": FieldSpec("family_size", FieldType.INTEGER, "profile", "Number of household members."),
    "household_size": FieldSpec(
        "household_size", FieldType.INTEGER, "profile", "Alias of family_size."
    ),
    "state": FieldSpec("state", FieldType.STRING, "address", "State of the citizen's primary address."),
    "district": FieldSpec("district", FieldType.STRING, "address", "District of the primary address."),
    "pincode": FieldSpec("pincode", FieldType.STRING, "address", "Postal code of the primary address."),
    "postal_code": FieldSpec("postal_code", FieldType.STRING, "address", "Alias of pincode."),
}

# Aliases: prompt-style dotted field paths -> canonical field_key.
FIELD_ALIASES: dict[str, str] = {
    "citizen.age": "age",
    "citizen.date_of_birth": "date_of_birth",
    "citizen.annual_income": "declared_annual_income",
    "citizen.declared_annual_income": "declared_annual_income",
    "citizen.gender": "gender",
    "citizen.category": "category",
    "citizen.occupation": "occupation",
    "citizen.employment_status": "employment_status",
    "citizen.education_level": "education_level",
    "citizen.disability_status": "disability_status",
    "citizen.household_size": "household_size",
    "citizen.family_size": "family_size",
    "citizen.address.state": "state",
    "citizen.address.district": "district",
    "citizen.address.postal_code": "postal_code",
    "citizen.address.pincode": "pincode",
}

# Some canonical keys are aliases of a stored column — normalize on read.
CANONICAL_ALIAS: dict[str, str] = {
    "household_size": "family_size",
    "postal_code": "pincode",
    # employment_status/education_level have no dedicated column yet; resolved
    # from the facts mapping (occupation / explicit facts) in context.py.
}

# Operator name normalization (prompt rule_type + symbol forms -> Operator).
_OPERATOR_SYMBOLS: dict[str, Operator] = {
    "==": Operator.EQ,
    "eq": Operator.EQ,
    "equals": Operator.EQ,
    "!=": Operator.NEQ,
    "neq": Operator.NEQ,
    "not_equals": Operator.NEQ,
    ">": Operator.GT,
    "gt": Operator.GT,
    ">=": Operator.GTE,
    "gte": Operator.GTE,
    "<": Operator.LT,
    "lt": Operator.LT,
    "<=": Operator.LTE,
    "lte": Operator.LTE,
    "in": Operator.IN,
    "not_in": Operator.NOT_IN,
    "exists": Operator.EXISTS,
    "between": Operator.BETWEEN,
}


def normalize_operator(raw: str) -> Operator | None:
    if not isinstance(raw, str):
        return None
    token = raw.strip()
    # Symbol forms are matched literally; word forms are case-insensitive.
    return _OPERATOR_SYMBOLS.get(token) or _OPERATOR_SYMBOLS.get(token.lower())


def normalize_field_key(raw: str) -> str | None:
    """Return the canonical field_key for a raw/aliased key, or None if unknown."""
    if not isinstance(raw, str):
        return None
    key = raw.strip()
    if key in FIELD_REGISTRY:
        return key
    if key in FIELD_ALIASES:
        return FIELD_ALIASES[key]
    return None


# --------------------------------------------------------------------------- #
# In-memory AST (produced by compiler.py from validated rules).
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ConditionNode:
    rule_id: str | None
    rule_code: str
    field_key: str
    operator: Operator
    value: Any
    mandatory: bool
    explanation_text: str
    source_citation: dict | None = None


@dataclass(frozen=True)
class GroupNode:
    operator: GroupOperator
    children: tuple["ConditionNode | GroupNode", ...] = field(default_factory=tuple)
    # A group is mandatory if it contains any mandatory descendant condition.
    mandatory: bool = True
