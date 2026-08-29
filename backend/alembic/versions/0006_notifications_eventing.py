"""Event-driven notifications + real-time infrastructure (Phase 6, prompt §40).

Extends the transactional outbox + notifications created in 0005 and adds
per-user preferences, a dead-letter table, and a language column.

Changes
-------
enums (ALTER TYPE ADD VALUE — new values are only used by runtime INSERTs, never
in this migration's DDL, so this is transaction-safe on PG 12+):
  * notification_channel  += push
  * notification_status   += pending, processing, delivered, cancelled
  * outbox_status         += processing, dead_letter
  * notification_priority  (new enum: low, normal, high, critical)

outbox_events (envelope + worker/retry — prompt §5, §6, §8, §31):
  + actor_id, schema_version, correlation_id, causation_id, occurred_at,
    sequence_no, attempt_count, next_attempt_at, last_error_code, locked_at,
    locked_by, published_at
  (existing `attempts`/`dispatched_at` kept; the new code uses attempt_count/
   published_at — both retained so no data is lost.)
  + a DB SEQUENCE (outbox_sequence_no_seq) backing per-aggregate ordering.
  + indexes: (status,next_attempt_at) for the worker poll; correlation_id.

notifications (per-recipient/channel delivery — prompt §10, §33):
  * citizen_profile_id -> NULLABLE (staff recipients have no citizen profile).
  + recipient_user_id (FK users, NOT NULL) — backfilled from the profile owner.
  + event_id (FK outbox_events), type, priority, title, body, template_key,
    template_version, language, provider, provider_message_id, attempt_count,
    error_code, read_at, delivered_at, failed_at.
  + UNIQUE(event_id, channel, recipient_user_id) — dedup boundary (prompt §33).
  + indexes: (recipient_user_id, created_at); partial (recipient_user_id) WHERE
    read_at IS NULL for the unread-count query (prompt §49).

new tables:
  * notification_preferences (per-user opt-in; prompt §16, §17)
  * dead_letter_events (exhausted retries; prompt §32)

citizen_profiles:
  + preferred_language (varchar(8) NOT NULL default 'en'; prompt §26, §27)

Revision ID: 0006_notifications_eventing
Revises: 0005_application_workflow
Create Date: 2026-08-29
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006_notifications_eventing"
down_revision: Union[str, None] = "0005_application_workflow"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    # --- enum value additions ---
    op.execute("ALTER TYPE notification_channel ADD VALUE IF NOT EXISTS 'push'")
    for v in ("pending", "processing", "delivered", "cancelled"):
        op.execute(f"ALTER TYPE notification_status ADD VALUE IF NOT EXISTS '{v}'")
    for v in ("processing", "dead_letter"):
        op.execute(f"ALTER TYPE outbox_status ADD VALUE IF NOT EXISTS '{v}'")
    postgresql.ENUM(
        "low", "normal", "high", "critical", name="notification_priority"
    ).create(bind, checkfirst=True)
    n_priority = postgresql.ENUM(
        "low", "normal", "high", "critical", name="notification_priority", create_type=False
    )

    # --- per-aggregate ordering sequence (prompt §34) ---
    op.execute("CREATE SEQUENCE IF NOT EXISTS outbox_sequence_no_seq")

    # --- outbox_events: envelope + worker/retry columns ---
    op.add_column("outbox_events", sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("outbox_events", sa.Column("schema_version", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("outbox_events", sa.Column("correlation_id", sa.String(length=64), nullable=True))
    op.add_column("outbox_events", sa.Column("causation_id", sa.String(length=64), nullable=True))
    op.add_column("outbox_events", sa.Column("occurred_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))
    op.add_column("outbox_events", sa.Column("sequence_no", sa.Integer(), nullable=True))
    op.add_column("outbox_events", sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("outbox_events", sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("outbox_events", sa.Column("last_error_code", sa.String(length=64), nullable=True))
    op.add_column("outbox_events", sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("outbox_events", sa.Column("locked_by", sa.String(length=64), nullable=True))
    op.add_column("outbox_events", sa.Column("published_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_outbox_events_status_next_attempt", "outbox_events", ["status", "next_attempt_at"])
    op.create_index("ix_outbox_events_correlation_id", "outbox_events", ["correlation_id"])

    # --- notifications: recipient + delivery/content/template columns ---
    op.alter_column("notifications", "citizen_profile_id", existing_type=postgresql.UUID(as_uuid=True), nullable=True)
    op.add_column("notifications", sa.Column("recipient_user_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("notifications", sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("notifications", sa.Column("type", sa.String(length=64), nullable=False, server_default="APPLICATION_STATUS_CHANGED"))
    op.add_column("notifications", sa.Column("priority", n_priority, nullable=False, server_default="normal"))
    op.add_column("notifications", sa.Column("title", sa.String(length=255), nullable=True))
    op.add_column("notifications", sa.Column("body", sa.Text(), nullable=True))
    op.add_column("notifications", sa.Column("template_key", sa.String(length=64), nullable=True))
    op.add_column("notifications", sa.Column("template_version", sa.Integer(), nullable=True))
    op.add_column("notifications", sa.Column("language", sa.String(length=8), nullable=True))
    op.add_column("notifications", sa.Column("provider", sa.String(length=64), nullable=True))
    op.add_column("notifications", sa.Column("provider_message_id", sa.String(length=128), nullable=True))
    op.add_column("notifications", sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("notifications", sa.Column("error_code", sa.String(length=64), nullable=True))
    op.add_column("notifications", sa.Column("read_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("notifications", sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("notifications", sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True))

    # Backfill recipient_user_id from the owning profile for any pre-existing rows.
    op.execute(
        "UPDATE notifications n SET recipient_user_id = cp.user_id "
        "FROM citizen_profiles cp WHERE n.citizen_profile_id = cp.id "
        "AND n.recipient_user_id IS NULL"
    )
    op.alter_column("notifications", "recipient_user_id", existing_type=postgresql.UUID(as_uuid=True), nullable=False)
    op.create_foreign_key("fk_notifications_recipient_user", "notifications", "users", ["recipient_user_id"], ["id"], ondelete="CASCADE")
    op.create_foreign_key("fk_notifications_event", "notifications", "outbox_events", ["event_id"], ["id"], ondelete="SET NULL")
    op.create_unique_constraint(
        "uq_notification_event_channel_recipient", "notifications",
        ["event_id", "channel", "recipient_user_id"],
    )
    op.create_index("ix_notifications_recipient_user_id", "notifications", ["recipient_user_id"])
    op.create_index("ix_notifications_event_id", "notifications", ["event_id"])
    op.create_index("ix_notifications_recipient_created", "notifications", ["recipient_user_id", "created_at"])
    # Efficient unread-count (prompt §49): partial index over unread rows.
    op.create_index(
        "ix_notifications_unread", "notifications", ["recipient_user_id"],
        postgresql_where=sa.text("read_at IS NULL"),
    )

    # --- notification_preferences ---
    op.create_table(
        "notification_preferences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("sms_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("push_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("in_app_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("application_updates", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("document_updates", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("scheme_updates", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("security_alerts", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", name="uq_notification_preferences_user"),
    )

    # --- dead_letter_events ---
    op.create_table(
        "dead_letter_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("outbox_event_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("aggregate_type", sa.String(length=64), nullable=False),
        sa.Column("aggregate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error_code", sa.String(length=64), nullable=True),
        sa.Column("last_error", sa.String(length=512), nullable=True),
        sa.Column("correlation_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_dead_letter_events_aggregate_id", "dead_letter_events", ["aggregate_id"])
    op.create_index("ix_dead_letter_events_outbox_event_id", "dead_letter_events", ["outbox_event_id"])

    # --- citizen_profiles.preferred_language ---
    op.add_column(
        "citizen_profiles",
        sa.Column("preferred_language", sa.String(length=8), nullable=False, server_default="en"),
    )


def downgrade() -> None:
    op.drop_column("citizen_profiles", "preferred_language")
    op.drop_index("ix_dead_letter_events_outbox_event_id", table_name="dead_letter_events")
    op.drop_index("ix_dead_letter_events_aggregate_id", table_name="dead_letter_events")
    op.drop_table("dead_letter_events")
    op.drop_table("notification_preferences")

    op.drop_index("ix_notifications_unread", table_name="notifications")
    op.drop_index("ix_notifications_recipient_created", table_name="notifications")
    op.drop_index("ix_notifications_event_id", table_name="notifications")
    op.drop_index("ix_notifications_recipient_user_id", table_name="notifications")
    op.drop_constraint("uq_notification_event_channel_recipient", "notifications", type_="unique")
    op.drop_constraint("fk_notifications_event", "notifications", type_="foreignkey")
    op.drop_constraint("fk_notifications_recipient_user", "notifications", type_="foreignkey")
    for col in ("failed_at", "delivered_at", "read_at", "error_code", "attempt_count",
                "provider_message_id", "provider", "language", "template_version", "template_key",
                "body", "title", "priority", "type", "event_id", "recipient_user_id"):
        op.drop_column("notifications", col)
    op.alter_column("notifications", "citizen_profile_id", existing_type=postgresql.UUID(as_uuid=True), nullable=False)

    op.drop_index("ix_outbox_events_correlation_id", table_name="outbox_events")
    op.drop_index("ix_outbox_events_status_next_attempt", table_name="outbox_events")
    for col in ("published_at", "locked_by", "locked_at", "next_attempt_at", "attempt_count",
                "sequence_no", "occurred_at", "causation_id", "correlation_id", "schema_version",
                "actor_id"):
        op.drop_column("outbox_events", col)
    op.execute("DROP SEQUENCE IF EXISTS outbox_sequence_no_seq")
    # notification_priority enum + added enum values are left in place (PG cannot
    # easily drop enum values); harmless if the migration is re-applied.
