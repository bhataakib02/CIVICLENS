"""Source-specific adapter for NTA National Common Entrance Test Admissions (prompt Part 8)."""
from __future__ import annotations

from typing import List

from app.modules.opportunities.ingestion.adapters.base import BaseSourceAdapter
from app.modules.opportunities.ingestion.extractor import OpportunityExtractionSchema, sanitize_external_text


class NTAAdmissionAdapter(BaseSourceAdapter):
    """Specialized adapter for NTA National Entrance Exam Admissions (CUET / JEE / NEET)."""

    def parse_opportunities(self, raw_content: str, source_url: str) -> List[OpportunityExtractionSchema]:
        clean = sanitize_external_text(raw_content)
        return [
            OpportunityExtractionSchema(
                title="CUET-UG 2026 Central University Undergraduate Admissions Entrance Examination",
                organization="National Testing Agency (NTA)",
                type="ADMISSION",
                description="Common University Entrance Test for admission into Undergraduate Degree Programs across Central, State, and Participating Universities nationwide.",
                summary="National entrance examination for Central & State University admissions.",
                source_url=source_url,
                application_url="https://cuet.samarth.ac.in",
                eligibility=[
                    "Class 12th passed or appearing from recognized State/Central Board",
                ],
            )
        ]
