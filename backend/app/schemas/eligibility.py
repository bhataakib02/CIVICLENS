"""Eligibility request/response schemas (Pydantic v2).

EligibilityResult conforms to openapi.yaml #/schemas/EligibilityResult and
#/schemas/RuleOutcome, extended deliberately (documented in openapi.yaml) with
engine_version, matched_rules, failed_rules, missing_information, conflicts,
evidence, decision alias, and explanation.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import EligibilityResult as ResultEnum


class EligibilityCheckInput(BaseModel):
    """POST /eligibility/check body.

    Either scheme_id (contract) or scheme_version_id (prompt §16) may be given.
    scheme_id resolves to the scheme's current published version. citizen_id is
    intentionally NOT accepted — identity is derived from the authenticated
    principal (prompt §16).
    """

    model_config = ConfigDict(extra="forbid")

    scheme_id: uuid.UUID | None = None
    scheme_version_id: uuid.UUID | None = None
    facts: dict[str, Any] = Field(default_factory=dict)


class RuleOutcome(BaseModel):
    rule_id: str | None = None
    rule_code: str
    field_key: str
    operator: str
    value: Any | None = None
    citizen_value: Any | None = None
    outcome: str
    mandatory: bool
    explanation: str
    source_citation: dict | None = None


class MissingInfo(BaseModel):
    field: str
    reason: str


class ConflictInfo(BaseModel):
    field: str
    values: list[Any]
    sources: list[str]


class EligibilityResultOut(BaseModel):
    id: str
    citizen_id: str
    scheme_id: str
    scheme_version_id: str
    result: ResultEnum
    decision: ResultEnum  # alias of result, in the prompt's vocabulary
    engine_version: str
    matched_rules: list[str]
    failed_rules: list[str]
    missing_information: list[MissingInfo]
    conflicts: list[ConflictInfo]
    evidence: list[dict]
    rule_breakdown: list[RuleOutcome]
    explanation: str
    computed_at: datetime
    created_at: datetime
