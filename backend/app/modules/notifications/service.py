"""Transactional outbox writer + event worker/dispatcher (prompt §7, §8, §31, §32).

OutboxWriter.enqueue writes an outbox_events row (full envelope) into the
CALLER's transaction — no commit — so a domain state change and its event commit
atomically (prompt §7). A per-aggregate sequence_no is assigned from a DB
sequence for per-aggregate ordering (prompt §34).

OutboxDispatcher is the worker. It claims a batch of due PENDING events with
FOR UPDATE SKIP LOCKED (prompt §8 — safe for concurrent workers), invokes the
NotificationOrchestrator for each, and:
  * success  -> status DISPATCHED, published_at set;
  * retryable failure -> attempt_count++, next_attempt_at = backoff, status
    back to PENDING; when attempts are exhausted -> DEAD_LETTER + dead_letter row
    (prompt §32);
  * permanent failure -> DEAD_LETTER immediately (no pointless retries, §31).

Notifications are idempotent (DB unique on event_id+channel+recipient), so
at-least-once event processing never double-notifies (prompt §9, §33).
"""
from __future__ import annotations

import socket
import uuid
from datetime import datetime, timezone

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.core.metrics import metrics
from app.db.session import get_sessionmaker
from app.models.enums import DomainEventType, OutboxStatus
from app.models.notification import DeadLetterEvent, OutboxEvent
from app.modules.notifications.delivery import (
    attempts_exhausted,
    next_attempt_at,
)
from app.modules.notifications.events import EventEnvelope
from app.modules.notifications.orchestrator import NotificationOrchestrator

logger = get_logger("civiclens.notifications.worker")

_WORKER_ID = f"{socket.gethostname()}:{uuid.uuid4().hex[:8]}"


class OutboxWriter:
    """Writes envelope events into the caller's transaction (no commit)."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def enqueue(self, envelope: EventEnvelope) -> OutboxEvent:
        seq = self._session.execute(text("SELECT nextval('outbox_sequence_no_seq')")).scalar()
        event = OutboxEvent(**envelope.to_row_kwargs(), status=OutboxStatus.PENDING, sequence_no=seq)
        self._session.add(event)
        self._session.flush()
        metrics.incr("outbox_events_created")
        return event

    def enqueue_simple(
        self,
        *,
        event_type: DomainEventType,
        aggregate_type: str,
        aggregate_id: uuid.UUID,
        payload: dict,
        actor_id: uuid.UUID | None = None,
        correlation_id: str | None = None,
        causation_id: str | None = None,
    ) -> OutboxEvent:
        return self.enqueue(EventEnvelope(
            event_type=event_type, aggregate_type=aggregate_type, aggregate_id=aggregate_id,
            payload=payload, actor_id=actor_id, correlation_id=correlation_id,
            causation_id=causation_id,
        ))


class OutboxDispatcher:
    """Drains due outbox events into notifications with retry/backoff/dead-letter."""

    def __init__(self, session: Session | None = None, settings: Settings | None = None) -> None:
        self._own = session is None
        self._session = session or get_sessionmaker()()
        self._s = settings or get_settings()

    def dispatch_pending(self, *, limit: int | None = None) -> int:
        limit = limit or self._s.outbox_worker_batch_size
        processed = 0
        now = datetime.now(timezone.utc)
        try:
            # Claim due events: PENDING and (never attempted OR backoff elapsed).
            stmt = (
                select(OutboxEvent)
                .where(
                    OutboxEvent.status == OutboxStatus.PENDING,
                    (OutboxEvent.next_attempt_at.is_(None))
                    | (OutboxEvent.next_attempt_at <= now),
                )
                .order_by(OutboxEvent.aggregate_id, OutboxEvent.sequence_no, OutboxEvent.created_at)
                .limit(limit)
                .with_for_update(skip_locked=True)  # concurrent-worker safe (§8)
            )
            events = list(self._session.scalars(stmt))
            metrics.gauge("outbox_queue_depth", self._pending_count())
            for event in events:
                self._process_one(event)
                processed += 1
            self._session.commit()
        except Exception:
            self._session.rollback()
            raise
        finally:
            if self._own:
                self._session.close()
        return processed

    def _process_one(self, event: OutboxEvent) -> None:
        event.locked_at = datetime.now(timezone.utc)
        event.locked_by = _WORKER_ID
        try:
            orch = NotificationOrchestrator(self._session, self._s)
            outcome = orch.handle_event(
                event_id=event.id, event_type_str=event.event_type,
                aggregate_type=event.aggregate_type, aggregate_id=event.aggregate_id,
                payload=event.payload, schema_version=event.schema_version,
            )
            if outcome.retryable_failure:
                self._schedule_retry_or_dead_letter(event, error_code="TRANSIENT_PROVIDER_ERROR")
            else:
                event.status = OutboxStatus.DISPATCHED
                event.published_at = datetime.now(timezone.utc)
                event.locked_at = None
                event.locked_by = None
                metrics.incr("outbox_events_processed")
        except Exception as exc:  # unexpected handler error -> retryable
            logger.warning("outbox_process_error",
                           extra={"event_id": str(event.id), "error": type(exc).__name__})
            self._schedule_retry_or_dead_letter(event, error_code="TRANSIENT_PROVIDER_ERROR",
                                                 detail=str(exc)[:512])

    def _schedule_retry_or_dead_letter(self, event: OutboxEvent, *, error_code: str,
                                       detail: str | None = None) -> None:
        event.attempt_count += 1
        event.last_error_code = error_code
        event.last_error = detail
        event.locked_at = None
        event.locked_by = None
        metrics.incr("notification_retry_count")
        if attempts_exhausted(event.attempt_count, self._s):
            event.status = OutboxStatus.DEAD_LETTER
            self._session.add(DeadLetterEvent(
                outbox_event_id=event.id, event_type=event.event_type,
                aggregate_type=event.aggregate_type, aggregate_id=event.aggregate_id,
                payload=event.payload, attempt_count=event.attempt_count,
                last_error_code=error_code, last_error=detail,
                correlation_id=event.correlation_id,
            ))
            metrics.incr("outbox_events_dead_lettered")
            logger.warning("outbox_event_dead_lettered", extra={"event_id": str(event.id)})
        else:
            event.status = OutboxStatus.PENDING
            event.next_attempt_at = next_attempt_at(event.attempt_count, self._s)
            metrics.incr("outbox_events_failed")

    def _pending_count(self) -> int:
        return int(
            self._session.scalar(
                select(text("count(1)")).select_from(OutboxEvent).where(
                    OutboxEvent.status == OutboxStatus.PENDING
                )
            ) or 0
        )


def dispatch_outbox_now(settings: Settings | None = None) -> int:
    """Convenience entry point for in-process background dispatch/tests."""
    return OutboxDispatcher(settings=settings).dispatch_pending()
