"""AI Extraction and validation engine for unstructured web & doc content (prompt §13, §14, §45, §46).

Extracts structured Pydantic schema and guards against prompt injection and malicious HTML.
"""
from __future__ import annotations

import re
import html
from typing import Any, List, Optional
from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.models.enums import OpportunityType

logger = get_logger("civiclens.opportunities.extractor")


class OpportunitySalarySchema(BaseModel):
    min: Optional[float] = None
    max: Optional[float] = None
    currency: str = "INR"


class OpportunityExtractionSchema(BaseModel):
    title: str = Field(..., description="Title of the opportunity")
    organization: str = Field(..., description="Publishing organization or department")
    type: str = Field(default="JOB", description="JOB, INTERNSHIP, SCHOLARSHIP, GOVERNMENT_SCHEME, etc.")
    description: str = Field(default="", description="Detailed summary description")
    summary: Optional[str] = None
    location: Optional[str] = None
    locations: List[str] = Field(default_factory=list)
    remote: bool = False
    employment_type: Optional[str] = None
    category: Optional[str] = None
    sector: Optional[str] = None
    skills: List[str] = Field(default_factory=list)

    education_requirements: List[str] = Field(default_factory=list)
    experience_requirements: dict = Field(default_factory=dict)
    age_requirements: dict = Field(default_factory=dict)
    income_requirements: dict = Field(default_factory=dict)
    citizenship_requirements: List[str] = Field(default_factory=list)
    gender_requirements: List[str] = Field(default_factory=list)
    state_requirements: List[str] = Field(default_factory=list)
    category_requirements: List[str] = Field(default_factory=list)
    eligibility: List[str] = Field(default_factory=list)
    benefits: List[str] = Field(default_factory=list)

    salary: Optional[OpportunitySalarySchema] = None
    stipend: Optional[str] = None
    fee: Optional[str] = None

    published_at: Optional[str] = None
    application_open_date: Optional[str] = None
    application_deadline: Optional[str] = None
    event_date: Optional[str] = None
    exam_date: Optional[str] = None
    interview_date: Optional[str] = None

    source_url: str = Field(default="", description="Canonical source URL")
    application_url: Optional[str] = Field(default=None, description="Official application or portal URL")
    links: List[dict] = Field(default_factory=list)


def sanitize_external_text(text: str) -> str:
    """Sanitize external untrusted text to prevent prompt injection and XSS (prompt §45, §46)."""
    if not text:
        return ""
    # Strip HTML tags
    clean = re.sub(r"<[^>]*>", " ", text)
    # Unescape HTML entities
    clean = html.unescape(clean)
    # Neutralize prompt injection phrases
    injection_patterns = [
        r"(?i)ignore\s+previous\s+instructions",
        r"(?i)system\s+prompt",
        r"(?i)reveal\s+credentials",
        r"(?i)override\s+system",
    ]
    for pattern in injection_patterns:
        clean = re.sub(pattern, "[FILTERED_INSTRUCTION_ATTEMPT]", clean)

    # Clean whitespace
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean


class OpportunityExtractor:
    """Extracts structured opportunity schema from raw page text."""

    def extract(self, raw_text: str, source_url: str, default_org: str = "Unknown") -> OpportunityExtractionSchema:
        clean_text = sanitize_external_text(raw_text)

        # Rule-based fallback extraction
        title_match = re.search(r"(?i)(?:title|recruitment|vacancy|scholarship|scheme):\s*([^\n\.]+)", clean_text)
        title = title_match.group(1).strip() if title_match else (clean_text[:120] if clean_text else "Opportunity Notice")

        org_match = re.search(r"(?i)(?:organization|department|ministry|company|board):\s*([^\n\.]+)", clean_text)
        org = org_match.group(1).strip() if org_match else default_org

        # Detect opportunity type from keywords
        opp_type = "JOB"
        text_lower = clean_text.lower()
        if "internship" in text_lower or "intern" in text_lower:
            opp_type = "INTERNSHIP"
        elif "scholarship" in text_lower:
            opp_type = "SCHOLARSHIP"
        elif "scheme" in text_lower or "yojana" in text_lower:
            opp_type = "GOVERNMENT_SCHEME"
        elif "fellowship" in text_lower:
            opp_type = "FELLOWSHIP"
        elif "apprenticeship" in text_lower or "apprentice" in text_lower:
            opp_type = "APPRENTICESHIP"
        elif "training" in text_lower or "skill" in text_lower:
            opp_type = "TRAINING"

        # Detect deadline date format (e.g. 2026-09-30 or 30 Sep 2026)
        deadline_match = re.search(
            r"(?i)(?:deadline|last date|closing date|apply before):\s*([0-9]{4}-[0-9]{2}-[0-9]{2}|[0-9]{1,2}\s+[A-Za-z]{3,9}\s+[0-9]{4})",
            clean_text,
        )
        deadline_str = deadline_match.group(1).strip() if deadline_match else None

        # Detect apply link
        apply_url_match = re.search(r'https?://[^\s<"]+apply[^\s<"]*', raw_text, re.IGNORECASE)
        app_url = apply_url_match.group(0) if apply_url_match else source_url

        return OpportunityExtractionSchema(
            title=title[:255],
            organization=org[:255],
            type=opp_type,
            description=clean_text[:5000] if clean_text else title,
            summary=clean_text[:300] if clean_text else None,
            source_url=source_url,
            application_url=app_url,
            application_deadline=deadline_str,
            eligibility=["As per official notification guidelines"],
        )
