"""scheme catalog + eligibility engine slice

Creates schemes, scheme_versions, eligibility_rules, eligibility_checks and
their enum types, plus the constraints/indexes required by prompt §26:
  * active-version integrity: a partial unique index guaranteeing at most one
    OPEN-ENDED published version per scheme (effective_to IS NULL). Full
    date-range overlap among published versions is additionally enforced in
    the schemes service layer (a range-overlap invariant cannot be expressed
    as a plain unique index without an exclusion constraint / btree_gist).
  * rule uniqueness: (scheme_version_id, rule_code) unique.
  * rule lookup: index on eligibility_rules.scheme_version_id.
  * eligibility history/idempotency: composite unique on
    (citizen_profile_id, profile_version_no, scheme_version_id,
    engine_version, idempotency_key) + index on (citizen_profile_id,
    scheme_version_id) for cache/history lookups.

DOCUMENTED EXTENSIONS beyond docs/database/data-dictionary.md (recorded in
the implementation report):
  * schemes.code (stable human-readable scheme code).
  * scheme_versions.created_by / published_by (four-eyes authorship, FR-ADMIN-2).
  * eligibility_rules.rule_code / mandatory / group_operator / parent_group_id
    / sort_order / source_citation (required by ai/rule-dsl.md).
  * eligibility_checks.engine_version / idempotency_key (prompt §18, §22).

Revision ID: 0002_scheme_eligibility_slice
Revises: 0001_auth_citizen_slice
Create Date: 2026-08-29
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_scheme_eligibility_slice"
down_revision: Union[str, None] = "0001_auth_citizen_slice"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    scheme_scope = postgresql.ENUM("central", "state", name="scheme_scope", create_type=False)
    version_status = postgresql.ENUM(
        "draft",
        "in_review",
        "published",
        "superseded",
        "archived",
        name="scheme_version_status",
        create_type=False,
    )
    postgresql.ENUM("central", "state", name="scheme_scope").create(bind, checkfirst=True)
    postgresql.ENUM(
        "draft", "in_review", "published", "superseded", "archived",
        name="scheme_version_status",
    ).create(bind, checkfirst=True)

    # --- schemes ---
    op.create_table(
        "schemes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("canonical_name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=True),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("administering_dept", sa.String(length=255), nullable=True),
        sa.Column("scope", scheme_scope, nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.UniqueConstraint("code", name="uq_schemes_code"),
    )
    op.create_index("ix_schemes_canonical_name", "schemes", ["canonical_name"])
    op.create_index("ix_schemes_category", "schemes", ["category"])

    # --- scheme_versions ---
    op.create_table(
        "scheme_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("scheme_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column("status", version_status, nullable=False, server_default="draft"),
        sa.Column("benefits_summary", sa.Text(), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("knowledge_source_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("published_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(["scheme_id"], ["schemes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["published_by"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("scheme_id", "version_no", name="uq_scheme_version_no"),
    )
    op.create_index("ix_scheme_versions_scheme_id", "scheme_versions", ["scheme_id"])
    op.create_index("ix_scheme_versions_status", "scheme_versions", ["status"])
    # At most one open-ended (currently-effective) published version per scheme.
    op.create_index(
        "uq_one_open_published_version_per_scheme",
        "scheme_versions",
        ["scheme_id"],
        unique=True,
        postgresql_where=sa.text("status = 'published' AND effective_to IS NULL"),
    )

    # --- eligibility_rules ---
    op.create_table(
        "eligibility_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("scheme_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("rule_code", sa.String(length=64), nullable=False),
        sa.Column("field_key", sa.String(length=64), nullable=False),
        sa.Column("operator", sa.String(length=16), nullable=False),
        sa.Column("value", postgresql.JSONB(), nullable=True),
        sa.Column("mandatory", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("group_id", sa.String(length=64), nullable=True),
        sa.Column("group_operator", sa.String(length=3), nullable=True),
        sa.Column("parent_group_id", sa.String(length=64), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("explanation_text", sa.Text(), nullable=False),
        sa.Column("source_citation", postgresql.JSONB(), nullable=True),
        sa.ForeignKeyConstraint(
            ["scheme_version_id"], ["scheme_versions.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint("scheme_version_id", "rule_code", name="uq_rule_code_per_version"),
    )
    op.create_index(
        "ix_eligibility_rules_scheme_version_id", "eligibility_rules", ["scheme_version_id"]
    )

    # --- eligibility_checks ---
    op.create_table(
        "eligibility_checks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("citizen_profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("profile_version_no", sa.Integer(), nullable=False),
        sa.Column("scheme_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("result", sa.String(length=32), nullable=False),
        sa.Column("rule_breakdown", postgresql.JSONB(), nullable=False),
        sa.Column("engine_version", sa.String(length=16), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        sa.Column(
            "computed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["citizen_profile_id"], ["citizen_profiles.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["scheme_version_id"], ["scheme_versions.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint(
            "citizen_profile_id",
            "profile_version_no",
            "scheme_version_id",
            "engine_version",
            "idempotency_key",
            name="uq_eligibility_idempotent",
        ),
    )
    op.create_index(
        "ix_eligibility_checks_profile_id", "eligibility_checks", ["citizen_profile_id"]
    )
    op.create_index(
        "ix_eligibility_checks_scheme_version_id", "eligibility_checks", ["scheme_version_id"]
    )
    op.create_index(
        "ix_eligibility_checks_profile_scheme",
        "eligibility_checks",
        ["citizen_profile_id", "scheme_version_id"],
    )
    op.create_index(
        "ix_eligibility_checks_computed_at", "eligibility_checks", ["computed_at"]
    )


def downgrade() -> None:
    op.drop_table("eligibility_checks")
    op.drop_table("eligibility_rules")
    op.drop_index("uq_one_open_published_version_per_scheme", table_name="scheme_versions")
    op.drop_table("scheme_versions")
    op.drop_table("schemes")

    bind = op.get_bind()
    for name in ("scheme_version_status", "scheme_scope"):
        postgresql.ENUM(name=name).drop(bind, checkfirst=True)
