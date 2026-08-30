"""Quality scoring and auto-publish decision engine (prompt §40, §70, Part XII).

Assigns quality score based on source authority, completeness, link verification, and extraction confidence.
Routes high confidence -> auto publish, medium -> review queue, low -> reject/manual review.
Applies stricter threshold (0.85) for OFFICIAL government and GOVERNMENT_SCHEME opportunities compared to private postings (0.75).
"""
from __future__ import annotations

from typing import Optional, Tuple, Union
from app.models.enums import OpportunityAuthorityLevel, OpportunityType


class QualityScorer:
    """Calculates internal quality score and auto-publish decision for discovered opportunities."""

    @staticmethod
    def calculate_quality_score(
        authority_level: OpportunityAuthorityLevel,
        has_title: bool,
        has_org: bool,
        has_deadline: bool,
        has_eligibility: bool,
        has_application_url: bool,
        extraction_confidence: float = 1.0,
        opp_type: Optional[Union[OpportunityType, str]] = None,
    ) -> Tuple[float, str]:
        score = 0.0

        # Authority weight (max 0.35)
        if authority_level == OpportunityAuthorityLevel.OFFICIAL:
            score += 0.35
        elif authority_level == OpportunityAuthorityLevel.VERIFIED_PARTNER:
            score += 0.30
        elif authority_level == OpportunityAuthorityLevel.KNOWN_PRIVATE:
            score += 0.25
        else:
            score += 0.10

        # Completeness weight (max 0.40)
        if has_title and has_org:
            score += 0.15
        if has_deadline:
            score += 0.10
        if has_eligibility:
            score += 0.08
        if has_application_url:
            score += 0.07

        # Confidence weight (max 0.25)
        score += min(extraction_confidence, 1.0) * 0.25

        score = round(min(score, 1.0), 2)

        # Tiered publish threshold: OFFICIAL sources or GOVERNMENT_SCHEME require stricter 0.85 cutoff
        type_str = opp_type.value if isinstance(opp_type, OpportunityType) else str(opp_type or "")
        is_high_impact = (
            authority_level == OpportunityAuthorityLevel.OFFICIAL
            or type_str == "GOVERNMENT_SCHEME"
        )
        publish_threshold = 0.85 if is_high_impact else 0.75

        if score >= publish_threshold:
            decision = "AUTO_PUBLISH"
        elif score >= 0.50:
            decision = "REVIEW_QUEUE"
        else:
            decision = "REJECT"

        return score, decision

