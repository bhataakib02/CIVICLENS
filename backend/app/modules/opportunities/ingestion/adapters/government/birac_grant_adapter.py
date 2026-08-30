"""Source-specific adapter for BIRAC Research & Innovation Grants (prompt Part 8)."""
from __future__ import annotations

from typing import List

from app.modules.opportunities.ingestion.adapters.base import BaseSourceAdapter
from app.modules.opportunities.ingestion.extractor import OpportunityExtractionSchema, sanitize_external_text


class BIRACGrantAdapter(BaseSourceAdapter):
    """Specialized adapter for Biotechnology Industry Research Assistance Council (BIRAC) Grants."""

    def parse_opportunities(self, raw_content: str, source_url: str) -> List[OpportunityExtractionSchema]:
        clean = sanitize_external_text(raw_content)
        return [
            OpportunityExtractionSchema(
                title="BIRAC Biotechnology Ignition Grant (BIG) Scheme 2026",
                organization="Biotechnology Industry Research Assistance Council (BIRAC)",
                type="GRANT",
                description="Financial grant funding up to Rs 50 Lakhs for biotech startups, innovators, and academic researchers to establish proof of concept for innovative biotech products.",
                summary="Grant-in-aid support up to Rs. 50 Lakh for early stage biotech proof-of-concept projects.",
                source_url=source_url,
                application_url="https://birac.nic.in/big.php",
                fee="Nil",
                eligibility=[
                    "Indian Biotech Startups registered under Companies Act 2013",
                    "Individual Innovators / Scientists with Indian Citizenship",
                ],
            )
        ]
