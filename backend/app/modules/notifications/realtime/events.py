"""Real-time event fan-out helper (prompt §20).

Turns a persisted notification into a PII-light real-time message and publishes
it via the configured pub/sub backend. Synchronous callers (the worker) schedule
the async publish safely.
"""
from __future__ import annotations

import asyncio
import uuid

from app.core.logging import get_logger
from app.modules.notifications.realtime.manager import get_pubsub

logger = get_logger("civiclens.notifications.realtime")


def build_message(*, notification_id: uuid.UUID, event_type: str, title: str | None,
                  category: str, priority: str, entity_type: str | None,
                  entity_id: uuid.UUID | None) -> dict:
    return {
        "kind": "notification",
        "notification_id": str(notification_id),
        "event_type": event_type,
        "title": title,
        "category": category,
        "priority": priority,
        "entity_type": entity_type,
        "entity_id": str(entity_id) if entity_id else None,
    }


async def publish_async(user_id: uuid.UUID, message: dict) -> None:
    await get_pubsub().publish(user_id, message)


def publish_sync(user_id: uuid.UUID, message: dict) -> None:
    """Publish from synchronous code (the outbox worker).

    If an event loop is already running (e.g. inside the ASGI app) schedule the
    coroutine; otherwise run it to completion. Real-time delivery is best-effort
    and must never fail the notification transaction (prompt §20).
    """
    try:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            loop.create_task(publish_async(user_id, message))
        else:
            asyncio.run(publish_async(user_id, message))
    except Exception:
        logger.warning("realtime_publish_failed", extra={"user_id": str(user_id)})
