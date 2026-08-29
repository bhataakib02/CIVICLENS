"""OTP requests and Consent management tables (Prompt 7).

Revision ID: 0007_otp_and_consents
Revises: 0006_notifications_eventing
Create Date: 2026-08-29
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007_otp_and_consents"
down_revision: Union[str, None] = "0006_notifications_eventing"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_CONSENT_TYPE = (
    "agent_assistance",
    "data_sharing",
    "document_access",
    "notification_subscription",
)


def _mk(bind, name, values):
    postgresql.ENUM(*values, name=name).create(bind, checkfirst=True)
    return postgresql.ENUM(*values, name=name, create_type=False)


def upgrade() -> None:
    bind = op.get_bind()

    # 1. otp_requests table
    op.create_table(
        "otp_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("phone_number", sa.String(20), nullable=False),
        sa.Column("code_hash", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_otp_requests_phone_number", "otp_requests", ["phone_number"])
    op.create_index("ix_otp_requests_expires_at", "otp_requests", ["expires_at"])

    # 2. consent_type enum & consent_records table
    consent_type_enum = _mk(bind, "consent_type", _CONSENT_TYPE)

    op.create_table(
        "consent_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("citizen_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("citizen_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("consent_type", consent_type_enum, nullable=False),
        sa.Column("purpose", sa.Text(), nullable=False),
        sa.Column("scope", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("version", sa.String(32), nullable=False, server_default="1.0"),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_consent_records_citizen_id", "consent_records", ["citizen_id"])
    op.create_index("ix_consent_records_consent_type", "consent_records", ["consent_type"])
    op.create_index("ix_consent_records_agent_id", "consent_records", ["agent_id"])
    op.create_index("ix_consent_records_revoked_at", "consent_records", ["revoked_at"])


def downgrade() -> None:
    op.drop_table("consent_records")
    op.execute("DROP TYPE IF EXISTS consent_type")
    op.drop_table("otp_requests")
