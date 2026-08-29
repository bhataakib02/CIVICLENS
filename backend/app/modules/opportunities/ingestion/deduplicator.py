"""Deduplication and canonical source selection engine (prompt §25, §71, §72).

Uses deterministic matching (source identifier, org, title, deadline) + content hash.
Prefers official government/university/company sources as canonical over third-party aggregators.
"""
from __future__ import annotations

import hashlib
import re
from typing import Optional, Tuple, List
from sqlalchemy.orm import Session

from app.models.opportunity import Opportunity
from app.models.enums import OpportunityAuthorityLevel


def compute_content_hash(organization: str, title: str, deadline: Optional[str] = None) -> str:
    norm_org = re.sub(r"\W+", "", organization.lower())
    norm_title = re.sub(r"\W+", "", title.lower())
    deadline_str = deadline or ""
    raw = f"{norm_org}:{norm_title}:{deadline_str}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class DeduplicationEngine:
    """Detects duplicates and selects the canonical official source."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def find_duplicate(
        self,
        content_hash: str,
        source_identifier: Optional[str] = None,
        organization: Optional[str] = None,
        title: Optional[str] = None,
    ) -> Optional[Opportunity]:
        """Find existing matching opportunity by hash or source identifier."""
        if source_identifier:
            match = self.session.query(Opportunity).filter(Opportunity.source_identifier == source_identifier).first()
            if match:
                return match

        match = self.session.query(Opportunity).filter(Opportunity.content_hash == content_hash).first()
        if match:
            return match

        if organization and title:
            norm_org = re.sub(r"\W+", "", organization.lower())
            norm_title = re.sub(r"\W+", "", title.lower())
            all_opps = self.session.query(Opportunity).filter(Opportunity.is_canonical == True).all()
            for opp in all_opps:
                if re.sub(r"\W+", "", opp.organization.lower()) == norm_org and re.sub(r"\W+", "", opp.title.lower()) == norm_title:
                    return opp
        return None

    def select_canonical(self, existing: Opportunity, incoming_authority: OpportunityAuthorityLevel) -> bool:
        """Return True if incoming opportunity has higher authority and should become canonical."""
        authority_rank = {
            OpportunityAuthorityLevel.OFFICIAL: 4,
            OpportunityAuthorityLevel.VERIFIED_PARTNER: 3,
            OpportunityAuthorityLevel.KNOWN_PRIVATE: 2,
            OpportunityAuthorityLevel.UNVERIFIED: 1,
        }
        existing_rank = authority_rank.get(existing.source.authority_level if existing.source else OpportunityAuthorityLevel.UNVERIFIED, 1)
        incoming_rank = authority_rank.get(incoming_authority, 1)
        return incoming_rank > existing_rank
