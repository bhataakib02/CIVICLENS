"""Admin API Pydantic schemas.

Request/response models for admin-only endpoints. No PII in response
models unless the caller's role is authorized (enforced by the service/router).
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


# ─── Dashboard ──────────────────────────────────────────────────────────────── #
class DashboardMetrics(BaseModel):
    applications_pending_review: int = 0
    applications_action_required: int = 0
    documents_verification_required: int = 0
    scheme_drafts_awaiting_review: int = 0
    knowledge_sources_pending: int = 0
    notifications_failed: int = 0
    total_citizens: int = 0
    total_applications: int = 0


# ─── Audit logs ─────────────────────────────────────────────────────────────── #
class AuditLogOut(BaseModel):
    id: str
    actor_user_id: str | None = None
    action: str
    entity_type: str
    entity_id: str | None = None
    diff: dict[str, Any] | None = None
    created_at: datetime


class AuditLogPage(BaseModel):
    items: list[AuditLogOut]
    total: int
    page: int
    page_size: int


# ─── Citizen management ─────────────────────────────────────────────────────── #
class CitizenSummaryAdmin(BaseModel):
    """Citizen summary for admin listing — PII minimized."""
    user_id: str
    email: str | None = None
    phone_number_masked: str | None = None
    role: str
    status: str
    created_at: datetime
    profile_completeness: float = 0.0


class CitizenSummaryPage(BaseModel):
    items: list[CitizenSummaryAdmin]
    total: int
    page: int
    page_size: int


class CitizenDetailAdmin(BaseModel):
    """Citizen detail for authorized admin/agent view."""
    user_id: str
    email: str | None = None
    phone_number_masked: str | None = None
    role: str
    status: str
    created_at: datetime

    # Profile (if exists)
    profile: dict[str, Any] | None = None
    addresses: list[dict[str, Any]] = []
    applications_count: int = 0
    documents_count: int = 0
    active_consents_count: int = 0


class ConsentOutAdmin(BaseModel):
    id: str
    citizen_id: str
    consent_type: str
    purpose: str
    scope: dict[str, Any] | None = None
    version: str
    agent_id: str | None = None
    granted_at: datetime
    revoked_at: datetime | None = None


# ─── Notification operations ────────────────────────────────────────────────── #
class NotificationOpsOut(BaseModel):
    id: str
    user_id: str | None = None
    channel: str
    category: str
    priority: str
    status: str
    title: str | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    created_at: datetime | None = None
    sent_at: datetime | None = None
    failure_code: str | None = None
    attempts: int = 0


class NotificationOpsPage(BaseModel):
    items: list[NotificationOpsOut]
    total: int
    page: int
    page_size: int


# ─── User management ────────────────────────────────────────────────────────── #
class UserOut(BaseModel):
    id: str
    email: str | None = None
    phone_number_masked: str | None = None
    role: str
    status: str
    last_login_at: datetime | None = None
    created_at: datetime


class UserPage(BaseModel):
    items: list[UserOut]
    total: int
    page: int
    page_size: int


class UserCreateInput(BaseModel):
    email: str = Field(min_length=5)
    password: str = Field(min_length=12)
    role: str = Field(description="One of: agent, scheme_admin, admin")


class UserUpdateInput(BaseModel):
    role: str | None = None
    status: str | None = None


# ─── System health ──────────────────────────────────────────────────────────── #
class SystemHealth(BaseModel):
    database: str = "unknown"
    redis: str = "unknown"
    overall: str = "unknown"
