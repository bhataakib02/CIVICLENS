"""Admin HTTP routes.

Endpoints for admin-only operations: dashboard metrics, audit logs, citizen
management, notification operations, user management, system health.

Agent endpoints for consent-scoped citizen access are also here to keep the
admin module self-contained.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.db.session import db_session
from app.modules.admin.schemas import (
    AuditLogPage,
    CitizenDetailAdmin,
    CitizenSummaryPage,
    ConsentOutAdmin,
    DashboardMetrics,
    NotificationOpsOut,
    NotificationOpsPage,
    SystemHealth,
    UserCreateInput,
    UserOut,
    UserPage,
    UserUpdateInput,
)
from app.modules.admin.service import AdminService
from app.modules.auth.dependencies import CurrentUser, require_authenticated_user, require_role

admin_ops_router = APIRouter(prefix="/admin", tags=["admin"])
agent_ops_router = APIRouter(prefix="/agent", tags=["agent"])

_require_staff = require_role("admin", "scheme_admin", "agent")
_require_admin = require_role("admin")


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


# ─── Dashboard ──────────────────────────────────────────────────────────────── #
@admin_ops_router.get("/dashboard", response_model=DashboardMetrics)
def get_dashboard(
    current: CurrentUser = Depends(_require_staff),
    session: Session = Depends(db_session),
) -> DashboardMetrics:
    return AdminService(session).dashboard(current)


# ─── Audit logs ─────────────────────────────────────────────────────────────── #
@admin_ops_router.get("/audit-logs", response_model=AuditLogPage)
def list_audit_logs(
    actor_id: uuid.UUID | None = Query(default=None),
    action: str | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current: CurrentUser = Depends(_require_admin),
    session: Session = Depends(db_session),
) -> AuditLogPage:
    return AdminService(session).list_audit_logs(
        current,
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )


# ─── Citizen management ─────────────────────────────────────────────────────── #
@admin_ops_router.get("/citizens", response_model=CitizenSummaryPage)
def search_citizens(
    q: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current: CurrentUser = Depends(_require_staff),
    session: Session = Depends(db_session),
) -> CitizenSummaryPage:
    return AdminService(session).search_citizens(current, q=q, page=page, page_size=page_size)


@admin_ops_router.get("/citizens/{user_id}", response_model=CitizenDetailAdmin)
def get_citizen(
    user_id: uuid.UUID,
    current: CurrentUser = Depends(_require_staff),
    session: Session = Depends(db_session),
) -> CitizenDetailAdmin:
    return AdminService(session).get_citizen(current, user_id)


@admin_ops_router.get("/citizens/{user_id}/consents", response_model=list[ConsentOutAdmin])
def citizen_consents(
    user_id: uuid.UUID,
    current: CurrentUser = Depends(_require_staff),
    session: Session = Depends(db_session),
) -> list[ConsentOutAdmin]:
    return AdminService(session).citizen_consents(current, user_id)


# ─── Notification operations ────────────────────────────────────────────────── #
@admin_ops_router.get("/notifications", response_model=NotificationOpsPage)
def list_notifications(
    status_filter: str | None = Query(default=None, alias="status"),
    channel: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current: CurrentUser = Depends(_require_admin),
    session: Session = Depends(db_session),
) -> NotificationOpsPage:
    return AdminService(session).list_notifications(
        current, status=status_filter, channel=channel, page=page, page_size=page_size
    )


@admin_ops_router.post("/notifications/{notification_id}/retry", response_model=NotificationOpsOut)
def retry_notification(
    notification_id: uuid.UUID,
    current: CurrentUser = Depends(_require_admin),
    session: Session = Depends(db_session),
) -> NotificationOpsOut:
    return AdminService(session).retry_notification(current, notification_id)


# ─── User management ────────────────────────────────────────────────────────── #
@admin_ops_router.get("/users", response_model=UserPage)
def list_users(
    role: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current: CurrentUser = Depends(_require_admin),
    session: Session = Depends(db_session),
) -> UserPage:
    return AdminService(session).list_users(current, role=role, page=page, page_size=page_size)


@admin_ops_router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    body: UserCreateInput,
    request: Request,
    current: CurrentUser = Depends(_require_admin),
    session: Session = Depends(db_session),
) -> UserOut:
    return AdminService(session).create_user(current, body, ip=_ip(request))


@admin_ops_router.patch("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: uuid.UUID,
    body: UserUpdateInput,
    request: Request,
    current: CurrentUser = Depends(_require_admin),
    session: Session = Depends(db_session),
) -> UserOut:
    return AdminService(session).update_user(current, user_id, body, ip=_ip(request))


# ─── System health ──────────────────────────────────────────────────────────── #
@admin_ops_router.get("/system-health", response_model=SystemHealth)
def system_health(
    current: CurrentUser = Depends(_require_admin),
    session: Session = Depends(db_session),
) -> SystemHealth:
    return AdminService(session).system_health(current)


# ═══ Agent endpoints ════════════════════════════════════════════════════════════ #
@agent_ops_router.get("/citizens", response_model=list[dict])
def agent_citizens(
    current: CurrentUser = Depends(require_authenticated_user),
    session: Session = Depends(db_session),
) -> list[dict]:
    return AdminService(session).agent_citizens(current)


@agent_ops_router.get("/citizens/{citizen_user_id}", response_model=CitizenDetailAdmin)
def agent_citizen_detail(
    citizen_user_id: uuid.UUID,
    current: CurrentUser = Depends(require_authenticated_user),
    session: Session = Depends(db_session),
) -> CitizenDetailAdmin:
    return AdminService(session).agent_citizen_detail(current, citizen_user_id)
