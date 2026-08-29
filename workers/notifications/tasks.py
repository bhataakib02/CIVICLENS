"""Notifications and outbox event dispatch Celery tasks (ADR-006).

Wraps ``backend/app/modules/notifications/service.py`` outbox dispatcher.
"""

from __future__ import annotations

from app.core.config import get_settings
from app.modules.notifications.service import OutboxDispatcher
from workers.celery_app import celery_app


def _get_task_decorator():
    if hasattr(celery_app, "task"):
        return celery_app.task(name="workers.notifications.process_outbox", bind=True)
    return lambda fn: fn


@_get_task_decorator()
def process_outbox_events_task() -> int:
    """Async task to drain pending outbox events into notifications."""
    settings = get_settings()
    dispatched_count = OutboxDispatcher(settings=settings).dispatch_pending()
    return dispatched_count
