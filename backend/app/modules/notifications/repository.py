"""Notifications persistence layer (prompt §18, §19, §49).

All queries are scoped by recipient_user_id (object-level authorization is
enforced here + in the service): a user can only ever read/modify their own
notifications. List is paginated + uses the (recipient_user_id, created_at)
index; unread-count uses the partial unread index.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models.enums import NotificationChannel, NotificationStatus
from app.models.notification import Notification


class NotificationsRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_owned(self, notification_id: uuid.UUID, user_id: uuid.UUID) -> Notification | None:
        return self._session.scalar(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.recipient_user_id == user_id,
            )
        )

    def list_for_user(
        self, user_id: uuid.UUID, *, limit: int, offset: int,
        unread_only: bool = False, type_filter: str | None = None,
    ) -> tuple[list[Notification], int]:
        base = select(Notification).where(
            Notification.recipient_user_id == user_id,
            # The in-app feed shows the in_app channel (email/sms are external).
            Notification.channel == NotificationChannel.IN_APP,
        )
        if unread_only:
            base = base.where(Notification.read_at.is_(None))
        if type_filter:
            base = base.where(Notification.type == type_filter)
        total = int(self._session.scalar(
            select(func.count()).select_from(base.subquery())
        ) or 0)
        rows = list(self._session.scalars(
            base.order_by(Notification.created_at.desc(), Notification.id)
            .limit(limit).offset(offset)
        ))
        return rows, total

    def unread_count(self, user_id: uuid.UUID) -> int:
        return int(self._session.scalar(
            select(func.count()).select_from(Notification).where(
                Notification.recipient_user_id == user_id,
                Notification.channel == NotificationChannel.IN_APP,
                Notification.read_at.is_(None),
            )
        ) or 0)

    def mark_read(self, notification: Notification) -> None:
        if notification.read_at is None:
            notification.read_at = datetime.now(timezone.utc)
        self._session.flush()

    def mark_all_read(self, user_id: uuid.UUID) -> int:
        now = datetime.now(timezone.utc)
        res = self._session.execute(
            update(Notification)
            .where(
                Notification.recipient_user_id == user_id,
                Notification.channel == NotificationChannel.IN_APP,
                Notification.read_at.is_(None),
            )
            .values(read_at=now)
        )
        self._session.flush()
        return res.rowcount or 0
