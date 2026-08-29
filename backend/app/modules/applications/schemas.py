"""Application API schemas (Pydantic v2).

Conform to openapi.yaml Application/ApplicationDetail (extended deliberately).
Role-specific views: citizens never see reviewer-only internals (prompt §29, §54).
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ReviewAction


class ApplicationCreateInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scheme_version_id: uuid.UUID | None = None
    scheme_id: uuid.UUID | None = None  # resolves to current published version
    scheme_specific_answers: dict[str, Any] = Field(default_factory=dict)
    document_ids: list[uuid.UUID] = Field(default_factory=list)


class Application(BaseModel):
    """Matches openapi #/schemas/Application (+ application_number/scheme_version_id)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    application_number: str
    scheme_id: str
    scheme_version_id: str
    status: str
    created_at: datetime
    submitted_at: datetime | None = None


class ApplicationPage(BaseModel):
    items: list[Application]
    page: int
    page_size: int
    total: int


class StatusHistoryItem(BaseModel):
    from_status: str | None = None
    to_status: str
    note: str | None = None
    actor_role: str | None = None
    created_at: datetime


class ChecklistItemOut(BaseModel):
    document_type: str
    required: bool
    status: str
    document_id: str | None = None


class ChecklistOut(BaseModel):
    items: list[ChecklistItemOut]
    all_required_satisfied: bool


class EligibilitySummary(BaseModel):
    decision: str | None = None
    engine_version: str | None = None
    scheme_version_id: str | None = None
    evaluated_at: str | None = None


class SubmissionInfo(BaseModel):
    status: str
    submission_method: str
    external_reference: str | None = None
    submitted_at: datetime | None = None
    provider_environment: str | None = None


class ReviewInfo(BaseModel):
    assigned_case_worker_id: str | None = None
    open_actions: list[dict] = Field(default_factory=list)


class ApplicationDetail(Application):
    eligibility: EligibilitySummary
    checklist: ChecklistOut
    status_history: list[StatusHistoryItem] = Field(default_factory=list)
    attached_document_ids: list[str] = Field(default_factory=list)
    submission: SubmissionInfo | None = None
    next_actions: list[str] = Field(default_factory=list)
    # reviewer-only; populated only for case worker/admin views.
    review: ReviewInfo | None = None


# ------------------------------ workflow inputs ----------------------------- #
class SubmitInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # test-only hook honored by the mock provider; ignored by real providers.
    simulate_provider_failure: bool = False


class WithdrawInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: str | None = None


class ReviewInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: ReviewAction
    reason: str = Field(min_length=1)
    required_items: list[str] = Field(default_factory=list)


class AssignInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_worker_id: uuid.UUID | None = None  # None = unassign


class ResolveActionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    note: str | None = None
