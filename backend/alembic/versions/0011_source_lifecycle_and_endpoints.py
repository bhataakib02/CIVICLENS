"""Source lifecycle states and multi-target endpoints (Phase 2).

Revision ID: 0011_source_lifecycle_and_endpoints
Revises: 0010_opportunity_phase4_fields
Create Date: 2026-08-30
"""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision = "0011_source_lifecycle_endpoints"
down_revision = "0010_opportunity_phase4_fields"
branch_labels = None
depends_on = None

LIFECYCLE_ENUM_VALUES = [
    "DISCOVERED",
    "VALIDATING",
    "PENDING_REVIEW",
    "APPROVED",
    "ACTIVE",
    "DEGRADED",
    "STALE",
    "FAILED",
    "BLOCKED",
    "RETIRED",
]


def upgrade() -> None:
    # 1. Create lifecycle enum type
    lifecycle_enum = postgresql.ENUM(*LIFECYCLE_ENUM_VALUES, name="opportunitysourcelifecyclestate")
    lifecycle_enum.create(op.get_bind(), checkfirst=True)

    # 2. Add lifecycle_state column with default ACTIVE
    op.add_column(
        "opportunity_sources",
        sa.Column(
            "lifecycle_state",
            lifecycle_enum,
            nullable=False,
            server_default="ACTIVE",
        ),
    )
    op.create_index("ix_opportunity_sources_lifecycle_state", "opportunity_sources", ["lifecycle_state"])

    # 3. Migrate existing 23 sources into appropriate lifecycle states based on real health status
    op.execute(
        """
        UPDATE opportunity_sources
        SET lifecycle_state = CASE
            WHEN enabled = FALSE THEN 'RETIRED'::opportunitysourcelifecyclestate
            WHEN health_status = 'BLOCKED' THEN 'BLOCKED'::opportunitysourcelifecyclestate
            WHEN health_status = 'DEGRADED' THEN 'DEGRADED'::opportunitysourcelifecyclestate
            WHEN health_status = 'STALE' THEN 'STALE'::opportunitysourcelifecyclestate
            WHEN health_status = 'FAILED' THEN 'FAILED'::opportunitysourcelifecyclestate
            ELSE 'ACTIVE'::opportunitysourcelifecyclestate
        END
        """
    )

    # 4. Create source_endpoints table for multi-endpoint crawling per source
    op.create_table(
        "source_endpoints",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("opportunity_sources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("connector_type", sa.String(length=50), nullable=False, server_default="HTML"),
        sa.Column("crawl_frequency", sa.String(length=50), nullable=False, server_default="30_minutes"),
        sa.Column("priority", sa.String(length=10), nullable=False, server_default="P1"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_crawled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_source_endpoints_source_id", "source_endpoints", ["source_id"])

    # 5. Populate primary endpoints from existing source base_urls
    op.execute(
        """
        INSERT INTO source_endpoints (id, source_id, name, url, connector_type, crawl_frequency, priority, enabled, created_at, updated_at)
        SELECT gen_random_uuid(), id, name || ' Main Endpoint', base_url, connector_type, crawl_frequency, priority, enabled, now(), now()
        FROM opportunity_sources
        """
    )


def downgrade() -> None:
    op.drop_index("ix_source_endpoints_source_id", table_name="source_endpoints")
    op.drop_table("source_endpoints")
    op.drop_index("ix_opportunity_sources_lifecycle_state", table_name="opportunity_sources")
    op.drop_column("opportunity_sources", "lifecycle_state")
    postgresql.ENUM(name="opportunitysourcelifecyclestate").drop(op.get_bind(), checkfirst=True)
