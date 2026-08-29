"""Natural language search parser and query filter builder (prompt §34, §35).

Parses natural language requests (e.g. "Find software internships in Bangalore for final year students closing this month")
into structured search filter models without raw SQL execution.
"""
from __future__ import annotations

import re
from typing import List, Optional
from pydantic import BaseModel, Field

from app.models.enums import OpportunityType, OpportunityDeadlineStatus


class OpportunitySearchFilter(BaseModel):
    query: Optional[str] = None
    type: Optional[OpportunityType] = None
    types: List[OpportunityType] = Field(default_factory=list)
    location: Optional[str] = None
    remote: Optional[bool] = None
    education: Optional[str] = None
    category: Optional[str] = None
    sector: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    min_salary: Optional[float] = None
    deadline_status: Optional[OpportunityDeadlineStatus] = None
    is_government: Optional[bool] = None
    closing_soon: Optional[bool] = None
    new_today: Optional[bool] = None
    upcoming: Optional[bool] = None


class NaturalLanguageSearchParser:
    """Translates natural language text into structured search filters safely."""

    def parse(self, text: str) -> OpportunitySearchFilter:
        clean = text.strip()
        text_lower = clean.lower()

        filters = OpportunitySearchFilter(query=clean)

        # Detect Opportunity Type
        if "internship" in text_lower or "intern" in text_lower:
            filters.type = OpportunityType.INTERNSHIP
        elif "scholarship" in text_lower:
            filters.type = OpportunityType.SCHOLARSHIP
        elif "scheme" in text_lower or "yojana" in text_lower:
            filters.type = OpportunityType.GOVERNMENT_SCHEME
        elif "fellowship" in text_lower:
            filters.type = OpportunityType.FELLOWSHIP
        elif "grant" in text_lower:
            filters.type = OpportunityType.GRANT
        elif "training" in text_lower or "skill" in text_lower:
            filters.type = OpportunityType.TRAINING
        elif "job" in text_lower or "recruitment" in text_lower or "vacancy" in text_lower:
            filters.type = OpportunityType.JOB

        # Detect Location
        city_match = re.search(r"\b(in|at|near)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b", clean)
        if city_match:
            filters.location = city_match.group(2)

        # Remote check
        if "remote" in text_lower or "work from home" in text_lower:
            filters.remote = True

        # Government vs Private check
        if "government" in text_lower or "govt" in text_lower or "public sector" in text_lower:
            filters.is_government = True
        elif "private" in text_lower or "company" in text_lower:
            filters.is_government = False

        # Deadline / Urgency
        if "closing soon" in text_lower or "this month" in text_lower or "urgent" in text_lower:
            filters.closing_soon = True
            filters.deadline_status = OpportunityDeadlineStatus.CLOSING_SOON

        # Education
        if "final year" in text_lower or "student" in text_lower or "graduate" in text_lower:
            filters.education = "Graduate"

        return filters
