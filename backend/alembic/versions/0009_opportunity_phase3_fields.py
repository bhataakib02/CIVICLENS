"""Phase 3 opportunity metadata, priority tiers, geographic target, and failure stage fields.

Revision ID: 0009_opportunity_phase3_fields
Revises: 0008_opportunity_intel_engine
Create Date: 2026-08-30
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0009_opportunity_phase3_fields"
down_revision: Union[str, None] = "0008_opportunity_intel_engine"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add priority, district, geographic_scope, last_failure_stage to opportunity_sources
    op.add_column("opportunity_sources", sa.Column("priority", sa.String(length=10), nullable=False, server_default="P1"))
    op.add_column("opportunity_sources", sa.Column("district", sa.String(length=100), nullable=True))
    op.add_column("opportunity_sources", sa.Column("geographic_scope", sa.String(length=50), nullable=False, server_default="NATIONAL"))
    op.add_column("opportunity_sources", sa.Column("last_failure_stage", sa.String(length=50), nullable=True))
    op.create_index(op.f("ix_opportunity_sources_priority"), "opportunity_sources", ["priority"], unique=False)

    # Add district, geographic_scope to opportunities
    op.add_column("opportunities", sa.Column("district", sa.String(length=100), nullable=True))
    op.add_column("opportunities", sa.Column("geographic_scope", sa.String(length=50), nullable=False, server_default="NATIONAL"))

    # Add failure_stage to crawl_runs
    op.add_column("crawl_runs", sa.Column("failure_stage", sa.String(length=50), nullable=True))


def downgrade() -> None:
    op.drop_column("crawl_runs", "failure_stage")

    op.drop_column("opportunities", "geographic_scope")
    op.drop_column("opportunities", "district")

    op.drop_index(op.f("ix_opportunity_sources_priority"), table_name="opportunity_sources")
    op.drop_column("opportunity_sources", "last_failure_stage")
    op.drop_column("opportunity_sources", "geographic_scope")
    op.drop_column("opportunity_sources", "district")
    op.drop_column("opportunity_sources", "priority")
