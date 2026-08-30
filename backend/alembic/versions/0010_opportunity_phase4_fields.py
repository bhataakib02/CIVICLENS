"""Phase 4 configuration-driven source fields and quality metric columns.

Revision ID: 0010_opportunity_phase4_fields
Revises: 0009_opportunity_phase3_fields
Create Date: 2026-08-30
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0010_opportunity_phase4_fields"
down_revision: Union[str, None] = "0009_opportunity_phase3_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("opportunity_sources", sa.Column("source_category", sa.String(length=100), nullable=True))
    op.add_column("opportunity_sources", sa.Column("connector_type", sa.String(length=50), nullable=False, server_default="HTML"))
    op.add_column("opportunity_sources", sa.Column("seed_urls", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"))
    op.add_column("opportunity_sources", sa.Column("allowed_paths", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"))
    op.add_column("opportunity_sources", sa.Column("excluded_paths", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"))
    op.add_column("opportunity_sources", sa.Column("rate_limit", sa.Float(), nullable=False, server_default="1.0"))
    op.add_column("opportunity_sources", sa.Column("opportunity_types", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"))

    op.add_column("opportunity_sources", sa.Column("overall_quality_score", sa.Float(), nullable=False, server_default="1.0"))
    op.add_column("opportunity_sources", sa.Column("reliability_score", sa.Float(), nullable=False, server_default="1.0"))
    op.add_column("opportunity_sources", sa.Column("crawl_success_rate", sa.Float(), nullable=False, server_default="1.0"))
    op.add_column("opportunity_sources", sa.Column("extraction_success_rate", sa.Float(), nullable=False, server_default="1.0"))
    op.add_column("opportunity_sources", sa.Column("link_success_rate", sa.Float(), nullable=False, server_default="1.0"))


def downgrade() -> None:
    op.drop_column("opportunity_sources", "link_success_rate")
    op.drop_column("opportunity_sources", "extraction_success_rate")
    op.drop_column("opportunity_sources", "crawl_success_rate")
    op.drop_column("opportunity_sources", "reliability_score")
    op.drop_column("opportunity_sources", "overall_quality_score")

    op.drop_column("opportunity_sources", "opportunity_types")
    op.drop_column("opportunity_sources", "rate_limit")
    op.drop_column("opportunity_sources", "excluded_paths")
    op.drop_column("opportunity_sources", "allowed_paths")
    op.drop_column("opportunity_sources", "seed_urls")
    op.drop_column("opportunity_sources", "connector_type")
    op.drop_column("opportunity_sources", "source_category")
