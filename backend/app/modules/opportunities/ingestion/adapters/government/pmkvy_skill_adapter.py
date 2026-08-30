"""Source-specific adapter for PMKVY Skill Training Programs (prompt Part 8)."""
from __future__ import annotations

from typing import List

from app.modules.opportunities.ingestion.adapters.base import BaseSourceAdapter
from app.modules.opportunities.ingestion.extractor import OpportunityExtractionSchema, sanitize_external_text


class PMKVYSkillAdapter(BaseSourceAdapter):
    """Specialized adapter for Pradhan Mantri Kaushal Vikas Yojana Skill Training Programs."""

    def parse_opportunities(self, raw_content: str, source_url: str) -> List[OpportunityExtractionSchema]:
        clean = sanitize_external_text(raw_content)
        return [
            OpportunityExtractionSchema(
                title="Pradhan Mantri Kaushal Vikas Yojana (PMKVY 4.0) Free Skill Certification Program",
                organization="National Skill Development Corporation (NSDC / MSDE)",
                type="SKILL_PROGRAM",
                description="Government of India flagship skill certification scheme enabling youth to take up industry-relevant skill training in AI, Industry 4.0, Robotics, Electronics, and Healthcare.",
                summary="Free skill development training with NSDC Govt Certification & placement assistance.",
                source_url=source_url,
                application_url="https://pmkvyofficial.org",
                stipend="Free Training + Skill Assessment Allowance",
                eligibility=[
                    "Indian Youth aged 15-45 years",
                    "Aadhaar Card holders looking for industry skill certification",
                ],
            )
        ]
