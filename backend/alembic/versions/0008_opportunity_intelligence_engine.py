"""Opportunity Intelligence Engine tables (Unified Government + Private Opportunity Discovery Engine).

Revision ID: 0008_opportunity_intelligence_engine
Revises: 0007_otp_and_consents
Create Date: 2026-08-29
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008_opportunity_intel_engine"
down_revision: Union[str, None] = "0007_otp_and_consents"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_OPPORTUNITY_TYPE = (
    "JOB",
    "INTERNSHIP",
    "APPRENTICESHIP",
    "SCHOLARSHIP",
    "FELLOWSHIP",
    "GOVERNMENT_SCHEME",
    "GRANT",
    "TRAINING",
    "SKILL_PROGRAM",
    "JOB_FAIR",
    "COMPETITION",
    "ADMISSION",
    "OTHER",
)

_SOURCE_TYPE = (
    "CENTRAL_GOVERNMENT",
    "STATE_GOVERNMENT",
    "PUBLIC_INSTITUTION",
    "UNIVERSITY",
    "PSU",
    "PRIVATE_COMPANY",
    "NGO",
    "FOUNDATION",
    "EDUCATIONAL_INSTITUTION",
    "OTHER",
)

_AUTHORITY_LEVEL = (
    "OFFICIAL",
    "VERIFIED_PARTNER",
    "KNOWN_PRIVATE",
    "UNVERIFIED",
)

_DEADLINE_STATUS = (
    "UPCOMING",
    "OPEN",
    "CLOSING_SOON",
    "CLOSED",
    "DATE_UNKNOWN",
)

_LINK_TYPE = (
    "NOTIFICATION",
    "APPLY",
    "REGISTRATION",
    "LOGIN",
    "DOWNLOAD",
    "RESULT",
    "SYLLABUS",
)

_APPLICATION_TRACK_STATUS = (
    "NOT_APPLIED",
    "APPLIED",
    "INTERVIEW",
    "SELECTED",
    "REJECTED",
    "WITHDRAWN",
)


def _mk(bind, name, values):
    postgresql.ENUM(*values, name=name).create(bind, checkfirst=True)
    return postgresql.ENUM(*values, name=name, create_type=False)


def upgrade() -> None:
    bind = op.get_bind()

    opp_type_enum = _mk(bind, "opportunity_type", _OPPORTUNITY_TYPE)
    source_type_enum = _mk(bind, "opportunity_source_type", _SOURCE_TYPE)
    authority_enum = _mk(bind, "opportunity_authority_level", _AUTHORITY_LEVEL)
    deadline_status_enum = _mk(bind, "opportunity_deadline_status", _DEADLINE_STATUS)
    link_type_enum = _mk(bind, "opportunity_link_type", _LINK_TYPE)
    app_track_status_enum = _mk(bind, "opportunity_application_status", _APPLICATION_TRACK_STATUS)

    # 1. opportunity_sources
    op.create_table(
        "opportunity_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("domain", sa.String(255), nullable=False),
        sa.Column("base_url", sa.Text(), nullable=False),
        sa.Column("source_type", source_type_enum, nullable=False, server_default="OTHER"),
        sa.Column("country", sa.String(10), nullable=False, server_default="IN"),
        sa.Column("state", sa.String(100), nullable=True),
        sa.Column("authority_level", authority_enum, nullable=False, server_default="UNVERIFIED"),
        sa.Column("robots_policy", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("crawl_policy", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("crawl_frequency", sa.String(50), nullable=False, server_default="daily"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("health_status", sa.String(50), nullable=False, server_default="HEALTHY"),
        sa.Column("consecutive_failures", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_crawl_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_crawl_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_crawled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_successful_crawl_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_failed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_opportunity_sources_domain", "opportunity_sources", ["domain"])

    # 2. opportunities
    op.create_table(
        "opportunities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("type", opp_type_enum, nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("organization", sa.String(255), nullable=False),
        sa.Column("organization_type", sa.String(100), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("locations", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("remote", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("employment_type", sa.String(100), nullable=True),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("sector", sa.String(100), nullable=True),
        sa.Column("skills", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("education_requirements", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("experience_requirements", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("age_requirements", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("income_requirements", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("citizenship_requirements", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("gender_requirements", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("state_requirements", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("category_requirements", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("eligibility", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("benefits", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("salary_min", sa.Float(), nullable=True),
        sa.Column("salary_max", sa.Float(), nullable=True),
        sa.Column("stipend", sa.String(100), nullable=True),
        sa.Column("fee", sa.String(100), nullable=True),
        sa.Column("application_open_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("application_deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("event_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("exam_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("interview_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", deadline_status_enum, nullable=False, server_default="DATE_UNKNOWN"),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("application_url", sa.Text(), nullable=True),
        sa.Column("source_domain", sa.String(255), nullable=False),
        sa.Column("source_name", sa.String(255), nullable=False),
        sa.Column("source_type", sa.String(100), nullable=False),
        sa.Column("source_identifier", sa.String(255), nullable=True),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("opportunity_sources.id", ondelete="SET NULL"), nullable=True),
        sa.Column("quality_score", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("extraction_confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("is_canonical", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("canonical_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("opportunities.id", ondelete="SET NULL"), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_opportunities_type", "opportunities", ["type"])
    op.create_index("ix_opportunities_title", "opportunities", ["title"])
    op.create_index("ix_opportunities_organization", "opportunities", ["organization"])
    op.create_index("ix_opportunities_category", "opportunities", ["category"])
    op.create_index("ix_opportunities_sector", "opportunities", ["sector"])
    op.create_index("ix_opportunities_deadline", "opportunities", ["application_deadline"])
    op.create_index("ix_opportunities_published_at", "opportunities", ["published_at"])
    op.create_index("ix_opportunities_status", "opportunities", ["status"])
    op.create_index("ix_opportunities_source_domain", "opportunities", ["source_domain"])
    op.create_index("ix_opportunities_source_identifier", "opportunities", ["source_identifier"])
    op.create_index("ix_opportunities_content_hash", "opportunities", ["content_hash"])

    # 3. opportunity_versions
    op.create_table(
        "opportunity_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("diff", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_opportunity_versions_opportunity_id", "opportunity_versions", ["opportunity_id"])

    # 4. opportunity_links
    op.create_table(
        "opportunity_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("domain", sa.String(255), nullable=False),
        sa.Column("link_type", link_type_enum, nullable=False, server_default="APPLY"),
        sa.Column("source_page", sa.Text(), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("redirect_target", sa.Text(), nullable=True),
        sa.Column("is_official", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_valid", sa.Boolean(), nullable=False, server_default="true"),
    )
    op.create_index("ix_opportunity_links_opportunity_id", "opportunity_links", ["opportunity_id"])

    # 5. opportunity_subscriptions
    op.create_table(
        "opportunity_subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("keywords", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("types", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("categories", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("locations", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("min_salary", sa.Float(), nullable=True),
        sa.Column("deadline_reminder_days", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[7,3,1]"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_opportunity_subscriptions_user_id", "opportunity_subscriptions", ["user_id"])

    # 6. opportunity_alerts
    op.create_table(
        "opportunity_alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("alert_type", sa.String(50), nullable=False),
        sa.Column("opportunity_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("opportunity_id", "user_id", "alert_type", "opportunity_version", name="uq_opportunity_alert_dedup"),
    )
    op.create_index("ix_opportunity_alerts_user_id", "opportunity_alerts", ["user_id"])
    op.create_index("ix_opportunity_alerts_opportunity_id", "opportunity_alerts", ["opportunity_id"])

    # 6b. raw_crawl_snapshots
    op.create_table(
        "raw_crawl_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("opportunity_sources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("content_type", sa.String(100), nullable=False, server_default="text/html"),
        sa.Column("size_bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("raw_content", sa.Text(), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_raw_crawl_snapshots_source_id", "raw_crawl_snapshots", ["source_id"])
    op.create_index("ix_raw_crawl_snapshots_content_hash", "raw_crawl_snapshots", ["content_hash"])


    # 7. opportunity_changes
    op.create_table(
        "opportunity_changes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("change_type", sa.String(100), nullable=False),
        sa.Column("old_value", sa.Text(), nullable=True),
        sa.Column("new_value", sa.Text(), nullable=True),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_opportunity_changes_opportunity_id", "opportunity_changes", ["opportunity_id"])

    # 8. opportunity_application_tracks
    op.create_table(
        "opportunity_application_tracks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", app_track_status_enum, nullable=False, server_default="APPLIED"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_opportunity_application_tracks_user_id", "opportunity_application_tracks", ["user_id"])
    op.create_index("ix_opportunity_application_tracks_opportunity_id", "opportunity_application_tracks", ["opportunity_id"])

    # 9. crawl_runs
    op.create_table(
        "crawl_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("opportunity_sources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="RUNNING"),
        sa.Column("pages_fetched", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pages_changed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pages_skipped", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("opportunities_found", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("opportunities_updated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duplicates_detected", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("errors_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Float(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_crawl_runs_source_id", "crawl_runs", ["source_id"])

    # 10. crawl_items
    op.create_table(
        "crawl_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("crawl_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("crawl_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("action_taken", sa.String(50), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_crawl_items_crawl_run_id", "crawl_items", ["crawl_run_id"])

    # 11. link_verifications
    op.create_table(
        "link_verifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("link_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("opportunity_links.id", ondelete="CASCADE"), nullable=False),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("is_valid", sa.Boolean(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_link_verifications_link_id", "link_verifications", ["link_id"])


def downgrade() -> None:
    op.drop_table("raw_crawl_snapshots")
    op.drop_table("link_verifications")
    op.drop_table("crawl_items")

    op.drop_table("crawl_runs")
    op.drop_table("opportunity_application_tracks")
    op.drop_table("opportunity_changes")
    op.drop_table("opportunity_alerts")
    op.drop_table("opportunity_subscriptions")
    op.drop_table("opportunity_links")
    op.drop_table("opportunity_versions")
    op.drop_table("opportunities")
    op.drop_table("opportunity_sources")

    op.execute("DROP TYPE IF EXISTS opportunity_application_status")
    op.execute("DROP TYPE IF EXISTS opportunity_link_type")
    op.execute("DROP TYPE IF EXISTS opportunity_deadline_status")
    op.execute("DROP TYPE IF EXISTS opportunity_authority_level")
    op.execute("DROP TYPE IF EXISTS opportunity_source_type")
    op.execute("DROP TYPE IF EXISTS opportunity_type")
