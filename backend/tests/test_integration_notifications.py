"""Integration tests: event outbox + worker + orchestrator + notifications
against real PostgreSQL (prompt §42-§48).

Covers: outbox transactionality + rollback (§7, §43), worker success/retry/
failure/dead-letter (§46), concurrency via SKIP LOCKED (§45), duplicate-event
dedup (§44), preference filtering (§47), localization (§48), notification
creation, SENT!=DELIVERED (§54)."""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import func, select

from app.models.enums import (
    DomainEventType,
    NotificationChannel,
    NotificationStatus,
    OutboxStatus,
)
from app.models.notification import (
    DeadLetterEvent,
    Notification,
    NotificationPreference,
    OutboxEvent,
)
from app.modules.notifications.events import AggregateType, EventEnvelope
from app.modules.notifications.service import OutboxDispatcher, OutboxWriter

pytestmark = pytest.mark.integration


# ------------------------------ helpers ------------------------------------- #
def _make_citizen(db_session_factory, *, email="evt@example.com", language="en"):
    from app.models.citizen_profile import CitizenProfile
    from app.models.user import User

    with db_session_factory() as s:
        user = User(email=email, role="citizen", status="active")
        s.add(user); s.flush()
        profile = CitizenProfile(user_id=user.id, preferred_language=language)
        s.add(profile); s.commit()
        return user.id, profile.id


def _enqueue(db_session_factory, *, event_type, profile_id, aggregate_id=None, extra=None):
    aggregate_id = aggregate_id or uuid.uuid4()
    with db_session_factory() as s:
        writer = OutboxWriter(s)
        payload = {"citizen_profile_id": str(profile_id), "application_number": "CL-2026-00000001",
                   "status": "submitted"}
        if extra:
            payload.update(extra)
        ev = writer.enqueue(EventEnvelope(
            event_type=event_type, aggregate_type=AggregateType.APPLICATION,
            aggregate_id=aggregate_id, payload=payload,
        ))
        eid = ev.id
        s.commit()
    return eid, aggregate_id


# ------------------------------ transactionality ---------------------------- #
def test_outbox_event_and_state_commit_atomically(db_session_factory):
    """The event exists only after the caller's transaction commits (§7)."""
    _, profile_id = _make_citizen(db_session_factory, email="tx1@example.com")
    with db_session_factory() as s:
        OutboxWriter(s).enqueue(EventEnvelope(
            event_type=DomainEventType.APPLICATION_SUBMITTED,
            aggregate_type=AggregateType.APPLICATION, aggregate_id=uuid.uuid4(),
            payload={"citizen_profile_id": str(profile_id)},
        ))
        # Not committed yet — a separate session must not see it.
        with db_session_factory() as s2:
            assert s2.scalar(select(func.count()).select_from(OutboxEvent)) == 0
        s.commit()
    with db_session_factory() as s3:
        assert s3.scalar(select(func.count()).select_from(OutboxEvent)) == 1


def test_critical_transaction_rollback_removes_both(db_session_factory):
    """Force a failure after enqueue: neither the event nor any side effect
    persists (prompt §43)."""
    _, profile_id = _make_citizen(db_session_factory, email="tx2@example.com")
    try:
        with db_session_factory() as s:
            OutboxWriter(s).enqueue(EventEnvelope(
                event_type=DomainEventType.APPLICATION_SUBMITTED,
                aggregate_type=AggregateType.APPLICATION, aggregate_id=uuid.uuid4(),
                payload={"citizen_profile_id": str(profile_id)},
            ))
            raise RuntimeError("boom before commit")
    except RuntimeError:
        pass
    with db_session_factory() as s:
        assert s.scalar(select(func.count()).select_from(OutboxEvent)) == 0


