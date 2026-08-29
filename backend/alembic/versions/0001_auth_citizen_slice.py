"""auth + citizen-profile vertical slice

Creates the tables for the authentication + citizen-profile slice:
users, citizen_profiles, citizen_profile_versions, addresses,
refresh_tokens, audit_logs, and the PostgreSQL enum types.

DOCUMENTED EXTENSIONS beyond docs/database/data-dictionary.md (recorded in
the implementation report):
  * users.status (user_status enum) — account suspension support.
  * users.last_login_at — login auditing.
  * refresh_tokens table — rotating/revocable refresh tokens (FR-AUTH-3);
    stores only a SHA-256 hash of the opaque token, never the raw token.
  * addresses.is_primary + a PARTIAL UNIQUE INDEX enforcing at most one
    primary address per citizen_profile.
  * users.phone_number / email / password_hash are nullable to support both
    phone+OTP and email+password accounts (FR-AUTH-1).

audit_logs and citizen_profile_versions are append-only (database-design.md
§2.5); UPDATE/DELETE would be REVOKE'd from the app role in a real deploy —
noted here; the grant model is environment-specific and not applied in this
migration (single-role local/test DB).

Revision ID: 0001_auth_citizen_slice
Revises:
Create Date: 2026-08-29
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_auth_citizen_slice"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    user_role = postgresql.ENUM(
        "citizen", "agent", "scheme_admin", "admin", name="user_role", create_type=False
    )
    user_status = postgresql.ENUM(
        "active", "suspended", name="user_status", create_type=False
    )
    address_type = postgresql.ENUM(
        "permanent", "current", name="address_type", create_type=False
    )

    bind = op.get_bind()
    # Create the enum types explicitly (idempotent); columns below reference
    # them with create_type=False so table DDL does not re-emit CREATE TYPE.
    postgresql.ENUM(
        "citizen", "agent", "scheme_admin", "admin", name="user_role"
    ).create(bind, checkfirst=True)
    postgresql.ENUM("active", "suspended", name="user_status").create(bind, checkfirst=True)
    postgresql.ENUM("permanent", "current", name="address_type").create(bind, checkfirst=True)

    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("phone_number", sa.String(length=20), nullable=True),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=True),
        sa.Column(
            "role", user_role, nullable=False, server_default="citizen"
        ),
        sa.Column(
            "status", user_status, nullable=False, server_default="active"
        ),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_unique_constraint("uq_users_phone_number", "users", ["phone_number"])
    op.create_unique_constraint("uq_users_email", "users", ["email"])
    op.create_index("ix_users_phone_number", "users", ["phone_number"])
    op.create_index("ix_users_email", "users", ["email"])

    # --- citizen_profiles ---
    op.create_table(
        "citizen_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("gender", sa.String(length=32), nullable=True),
        sa.Column("category", sa.String(length=64), nullable=True),
        sa.Column("occupation", sa.String(length=128), nullable=True),
        sa.Column("declared_annual_income", sa.Numeric(14, 2), nullable=True),
        sa.Column("disability_status", sa.Boolean(), nullable=True),
        sa.Column("family_size", sa.Integer(), nullable=True),
        sa.Column("current_version_no", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", name="uq_citizen_profiles_user_id"),
    )
    op.create_index(
        "ix_citizen_profiles_user_id", "citizen_profiles", ["user_id"]
    )

    # --- citizen_profile_versions (append-only) ---
    op.create_table(
        "citizen_profile_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("citizen_profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column("snapshot", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["citizen_profile_id"], ["citizen_profiles.id"], ondelete="CASCADE"
        ),
    )
    op.create_index(
        "ix_citizen_profile_versions_profile_id",
        "citizen_profile_versions",
        ["citizen_profile_id"],
    )

    # --- addresses ---
    op.create_table(
        "addresses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("citizen_profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", address_type, nullable=False),
        sa.Column("state", sa.String(length=64), nullable=False),
        sa.Column("district", sa.String(length=64), nullable=False),
        sa.Column("pincode", sa.String(length=6), nullable=False),
        sa.Column("line1", sa.Text(), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.ForeignKeyConstraint(
            ["citizen_profile_id"], ["citizen_profiles.id"], ondelete="CASCADE"
        ),
    )
    op.create_index("ix_addresses_profile_id", "addresses", ["citizen_profile_id"])
    # At most one primary address per citizen (partial unique index).
    op.create_index(
        "uq_one_primary_address_per_profile",
        "addresses",
        ["citizen_profile_id"],
        unique=True,
        postgresql_where=sa.text("is_primary"),
    )

    # --- refresh_tokens ---
    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("rotated_from_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["rotated_from_id"], ["refresh_tokens.id"], ondelete="SET NULL"
        ),
        sa.UniqueConstraint("token_hash", name="uq_refresh_tokens_token_hash"),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"])

    # --- audit_logs (append-only) ---
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("diff", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["actor_user_id"], ["users.id"], ondelete="SET NULL"
        ),
    )
    op.create_index("ix_audit_logs_actor_user_id", "audit_logs", ["actor_user_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("refresh_tokens")
    op.drop_index("uq_one_primary_address_per_profile", table_name="addresses")
    op.drop_table("addresses")
    op.drop_table("citizen_profile_versions")
    op.drop_table("citizen_profiles")
    op.drop_table("users")

    bind = op.get_bind()
    for name in ("address_type", "user_status", "user_role"):
        postgresql.ENUM(name=name).drop(bind, checkfirst=True)
