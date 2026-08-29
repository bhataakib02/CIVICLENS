"""Pydantic domain schemas for Opportunity APIs (prompt §49, §51)."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.models.enums import (
    OpportunityApplicationStatus,
    OpportunityAuthorityLevel,
    OpportunityDeadlineStatus,
    OpportunityLinkType,
    OpportunitySourceType,
    OpportunityType,
)


# --- Opportunity Source Schemas ---

class OpportunitySourceCreate(BaseModel):
    name: str = Field(..., max_length=255)
    domain: str = Field(..., max_length=255)
    base_url: str
    source_type: OpportunitySourceType = OpportunitySourceType.OTHER
    country: str = "IN"
    state: Optional[str] = None
    authority_level: OpportunityAuthorityLevel = OpportunityAuthorityLevel.UNVERIFIED
    crawl_frequency: str = "daily"
    enabled: bool = True


class OpportunitySourceUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    base_url: Optional[str] = None
    source_type: Optional[OpportunitySourceType] = None
    authority_level: Optional[OpportunityAuthorityLevel] = None
    crawl_frequency: Optional[str] = None
    enabled: Optional[bool] = None


class OpportunitySourceResponse(BaseModel):
    id: uuid.UUID
    name: str
    domain: str
    base_url: str
    source_type: OpportunitySourceType
    country: str
    state: Optional[str] = None
    authority_level: OpportunityAuthorityLevel
    crawl_frequency: str
    enabled: bool
    last_crawled_at: Optional[datetime] = None
    last_successful_crawl_at: Optional[datetime] = None
    last_error_at: Optional[datetime] = None
    last_error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --- Opportunity Link & Version Schemas ---

class OpportunityLinkResponse(BaseModel):
    id: uuid.UUID
    opportunity_id: uuid.UUID
    url: str
    domain: str
    link_type: OpportunityLinkType
    source_page: Optional[str] = None
    verified_at: Optional[datetime] = None
    http_status: Optional[int] = None
    redirect_target: Optional[str] = None
    is_official: bool
    is_valid: bool

    class Config:
        from_attributes = True


class OpportunityVersionResponse(BaseModel):
    id: uuid.UUID
    opportunity_id: uuid.UUID
    version_number: int
    payload: Dict[str, Any]
    diff: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


# --- Opportunity Core Schemas ---

class OpportunityCreate(BaseModel):
    type: OpportunityType
    title: str = Field(..., max_length=500)
    organization: str = Field(..., max_length=255)
    organization_type: Optional[str] = None
    description: str
    summary: Optional[str] = None
    location: Optional[str] = None
    locations: List[str] = Field(default_factory=list)
    remote: bool = False
    employment_type: Optional[str] = None
    category: Optional[str] = None
    sector: Optional[str] = None
    skills: List[str] = Field(default_factory=list)

    education_requirements: List[str] = Field(default_factory=list)
    experience_requirements: Dict[str, Any] = Field(default_factory=dict)
    age_requirements: Dict[str, Any] = Field(default_factory=dict)
    income_requirements: Dict[str, Any] = Field(default_factory=dict)
    citizenship_requirements: List[str] = Field(default_factory=list)
    gender_requirements: List[str] = Field(default_factory=list)
    state_requirements: List[str] = Field(default_factory=list)
    category_requirements: List[str] = Field(default_factory=list)
    eligibility: List[str] = Field(default_factory=list)
    benefits: List[str] = Field(default_factory=list)

    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    stipend: Optional[str] = None
    fee: Optional[str] = None

    application_open_date: Optional[datetime] = None
    application_deadline: Optional[datetime] = None
    event_date: Optional[datetime] = None
    exam_date: Optional[datetime] = None
    interview_date: Optional[datetime] = None
    published_at: Optional[datetime] = None
    status: OpportunityDeadlineStatus = OpportunityDeadlineStatus.DATE_UNKNOWN

    source_url: str
    application_url: Optional[str] = None
    source_domain: str
    source_name: str
    source_type: str
    source_identifier: Optional[str] = None
    source_id: Optional[uuid.UUID] = None


class OpportunityResponse(BaseModel):
    id: uuid.UUID
    type: OpportunityType
    title: str
    organization: str
    organization_type: Optional[str] = None
    description: str
    summary: Optional[str] = None
    location: Optional[str] = None
    locations: List[str] = Field(default_factory=list)
    remote: bool
    employment_type: Optional[str] = None
    category: Optional[str] = None
    sector: Optional[str] = None
    skills: List[str] = Field(default_factory=list)

    education_requirements: List[str] = Field(default_factory=list)
    experience_requirements: Dict[str, Any] = Field(default_factory=dict)
    age_requirements: Dict[str, Any] = Field(default_factory=dict)
    income_requirements: Dict[str, Any] = Field(default_factory=dict)
    citizenship_requirements: List[str] = Field(default_factory=list)
    gender_requirements: List[str] = Field(default_factory=list)
    state_requirements: List[str] = Field(default_factory=list)
    category_requirements: List[str] = Field(default_factory=list)
    eligibility: List[str] = Field(default_factory=list)
    benefits: List[str] = Field(default_factory=list)

    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    stipend: Optional[str] = None
    fee: Optional[str] = None

    application_open_date: Optional[datetime] = None
    application_deadline: Optional[datetime] = None
    event_date: Optional[datetime] = None
    exam_date: Optional[datetime] = None
    interview_date: Optional[datetime] = None
    published_at: Optional[datetime] = None
    status: OpportunityDeadlineStatus

    source_url: str
    application_url: Optional[str] = None
    source_domain: str
    source_name: str
    source_type: str
    source_identifier: Optional[str] = None
    source_id: Optional[uuid.UUID] = None

    quality_score: float
    extraction_confidence: float
    is_canonical: bool
    last_seen_at: datetime
    last_verified_at: datetime
    content_hash: str
    created_at: datetime
    updated_at: datetime

    links: List[OpportunityLinkResponse] = Field(default_factory=list)
    match_breakdown: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class OpportunityListResponse(BaseModel):
    items: List[OpportunityResponse]
    total: int
    page: int
    page_size: int
    indexed_sources: int
    verified_sources: int
    last_crawl_time: Optional[datetime] = None
    last_verification_time: Optional[datetime] = None


# --- Subscription & Application Tracking Schemas ---

class OpportunitySubscriptionCreate(BaseModel):
    keywords: List[str] = Field(default_factory=list)
    types: List[OpportunityType] = Field(default_factory=list)
    categories: List[str] = Field(default_factory=list)
    locations: List[str] = Field(default_factory=list)
    min_salary: Optional[float] = None
    deadline_reminder_days: List[int] = Field(default_factory=lambda: [7, 3, 1])


class OpportunitySubscriptionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    keywords: List[str]
    types: List[OpportunityType]
    categories: List[str]
    locations: List[str]
    min_salary: Optional[float] = None
    deadline_reminder_days: List[int]
    enabled: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ApplicationTrackCreate(BaseModel):
    status: OpportunityApplicationStatus = OpportunityApplicationStatus.APPLIED
    notes: Optional[str] = None


class ApplicationTrackResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    opportunity_id: uuid.UUID
    status: OpportunityApplicationStatus
    notes: Optional[str] = None
    applied_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
