"""SQLAlchemy models for the Opportunity Intelligence Engine."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.enums import (
    OpportunityApplicationStatus,
    OpportunityAuthorityLevel,
    OpportunityDeadlineStatus,
    OpportunityLinkType,
    OpportunitySourceType,
    OpportunityType,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class OpportunitySource(Base):
    """Source registry entry representing authoritative government or private source."""

    __tablename__ = "opportunity_sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    domain = Column(String(255), nullable=False, index=True)
    base_url = Column(Text, nullable=False)
    source_type = Column(
        Enum(OpportunitySourceType),
        nullable=False,
        default=OpportunitySourceType.OTHER,
    )
    country = Column(String(10), nullable=False, default="IN")
    state = Column(String(100), nullable=True)
    authority_level = Column(
        Enum(OpportunityAuthorityLevel),
        nullable=False,
        default=OpportunityAuthorityLevel.UNVERIFIED,
    )
    robots_policy = Column(JSONB, nullable=False, default=dict)
    crawl_policy = Column(JSONB, nullable=False, default=dict)
    crawl_frequency = Column(String(50), nullable=False, default="daily")  # hourly, 6h, daily
    enabled = Column(Boolean, nullable=False, default=True)

    priority = Column(String(10), nullable=False, default="P1", index=True)  # P0, P1, P2, P3
    district = Column(String(100), nullable=True)
    geographic_scope = Column(String(50), nullable=False, default="NATIONAL")  # NATIONAL, STATE, DISTRICT, CITY, REMOTE
    last_failure_stage = Column(String(50), nullable=True)  # DNS_FAILED, HTTP_ERROR, ROBOTS_BLOCKED, TIMEOUT, PARSER_FAILED, EXTRACTION_FAILED, VALIDATION_FAILED, CRAWL_SUCCESS_ZERO_OPPORTUNITIES, NONE

    # Source Health Metrics (Prompt Amendment §8)
    health_status = Column(String(50), nullable=False, default="HEALTHY")  # HEALTHY, STALE, DEGRADED, BLOCKED, DISABLED
    consecutive_failures = Column(Integer, nullable=False, default=0)
    last_crawl_started_at = Column(DateTime(timezone=True), nullable=True)
    last_crawl_completed_at = Column(DateTime(timezone=True), nullable=True)
    last_crawled_at = Column(DateTime(timezone=True), nullable=True)
    last_successful_crawl_at = Column(DateTime(timezone=True), nullable=True)
    last_failed_at = Column(DateTime(timezone=True), nullable=True)
    last_error_at = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now, onupdate=_utc_now)

    opportunities = relationship("Opportunity", back_populates="source", cascade="all, delete-orphan")
    crawl_runs = relationship("CrawlRun", back_populates="source", cascade="all, delete-orphan")
    raw_snapshots = relationship("RawCrawlSnapshot", back_populates="source", cascade="all, delete-orphan")



class Opportunity(Base):
    """Normalized Opportunity model covering jobs, internships, scholarships, schemes, etc."""

    __tablename__ = "opportunities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(Enum(OpportunityType), nullable=False, index=True)
    title = Column(String(500), nullable=False, index=True)
    organization = Column(String(255), nullable=False, index=True)
    organization_type = Column(String(100), nullable=True)

    description = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)
    locations = Column(JSONB, nullable=False, default=list)
    remote = Column(Boolean, nullable=False, default=False)
    employment_type = Column(String(100), nullable=True)
    category = Column(String(100), nullable=True, index=True)
    sector = Column(String(100), nullable=True, index=True)
    skills = Column(JSONB, nullable=False, default=list)

    district = Column(String(100), nullable=True)
    geographic_scope = Column(String(50), nullable=False, default="NATIONAL")

    # Criteria JSON specs
    education_requirements = Column(JSONB, nullable=False, default=list)
    experience_requirements = Column(JSONB, nullable=False, default=dict)
    age_requirements = Column(JSONB, nullable=False, default=dict)
    income_requirements = Column(JSONB, nullable=False, default=dict)
    citizenship_requirements = Column(JSONB, nullable=False, default=list)
    gender_requirements = Column(JSONB, nullable=False, default=list)
    state_requirements = Column(JSONB, nullable=False, default=list)
    category_requirements = Column(JSONB, nullable=False, default=list)
    eligibility = Column(JSONB, nullable=False, default=list)
    benefits = Column(JSONB, nullable=False, default=list)

    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    stipend = Column(String(100), nullable=True)
    fee = Column(String(100), nullable=True)

    # Dates
    application_open_date = Column(DateTime(timezone=True), nullable=True)
    application_deadline = Column(DateTime(timezone=True), nullable=True, index=True)
    event_date = Column(DateTime(timezone=True), nullable=True)
    exam_date = Column(DateTime(timezone=True), nullable=True)
    interview_date = Column(DateTime(timezone=True), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True, index=True)
    status = Column(
        Enum(OpportunityDeadlineStatus),
        nullable=False,
        default=OpportunityDeadlineStatus.DATE_UNKNOWN,
        index=True,
    )

    # Link & Source provenance
    source_url = Column(Text, nullable=False)
    application_url = Column(Text, nullable=True)
    source_domain = Column(String(255), nullable=False, index=True)
    source_name = Column(String(255), nullable=False)
    source_type = Column(String(100), nullable=False)
    source_identifier = Column(String(255), nullable=True, index=True)
    source_id = Column(UUID(as_uuid=True), ForeignKey("opportunity_sources.id", ondelete="SET NULL"), nullable=True)

    # Audit & Quality metrics
    quality_score = Column(Float, nullable=False, default=1.0)
    extraction_confidence = Column(Float, nullable=False, default=1.0)
    is_canonical = Column(Boolean, nullable=False, default=True)
    canonical_id = Column(UUID(as_uuid=True), ForeignKey("opportunities.id", ondelete="SET NULL"), nullable=True)

    last_seen_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)
    last_verified_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)
    content_hash = Column(String(64), nullable=False, index=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now, onupdate=_utc_now)

    source = relationship("OpportunitySource", back_populates="opportunities")
    links = relationship("OpportunityLink", back_populates="opportunity", cascade="all, delete-orphan")
    versions = relationship("OpportunityVersion", back_populates="opportunity", cascade="all, delete-orphan")
    changes = relationship("OpportunityChange", back_populates="opportunity", cascade="all, delete-orphan")
    user_tracks = relationship("OpportunityApplicationTrack", back_populates="opportunity", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_opp_type_status", "type", "status"),
        Index("idx_opp_deadline", "application_deadline"),
    )


class OpportunityVersion(Base):
    """Historical versioning for opportunity updates."""

    __tablename__ = "opportunity_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    opportunity_id = Column(UUID(as_uuid=True), ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    payload = Column(JSONB, nullable=False)
    diff = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)

    opportunity = relationship("Opportunity", back_populates="versions")


class OpportunityLink(Base):
    """Link extraction, classification and audit provenance."""

    __tablename__ = "opportunity_links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    opportunity_id = Column(UUID(as_uuid=True), ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False, index=True)
    url = Column(Text, nullable=False)
    domain = Column(String(255), nullable=False)
    link_type = Column(Enum(OpportunityLinkType), nullable=False, default=OpportunityLinkType.APPLY)
    source_page = Column(Text, nullable=True)

    verified_at = Column(DateTime(timezone=True), nullable=True)
    http_status = Column(Integer, nullable=True)
    redirect_target = Column(Text, nullable=True)
    is_official = Column(Boolean, nullable=False, default=True)
    is_valid = Column(Boolean, nullable=False, default=True)

    opportunity = relationship("Opportunity", back_populates="links")


class OpportunitySubscription(Base):
    """Alert subscriptions for matched opportunities & deadlines."""

    __tablename__ = "opportunity_subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    keywords = Column(JSONB, nullable=False, default=list)
    types = Column(JSONB, nullable=False, default=list)
    categories = Column(JSONB, nullable=False, default=list)
    locations = Column(JSONB, nullable=False, default=list)
    min_salary = Column(Float, nullable=True)
    deadline_reminder_days = Column(JSONB, nullable=False, default=lambda: [7, 3, 1])
    enabled = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now, onupdate=_utc_now)


class OpportunityAlert(Base):
    """Sent deadline reminder or opportunity alert log (deduplicated per user + opp + alert_type + version)."""

    __tablename__ = "opportunity_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    opportunity_id = Column(UUID(as_uuid=True), ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False, index=True)
    alert_type = Column(String(50), nullable=False)  # NEW_MATCH, DEADLINE_REMINDER, CHANGE_ALERT
    opportunity_version = Column(Integer, nullable=False, default=1)
    message = Column(Text, nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)

    __table_args__ = (
        UniqueConstraint("opportunity_id", "user_id", "alert_type", "opportunity_version", name="uq_opportunity_alert_dedup"),
    )


class RawCrawlSnapshot(Base):
    """Raw crawled document snapshot with retention rules (prompt §2)."""

    __tablename__ = "raw_crawl_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("opportunity_sources.id", ondelete="CASCADE"), nullable=False, index=True)
    url = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False, index=True)
    content_type = Column(String(100), nullable=False, default="text/html")
    size_bytes = Column(Integer, nullable=False, default=0)
    raw_content = Column(Text, nullable=False)
    retrieved_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)
    expires_at = Column(DateTime(timezone=True), nullable=True)  # retention policy cutoff

    source = relationship("OpportunitySource", back_populates="raw_snapshots")



class OpportunityChange(Base):
    """Structured record of changes when source documents update."""

    __tablename__ = "opportunity_changes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    opportunity_id = Column(UUID(as_uuid=True), ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False, index=True)
    change_type = Column(String(100), nullable=False)  # DEADLINE_CHANGED, APPLY_LINK_CHANGED, ELIGIBILITY_CHANGED
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    detected_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)

    opportunity = relationship("Opportunity", back_populates="changes")


class OpportunityApplicationTrack(Base):
    """Citizen external application tracking record."""

    __tablename__ = "opportunity_application_tracks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    opportunity_id = Column(UUID(as_uuid=True), ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(Enum(OpportunityApplicationStatus), nullable=False, default=OpportunityApplicationStatus.APPLIED)
    notes = Column(Text, nullable=True)

    applied_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now, onupdate=_utc_now)

    opportunity = relationship("Opportunity", back_populates="user_tracks")


class CrawlRun(Base):
    """Audit log and metrics for a crawl run on a source."""

    __tablename__ = "crawl_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("opportunity_sources.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="RUNNING")  # RUNNING, COMPLETED, FAILED
    failure_stage = Column(String(50), nullable=True)  # DNS_FAILED, HTTP_ERROR, ROBOTS_BLOCKED, TIMEOUT, PARSER_FAILED, EXTRACTION_FAILED, VALIDATION_FAILED, CRAWL_SUCCESS_ZERO_OPPORTUNITIES, NONE
    pages_fetched = Column(Integer, nullable=False, default=0)
    pages_changed = Column(Integer, nullable=False, default=0)
    pages_skipped = Column(Integer, nullable=False, default=0)
    opportunities_found = Column(Integer, nullable=False, default=0)
    opportunities_updated = Column(Integer, nullable=False, default=0)
    duplicates_detected = Column(Integer, nullable=False, default=0)
    errors_count = Column(Integer, nullable=False, default=0)
    error_summary = Column(Text, nullable=True)

    duration_ms = Column(Float, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    source = relationship("OpportunitySource", back_populates="crawl_runs")


class CrawlItem(Base):
    """Detailed item log within a crawl run."""

    __tablename__ = "crawl_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    crawl_run_id = Column(UUID(as_uuid=True), ForeignKey("crawl_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    url = Column(Text, nullable=False)
    status_code = Column(Integer, nullable=True)
    content_hash = Column(String(64), nullable=True)
    action_taken = Column(String(50), nullable=False)  # PARSED, SKIPPED_UNCHANGED, FAILED
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)


class LinkVerification(Base):
    """Link verification check log."""

    __tablename__ = "link_verifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    link_id = Column(UUID(as_uuid=True), ForeignKey("opportunity_links.id", ondelete="CASCADE"), nullable=False, index=True)
    http_status = Column(Integer, nullable=True)
    is_valid = Column(Boolean, nullable=False)
    error_message = Column(Text, nullable=True)
    checked_at = Column(DateTime(timezone=True), nullable=False, default=_utc_now)
