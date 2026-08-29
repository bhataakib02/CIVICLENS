"""Notifications router (prompt §16, §18, §19).

In-app feed (list/unread-count/read/read-all) + per-user preferences under
/me/notification-preferences. Every endpoint is scoped to the authenticated
user — object-level authorization is enforced in the repository/service so a
citizen can never read or modify another user's notifications (§19).
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.session import db_session
from app.modules.audit.service import AuditAction, AuditService
from app.modules.auth.dependencies import CurrentUser, require_authenticated_user
from app.modules.notifications import preferences as prefs
from app.modules.notifications.repository import NotificationsRepository
from app.modules.notifications.schemas import (
    MarkAllReadOut,
    NotificationOut,
    NotificationPage,
    NotificationPreferencesOut,
    NotificationPreferencesUpdate,
    UnreadCountOut,
)

notifications_router = APIRouter(prefix="/notifications", tags=["notifications"])
me_notifications_router = APIRouter(prefix="/me", tags=["notifications"])


def _to_out(n) -> NotificationOut:
    return NotificationOut(
        id=str(n.id), type=n.type, channel=n.channel.value, category=n.category.value,
        priority=n.priority.value, status=n.status.value, title=n.title or n.subject,
        body=n.body, entity_type=n.entity_type,
        entity_id=str(n.entity_id) if n.entity_id else None,
        read=n.read_at is not None,
        created_at=n.created_at.isoformat() if n.created_at else None,
    )


@notifications_router.get("", response_model=NotificationPage)
@notifications_router.get("/", response_model=NotificationPage, include_in_schema=False)
def list_notifications(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    unread: bool = Query(default=False),
    type: str | None = Query(default=None),
    current: CurrentUser = Depends(require_authenticated_user),
    session: Session = Depends(db_session),
) -> NotificationPage:
    repo = NotificationsRepository(session)
    rows, total = repo.list_for_user(
        current.id, limit=page_size, offset=(page - 1) * page_size,
        unread_only=unread, type_filter=type,
    )
    return NotificationPage(items=[_to_out(n) for n in rows], total=total,
                            page=page, page_size=page_size)


@notifications_router.get("/unread-count", response_model=UnreadCountOut)
def unread_count(
    current: CurrentUser = Depends(require_authenticated_user),
    session: Session = Depends(db_session),
) -> UnreadCountOut:
    return UnreadCountOut(unread=NotificationsRepository(session).unread_count(current.id))


@notifications_router.post("/{notification_id}/read", response_model=NotificationOut)
def mark_read(
    notification_id: uuid.UUID,
    current: CurrentUser = Depends(require_authenticated_user),
    session: Session = Depends(db_session),
) -> NotificationOut:
    repo = NotificationsRepository(session)
    n = repo.get_owned(notification_id, current.id)
    if n is None:
        raise NotFoundError("Notification not found.")  # no cross-user disclosure
    repo.mark_read(n)
    AuditService(session).record(action=AuditAction.NOTIFICATION_READ, entity_type="notification",
                                 entity_id=n.id, actor_user_id=current.id)
    session.commit()
    session.refresh(n)
    return _to_out(n)


@notifications_router.post("/read-all", response_model=MarkAllReadOut)
def mark_all_read(
    current: CurrentUser = Depends(require_authenticated_user),
    session: Session = Depends(db_session),
) -> MarkAllReadOut:
    count = NotificationsRepository(session).mark_all_read(current.id)
    session.commit()
    return MarkAllReadOut(marked_read=count)


# ---------- Preferences (prompt §16) ----------
@me_notifications_router.get("/notification-preferences", response_model=NotificationPreferencesOut)
def get_preferences(
    current: CurrentUser = Depends(require_authenticated_user),
    session: Session = Depends(db_session),
) -> NotificationPreferencesOut:
    pref = prefs.get_or_create(session, current.id)
    session.commit()
    return NotificationPreferencesOut(**prefs.as_dict(pref))


@me_notifications_router.put("/notification-preferences", response_model=NotificationPreferencesOut)
def update_preferences(
    body: NotificationPreferencesUpdate,
    current: CurrentUser = Depends(require_authenticated_user),
    session: Session = Depends(db_session),
) -> NotificationPreferencesOut:
    pref = prefs.get_or_create(session, current.id)
    prefs.apply_update(pref, body.model_dump(exclude_none=True))
    AuditService(session).record(
        action=AuditAction.NOTIFICATION_PREFERENCES_CHANGED, entity_type="user",
        entity_id=current.id, actor_user_id=current.id,
    )
    session.commit()
    session.refresh(pref)
    return NotificationPreferencesOut(**prefs.as_dict(pref))
