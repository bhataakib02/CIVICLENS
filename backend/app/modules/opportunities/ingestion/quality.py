"""Quality scoring and auto-publish decision engine (prompt §40, §70).

Assigns quality score based on source authority, completeness, link verification, and extraction confidence.
Routes high confidence -> auto publish, medium -> review queue, low -> reject/manual review.
"""
from __future__ import annotations

from typing import Tuple
from app.models.enums import OpportunityAuthorityLevel


class QualityScorer:
    """Calculates internal quality score for discovered opportunities."""

    @staticmethod
    def calculate_quality_score(
        authority_level: OpportunityAuthorityLevel,
        has_title: bool,
        has_org: bool,
        has_deadline: bool,
        has_eligibility: bool,
        has_application_url: bool,
        extraction_confidence: float = 1.0,
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

        if score >= 0.75:
            decision = "AUTO_PUBLISH"
        elif score >= 0.50:
            decision = "REVIEW_QUEUE"
        else:
            decision = "REJECT"

        return score, decision
