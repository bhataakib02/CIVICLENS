"""Notifications outbox worker tasks package."""

from workers.notifications.tasks import process_outbox_events_task

__all__ = ["process_outbox_events_task"]