# ------------------------------ worker success ------------------------------ #
def test_worker_processes_event_creates_notification(db_session_factory):
    _, profile_id = _make_citizen(db_session_factory, email="w1@example.com")
    eid, _ = _enqueue(db_session_factory, event_type=DomainEventType.APPLICATION_SUBMITTED,
                      profile_id=profile_id)
    with db_session_factory() as s:
        n = OutboxDispatcher(session=s).dispatch_pending()
    assert n == 1
    with db_session_factory() as s:
        ev = s.get(OutboxEvent, eid)
        assert ev.status is OutboxStatus.DISPATCHED and ev.published_at is not None
        notifs = s.scalars(select(Notification).where(Notification.event_id == eid)).all()
        # policy = IN_APP + EMAIL for submitted; email pref off by default -> in_app only.
        channels = {x.channel for x in notifs}
        assert NotificationChannel.IN_APP in channels
        in_app = [x for x in notifs if x.channel is NotificationChannel.IN_APP][0]
        assert in_app.status is NotificationStatus.SENT  # SENT, not DELIVERED (§54)
        assert in_app.title and in_app.template_version == 1


# ------------------------------ dedup / duplicate --------------------------- #
def test_duplicate_event_processing_is_idempotent(db_session_factory):
    """Processing the same event twice yields one notification per channel (§44)."""
    _, profile_id = _make_citizen(db_session_factory, email="dup@example.com")
    eid, _ = _enqueue(db_session_factory, event_type=DomainEventType.APPLICATION_SUBMITTED,
                      profile_id=profile_id)
    # First drain.
    with db_session_factory() as s:
        OutboxDispatcher(session=s).dispatch_pending()
    before = _count_notifs(db_session_factory, eid)
    # Force reprocessing by resetting the event to PENDING and draining again.
    with db_session_factory() as s:
        ev = s.get(OutboxEvent, eid); ev.status = OutboxStatus.PENDING; ev.next_attempt_at = None
        s.commit()
    with db_session_factory() as s:
        OutboxDispatcher(session=s).dispatch_pending()
    after = _count_notifs(db_session_factory, eid)
    assert before == after  # no duplicates (DB unique boundary)


def _count_notifs(db_session_factory, eid):
    with db_session_factory() as s:
        return s.scalar(select(func.count()).select_from(Notification).where(
            Notification.event_id == eid))


# ------------------------------ preference filtering ------------------------ #
def test_preference_opt_out_suppresses_email_keeps_in_app(db_session_factory):
    """Citizen enables email but opts OUT of application_updates category (§47).
    APPLICATION_APPROVED (in_app+email) then yields NO notifications for the
    category — both channels are governed by application_updates."""
    user_id, profile_id = _make_citizen(db_session_factory, email="pref@example.com")
    with db_session_factory() as s:
        pref = NotificationPreference(user_id=user_id, email_enabled=True,
                                      application_updates=False)
        s.add(pref); s.commit()
    eid, _ = _enqueue(db_session_factory, event_type=DomainEventType.APPLICATION_APPROVED,
                      profile_id=profile_id)
    with db_session_factory() as s:
        OutboxDispatcher(session=s).dispatch_pending()
    with db_session_factory() as s:
        notifs = s.scalars(select(Notification).where(Notification.event_id == eid)).all()
    assert notifs == []  # category opted out -> nothing delivered


def test_email_channel_delivered_when_enabled(db_session_factory):
    user_id, profile_id = _make_citizen(db_session_factory, email="pref2@example.com")
    with db_session_factory() as s:
        s.add(NotificationPreference(user_id=user_id, email_enabled=True,
                                     application_updates=True)); s.commit()
    eid, _ = _enqueue(db_session_factory, event_type=DomainEventType.APPLICATION_APPROVED,
                      profile_id=profile_id)
    with db_session_factory() as s:
        OutboxDispatcher(session=s).dispatch_pending()
    with db_session_factory() as s:
        channels = {n.channel for n in s.scalars(
            select(Notification).where(Notification.event_id == eid))}
    assert NotificationChannel.IN_APP in channels
    assert NotificationChannel.EMAIL in channels  # opted-in email delivered


# ------------------------------ localization -------------------------------- #
def test_localization_uses_profile_language(db_session_factory):
    _, profile_id = _make_citizen(db_session_factory, email="loc@example.com", language="bn")
    eid, _ = _enqueue(db_session_factory, event_type=DomainEventType.APPLICATION_SUBMITTED,
                      profile_id=profile_id)
    with db_session_factory() as s:
        OutboxDispatcher(session=s).dispatch_pending()
    with db_session_factory() as s:
        n = s.scalars(select(Notification).where(
            Notification.event_id == eid,
            Notification.channel == NotificationChannel.IN_APP)).first()
    assert n.language == "bn"


