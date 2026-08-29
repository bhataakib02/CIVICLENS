"""application workflow + case management

Creates the application/case-management/notification/outbox tables (prompt §40):
  document_requirements, applications, application_documents,
  application_status_history, application_submissions, application_assignments,
  application_actions, notifications, outbox_events
plus enum types.

Key constraints (prompt §41):
  * applications.application_number UNIQUE (human reference).
  * At most ONE non-failed submission per application — a PARTIAL UNIQUE INDEX
    on application_submissions(application_id) WHERE status <> 'failed'
    guarantees concurrent/duplicate submits cannot create two live submissions.
  * FKs everywhere; scheme_version_id uses ON DELETE RESTRICT so a submitted
    application's pinned version cannot be deleted out from under it.
  * indexes for pagination/status/assignment lookups.

DOCUMENTED EXTENSIONS beyond docs/database/data-dictionary.md (recorded in the
report): applications.application_number/eligibility_check_id/
eligibility_snapshot/assigned_case_worker_id/updated_at/completed_at/deadline_at;
application_status_history.metadata; new submissions/assignments/actions/outbox
tables; notifications.subject/entity_type/entity_id.

Revision ID: 0005_application_workflow
Revises: 0004_document_intelligence
Create Date: 2026-08-29
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005_application_workflow"
down_revision: Union[str, None] = "0004_document_intelligence"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_APP_STATUS = (
    "draft", "ready_for_submission", "submission_pending", "submission_failed",
    "submitted", "under_review", "action_required", "info_requested",
    "approved", "rejected", "withdrawn", "completed",
)
_SUB_STATUS = ("pending", "submitted", "failed", "acknowledged")
_SUB_METHOD = ("mock", "portal_api", "manual_export")
_ASSIGN_ACTION = ("assign", "unassign", "reassign")
_ACTION_STATUS = ("open", "resolved", "cancelled")
_N_CHANNEL = ("sms", "email", "in_app")
_N_CATEGORY = ("scheme_match", "status_change", "doc_reverification", "deadline_reminder")
_N_STATUS = ("queued", "sent", "failed")
_OUTBOX_STATUS = ("pending", "dispatched", "failed")


def _mk(bind, name, values):
    postgresql.ENUM(*values, name=name).create(bind, checkfirst=True)
    return postgresql.ENUM(*values, name=name, create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    app_status = _mk(bind, "application_status", _APP_STATUS)
    sub_status = _mk(bind, "submission_status", _SUB_STATUS)
    sub_method = _mk(bind, "submission_method", _SUB_METHOD)
    assign_action = _mk(bind, "assignment_action", _ASSIGN_ACTION)
    action_status = _mk(bind, "action_required_status", _ACTION_STATUS)
    n_channel = _mk(bind, "notification_channel", _N_CHANNEL)
    n_category = _mk(bind, "notification_category", _N_CATEGORY)
    n_status = _mk(bind, "notification_status", _N_STATUS)
    outbox_status = _mk(bind, "outbox_status", _OUTBOX_STATUS)
    # document_type enum already exists (migration 0004).
    doc_type = postgresql.ENUM(name="document_type", create_type=False)

    # --- document_requirements ---
    op.create_table(
        "document_requirements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("scheme_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_type", doc_type, nullable=False),
        sa.Column("is_mandatory", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["scheme_version_id"], ["scheme_versions.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_document_requirements_scheme_version_id", "document_requirements", ["scheme_version_id"])

    # --- applications ---
    op.create_table(
        "applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("application_number", sa.String(length=32), nullable=False),
        sa.Column("citizen_profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scheme_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("eligibility_check_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("eligibility_snapshot", postgresql.JSONB(), nullable=True),
        sa.Column("status", app_status, nullable=False, server_default="draft"),
        sa.Column("scheme_specific_answers", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("assigned_case_worker_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("deadline_at", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["citizen_profile_id"], ["citizen_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["scheme_version_id"], ["scheme_versions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["eligibility_check_id"], ["eligibility_checks.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["assigned_case_worker_id"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("application_number", name="uq_application_number"),
    )
    op.create_index("ix_applications_citizen_profile_id", "applications", ["citizen_profile_id"])
    op.create_index("ix_applications_scheme_version_id", "applications", ["scheme_version_id"])
    op.create_index("ix_applications_status", "applications", ["status"])
    op.create_index("ix_applications_assigned_case_worker_id", "applications", ["assigned_case_worker_id"])
    op.create_index("ix_applications_created_at", "applications", ["created_at"])
    # Common dashboard query: a citizen's applications by recency.
    op.create_index("ix_applications_citizen_created", "applications", ["citizen_profile_id", "created_at"])

    # --- application_documents (join) ---
    op.create_table(
        "application_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_type", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("application_id", "document_id", name="pk_application_documents"),
    )
    op.create_index("ix_application_documents_application_id", "application_documents", ["application_id"])
    op.create_index("ix_application_documents_document_id", "application_documents", ["document_id"])

    # --- application_status_history (append-only) ---
    op.create_table(
        "application_status_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("from_status", sa.String(length=32), nullable=True),
        sa.Column("to_status", sa.String(length=32), nullable=False),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_application_status_history_application_id", "application_status_history", ["application_id"])

    # --- application_submissions ---
    op.create_table(
        "application_submissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sub_status, nullable=False, server_default="pending"),
        sa.Column("submission_method", sub_method, nullable=False),
        sa.Column("external_reference", sa.String(length=128), nullable=True),
        sa.Column("submitted_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("request_id", sa.String(length=128), nullable=True),
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        sa.Column("response_metadata", postgresql.JSONB(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["submitted_by"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_application_submissions_application_id", "application_submissions", ["application_id"])
    # At most ONE live (non-failed) submission per application — idempotency +
    # concurrency safety at the DB level.
    op.create_index(
        "uq_one_live_submission_per_application", "application_submissions", ["application_id"],
        unique=True, postgresql_where=sa.text("status <> 'failed'"),
    )

    # --- application_assignments ---
    op.create_table(
        "application_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", assign_action, nullable=False),
        sa.Column("case_worker_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("previous_case_worker_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("assigned_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["case_worker_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["previous_case_worker_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["assigned_by"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_application_assignments_application_id", "application_assignments", ["application_id"])

    # --- application_actions ---
    op.create_table(
        "application_actions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("required_items", postgresql.JSONB(), nullable=True),
        sa.Column("status", action_status, nullable=False, server_default="open"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_application_actions_application_id", "application_actions", ["application_id"])

    # --- notifications ---
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("citizen_profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("channel", n_channel, nullable=False),
        sa.Column("category", n_category, nullable=False),
        sa.Column("status", n_status, nullable=False, server_default="queued"),
        sa.Column("subject", sa.String(length=255), nullable=True),
        sa.Column("entity_type", sa.String(length=64), nullable=True),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["citizen_profile_id"], ["citizen_profiles.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_notifications_citizen_profile_id", "notifications", ["citizen_profile_id"])
    op.create_index("ix_notifications_status", "notifications", ["status"])
    op.create_index("ix_notifications_created_at", "notifications", ["created_at"])

    # --- outbox_events ---
    op.create_table(
        "outbox_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("aggregate_type", sa.String(length=64), nullable=False),
        sa.Column("aggregate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("status", outbox_status, nullable=False, server_default="pending"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("dispatched_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_outbox_events_status", "outbox_events", ["status"])
    op.create_index("ix_outbox_events_event_type", "outbox_events", ["event_type"])
    op.create_index("ix_outbox_events_aggregate_id", "outbox_events", ["aggregate_id"])
    op.create_index("ix_outbox_events_created_at", "outbox_events", ["created_at"])


def downgrade() -> None:
    op.drop_table("outbox_events")
    op.drop_table("notifications")
    op.drop_table("application_actions")
    op.drop_table("application_assignments")
    op.drop_index("uq_one_live_submission_per_application", table_name="application_submissions")
    op.drop_table("application_submissions")
    op.drop_table("application_status_history")
    op.drop_table("application_documents")
    op.drop_table("applications")
    op.drop_table("document_requirements")
    bind = op.get_bind()
    for name in (
        "outbox_status", "notification_status", "notification_category", "notification_channel",
        "action_required_status", "assignment_action", "submission_method", "submission_status",
        "application_status",
    ):
        postgresql.ENUM(name=name).drop(bind, checkfirst=True)
