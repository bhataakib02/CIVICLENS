"""Scheme + scheme-version + rule schemas (Pydantic v2).

Conform to openapi.yaml #/schemas: SchemeSummary, SchemeDetail, SchemePage,
SchemeVersion, SchemeVersionInput, DocumentRequirement, RuleOutcome. Extended
deliberately (documented in openapi.yaml) for rule authoring + version listing.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import SchemeScope, SchemeVersionStatus


# ------------------------------- Schemes ------------------------------------ #
class SchemeCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    canonical_name: str = Field(min_length=1, max_length=255)
    category: str = Field(min_length=1, max_length=64)
    scope: SchemeScope
    administering_dept: str | None = Field(default=None, max_length=255)
    code: str | None = Field(default=None, max_length=64)


class SchemeSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    canonical_name: str
    category: str
    scope: SchemeScope
    benefits_summary: str | None = None


class SchemePage(BaseModel):
    items: list[SchemeSummary]
    page: int
    page_size: int
    total: int


class DocumentRequirementOut(BaseModel):
    document_type: str
    is_mandatory: bool
    notes: str | None = None


class SchemeDetail(SchemeSummary):
    administering_dept: str | None = None
    document_requirements: list[DocumentRequirementOut] = Field(default_factory=list)
    last_verified_at: datetime | None = None
    scheme_version_id: str | None = None


# --------------------------- Scheme versions -------------------------------- #
class SchemeVersionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    benefits_summary: str = Field(min_length=1)
    effective_from: date
    effective_to: date | None = None
    knowledge_source_id: uuid.UUID | None = None


class SchemeVersionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    scheme_id: str
    version_no: int
    status: SchemeVersionStatus
    benefits_summary: str
    effective_from: date
    effective_to: date | None = None
    published_at: datetime | None = None


# -------------------------------- Rules ------------------------------------- #
class RuleInput(BaseModel):
    """A rule node (prompt or authoritative shape). Validated by validator.py."""

    model_config = ConfigDict(extra="allow")


class RuleSetInput(BaseModel):
    """Create/replace the full rule set for a draft scheme_version."""

    model_config = ConfigDict(extra="forbid")

    rules: list[dict] = Field(min_length=1)


class RuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    rule_code: str
    field_key: str
    operator: str
    value: object | None = None
    mandatory: bool
    group_id: str | None = None
    group_operator: str | None = None
    explanation_text: str
    source_citation: dict | None = None


class RuleValidateInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rules: list[dict] = Field(min_length=1)


class RuleValidateResult(BaseModel):
    valid: bool
    normalized_rule_count: int
    message: str