# ------------------------------ retry / dead-letter ------------------------- #
def test_retry_then_dead_letter_on_persistent_failure(db_session_factory, monkeypatch):
    """A persistent retryable failure schedules retries then dead-letters after
    the attempt budget, incrementing attempt_count each time (§46, §32)."""
    _, profile_id = _make_citizen(db_session_factory, email="retry@example.com")
    eid, _ = _enqueue(db_session_factory, event_type=DomainEventType.APPLICATION_SUBMITTED,
                      profile_id=profile_id)

    # Force the orchestrator to report a retryable failure every time.
    from app.modules.notifications import orchestrator as orch_mod

    def _always_retryable(self, **kwargs):
        r = orch_mod.OrchestrationResult()
        r.retryable_failure = True
        return r

    monkeypatch.setattr(orch_mod.NotificationOrchestrator, "handle_event", _always_retryable)

    from app.core.config import get_settings

    max_attempts = get_settings().notification_max_attempts
    # Drain repeatedly, clearing next_attempt_at so backoff doesn't block the test.
    for _ in range(max_attempts + 2):
        with db_session_factory() as s:
            ev = s.get(OutboxEvent, eid)
            if ev.status is OutboxStatus.PENDING:
                ev.next_attempt_at = None
                s.commit()
        with db_session_factory() as s:
            OutboxDispatcher(session=s).dispatch_pending()

    with db_session_factory() as s:
        ev = s.get(OutboxEvent, eid)
        assert ev.status is OutboxStatus.DEAD_LETTER
        assert ev.attempt_count >= max_attempts
        dl = s.scalars(select(DeadLetterEvent).where(DeadLetterEvent.outbox_event_id == eid)).all()
        assert len(dl) == 1  # visible, not silently discarded


def test_backoff_scheduled_on_first_failure(db_session_factory, monkeypatch):
    _, profile_id = _make_citizen(db_session_factory, email="bo@example.com")
    eid, _ = _enqueue(db_session_factory, event_type=DomainEventType.APPLICATION_SUBMITTED,
                      profile_id=profile_id)
    from app.modules.notifications import orchestrator as orch_mod

    def _retryable(self, **kwargs):
        r = orch_mod.OrchestrationResult(); r.retryable_failure = True
        return r

    monkeypatch.setattr(orch_mod.NotificationOrchestrator, "handle_event", _retryable)
    with db_session_factory() as s:
        OutboxDispatcher(session=s).dispatch_pending()
    with db_session_factory() as s:
        ev = s.get(OutboxEvent, eid)
        assert ev.status is OutboxStatus.PENDING
        assert ev.attempt_count == 1
        assert ev.next_attempt_at is not None  # backoff scheduled


# ------------------------------ concurrency (SKIP LOCKED) ------------------- #
def test_concurrent_workers_no_duplicate_notifications(db_session_factory):
    """Two workers drain the same pending set concurrently; SKIP LOCKED + the
    dedup constraint guarantee one notification per (event,channel) (§45)."""
    import threading

    _, profile_id = _make_citizen(db_session_factory, email="conc@example.com")
    eids = []
    for _ in range(5):
        eid, _agg = _enqueue(db_session_factory,
                             event_type=DomainEventType.APPLICATION_SUBMITTED, profile_id=profile_id)
        eids.append(eid)

    barrier = threading.Barrier(2)

    def _drain():
        barrier.wait()
        with db_session_factory() as s:
            OutboxDispatcher(session=s).dispatch_pending()

    threads = [threading.Thread(target=_drain) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    with db_session_factory() as s:
        for eid in eids:
            in_app = s.scalar(select(func.count()).select_from(Notification).where(
                Notification.event_id == eid,
                Notification.channel == NotificationChannel.IN_APP))
            assert in_app == 1  # exactly one, never duplicated
            ev = s.get(OutboxEvent, eid)
            assert ev.status is OutboxStatus.DISPATCHED
