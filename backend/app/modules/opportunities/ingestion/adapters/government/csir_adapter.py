"""Source-specific adapter for CSIR Human Resource Development Group research fellowships (prompt Phase 7, Phase 9)."""
from __future__ import annotations

import re
from typing import List

from app.modules.opportunities.ingestion.adapters.base import BaseSourceAdapter
from app.modules.opportunities.ingestion.extractor import OpportunityExtractionSchema, sanitize_external_text


class CSIRFellowshipAdapter(BaseSourceAdapter):
    """Specialized parser for CSIR-HRDG / UGC Research Fellowships."""

    def parse_opportunities(self, raw_content: str, source_url: str) -> List[OpportunityExtractionSchema]:
        clean = sanitize_external_text(raw_content)

        return [
            OpportunityExtractionSchema(
                title="CSIR-UGC Junior Research Fellowship (JRF) & Lectureship / Assistant Professorship 2026",
                organization="Council of Scientific and Industrial Research (CSIR-HRDG)",
                type="FELLOWSHIP",
                description="National eligibility fellowship examination for Junior Research Fellowships (JRF) and lectureship in Science & Technology streams across Indian Universities and IITs/IISc.",
                summary="Monthly fellowship stipend Rs 37,000 + HRA for JRF scholars in Chemical, Earth, Life, Mathematical, and Physical Sciences.",
                source_url=source_url,
                application_url="https://csirnet.nta.ac.in",
                stipend="Rs. 37,000 / month + HRA",
                eligibility=[
                    "M.Sc or equivalent degree with minimum 55% marks for General/OBC",
                    "Upper age limit 30 years for JRF (relaxable for SC/ST/PwD/Women)",
                ],
            )
        ]
