"""Notification, transactional outbox, preferences + dead-letter models.

Design (prompt §5-§10, §32, §33, §40):

  * outbox_events is the transactional outbox: a domain event is written in the
    SAME DB transaction as the state change (a committed state change and its
    event never diverge — prompt §7). It carries the full EVENT ENVELOPE
    (event_id, event_type, aggregate_*, actor_id, occurred_at, schema_version,
    correlation_id, causation_id) plus worker/retry columns (attempt_count,
    next_attempt_at, locked_at/locked_by for FOR UPDATE SKIP LOCKED claiming).

  * notifications is the per-recipient, per-channel delivery record. A UNIQUE
    constraint on (event_id, channel, recipient_user_id) is the DB-level
    idempotency boundary (prompt §33) so at-least-once event processing never
    creates duplicate notifications. SENT != DELIVERED (prompt §10, §54).

  * notification_preferences persists per-user channel/category opt-in
    (prompt §16, §17); security_alerts is mandatory and cannot be disabled.

  * dead_letter_events records events that exhausted their retry budget so a
    failed notification is never silently discarded (prompt §32).

Notifications are NEVER emitted from models — always via the service/orchestrator
boundary.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, uuid_pk
from app.models.enums import (
    NotificationCategory,
    NotificationChannel,
    NotificationPriority,
    NotificationStatus,
    OutboxStatus,
    PreferredLanguage,
)


def _enum_col(py_enum, name):
    return Enum(
        py_enum,
        name=name,
        native_enum=True,
        validate_strings=True,
        values_callable=lambda enum: [m.value for m in enum],
    )


class OutboxEvent(Base):
    """Transactional outbox row carrying the full domain-event envelope."""

    __tablename__ = "outbox_events"

    # envelope
    id: Mapped[uuid.UUID] = uuid_pk()  # == event_id
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    aggregate_type: Mapped[str] = mapped_column(String(64), nullable=False)
    aggregate_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)  # no PII/secrets
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    causation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    # per-aggregate ordering (prompt §34): monotonically increasing seq assigned
    # at enqueue time from a DB sequence; consumers order by (aggregate_id, seq).
    sequence_no: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # worker / retry
    status: Mapped[OutboxStatus] = mapped_column(
        _enum_col(OutboxStatus, "outbox_status"),
        default=OutboxStatus.PENDING,
        nullable=False,
        index=True,
    )
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    next_attempt_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    last_error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_error: Mapped[str | None] = mapped_column(String(512), nullable=True)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    locked_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )


class Notification(Base):
    """Per-recipient, per-channel delivery record."""

    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = uuid_pk()
    # Recipient. citizen_profile_id retained for the citizen-facing in-app feed
    # (data-dictionary + Phase 5). recipient_user_id is the canonical recipient
    # identity used for the dedup boundary + object-level auth (works for staff
    # recipients too, who may have no citizen profile).
    citizen_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("citizen_profiles.id", ondelete="CASCADE"), nullable=True, index=True
    )
    recipient_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("outbox_events.id", ondelete="SET NULL"), nullable=True, index=True
    )
    # notification "type" == the source domain event type (typed string).
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    channel: Mapped[NotificationChannel] = mapped_column(
        _enum_col(NotificationChannel, "notification_channel"), nullable=False
    )
    category: Mapped[NotificationCategory] = mapped_column(
        _enum_col(NotificationCategory, "notification_category"), nullable=False
    )
    priority: Mapped[NotificationPriority] = mapped_column(
        _enum_col(NotificationPriority, "notification_priority"),
        default=NotificationPriority.NORMAL,
        nullable=False,
    )
    status: Mapped[NotificationStatus] = mapped_column(
        _enum_col(NotificationStatus, "notification_status"),
        default=NotificationStatus.PENDING,
        nullable=False,
        index=True,
    )
    # Rendered content. title/body may contain user-facing info; kept out of logs.
    subject: Mapped[str | None] = mapped_column(String(255), nullable=True)  # legacy alias of title
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Template provenance (prompt §25): the exact template + version rendered.
    template_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    template_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    language: Mapped[str | None] = mapped_column(String(8), nullable=True)

    entity_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)

    # delivery provenance (prompt §12, §28)
    provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    provider_message_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)

    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    __table_args__ = (
        # DB-level idempotency boundary (prompt §33): one logical delivery per
        # (event, channel, recipient). Guarantees at-least-once event processing
        # never produces duplicate notifications.
        UniqueConstraint(
            "event_id", "channel", "recipient_user_id",
            name="uq_notification_event_channel_recipient",
        ),
    )


class NotificationPreference(Base):
    """Per-user notification preferences (prompt §16, §17)."""

    __tablename__ = "notification_preferences"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    # channel opt-in
    email_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sms_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    push_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    in_app_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # category opt-in (safe public-service defaults; no marketing — prompt §17)
    application_updates: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    document_updates: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    scheme_updates: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # Mandatory — cannot be disabled (prompt §16); kept for completeness/UX.
    security_alerts: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class DeadLetterEvent(Base):
    """Events whose delivery exhausted the retry budget (prompt §32).

    Retains only the envelope + failure metadata (no PII) so operators can see
    and replay failures. Never silently discarded.
    """

    __tablename__ = "dead_letter_events"

    id: Mapped[uuid.UUID] = uuid_pk()
    outbox_event_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    aggregate_type: Mapped[str] = mapped_column(String(64), nullable=False)
    aggregate_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_error: Mapped[str | None] = mapped_column(String(512), nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
