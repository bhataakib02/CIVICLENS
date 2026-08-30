"""Source-specific adapter for UPSC recruitment advertisements and notices (prompt Phase 7)."""
from __future__ import annotations

import re
from typing import List

from app.modules.opportunities.ingestion.adapters.base import BaseSourceAdapter
from app.modules.opportunities.ingestion.extractor import OpportunityExtractionSchema, sanitize_external_text


class UPSCAdapter(BaseSourceAdapter):
    """Specialized parser for Union Public Service Commission portal pages."""

    def parse_opportunities(self, raw_content: str, source_url: str) -> List[OpportunityExtractionSchema]:
        clean = sanitize_external_text(raw_content)

        # Look for recruitment advertisement patterns
        advt_matches = re.findall(
            r"(?i)(?:Advertisement\s+No\.?\s*([0-9/\-]+)|Exam(?:ination)?\s+Notice\s+No\.?\s*([0-9/\-]+))[:\s\n]*([^\n\.]+)",
            clean,
        )

        schemas = []
        if advt_matches:
            for match in advt_matches[:5]:
                advt_no = match[0] or match[1]
                title = f"UPSC Recruitment Advt {advt_no}: {match[2].strip()}"
                schemas.append(
                    OpportunityExtractionSchema(
                        title=title[:255],
                        organization="Union Public Service Commission (UPSC)",
                        type="JOB",
                        description=f"Official UPSC Examination and Recruitment Advertisement {advt_no}. {clean[:1000]}",
                        summary=f"UPSC Civil Services / Public Post Recruitment Notice {advt_no}",
                        source_url=source_url,
                        application_url=f"https://upsconline.nic.in/app/{advt_no}",
                        eligibility=["Graduate Degree from recognized University", "Age per official UPSC notice"],
                    )
                )

        if not schemas:
            # Fallback single document schema
            schemas.append(
                OpportunityExtractionSchema(
                    title="UPSC Examination and Recruitment Notice 2026",
                    organization="Union Public Service Commission (UPSC)",
                    type="JOB",
                    description=clean[:5000],
                    summary="Official UPSC Recruitment and Exam Notification",
                    source_url=source_url,
                    application_url="https://upsconline.nic.in",
                    eligibility=["Graduate Degree from recognized University"],
                )
            )

        return schemas
