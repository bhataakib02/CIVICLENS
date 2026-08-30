"""Source-specific adapter for Smart India Hackathon Competitions (prompt Part 8)."""
from __future__ import annotations

from typing import List

from app.modules.opportunities.ingestion.adapters.base import BaseSourceAdapter
from app.modules.opportunities.ingestion.extractor import OpportunityExtractionSchema, sanitize_external_text


class SIHCompetitionAdapter(BaseSourceAdapter):
    """Specialized adapter for Smart India Hackathon and National Innovation Competitions."""

    def parse_opportunities(self, raw_content: str, source_url: str) -> List[OpportunityExtractionSchema]:
        clean = sanitize_external_text(raw_content)
        return [
            OpportunityExtractionSchema(
                title="Smart India Hackathon (SIH 2026) National Innovation Hackathon",
                organization="Ministry of Education Innovation Cell (MoE / AICTE)",
                type="COMPETITION",
                description="Nationwide initiative for students to solve pressing real-world problem statements submitted by Central Ministries, State Governments, and Industry leaders.",
                summary="National Hackathon competition with Rs 1 Lakh cash prize per problem statement.",
                source_url=source_url,
                application_url="https://sih.gov.in",
                fee="Nil",
                eligibility=[
                    "B.Tech / M.Tech / MCA / Diploma Students of AICTE / UGC approved Institutions",
                    "Team size of 6 students (minimum 1 female member required)",
                ],
            )
        ]
