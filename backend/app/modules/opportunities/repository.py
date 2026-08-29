"""Database repository for Opportunity operations."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy import func, or_, and_, desc
from sqlalchemy.orm import Session, joinedload

from app.models.opportunity import (
    CrawlItem,
    CrawlRun,
    LinkVerification,
    Opportunity,
    OpportunityAlert,
    OpportunityApplicationTrack,
    OpportunityChange,
    OpportunityLink,
    OpportunitySource,
    OpportunitySubscription,
    OpportunityVersion,
)
from app.models.enums import (
    OpportunityApplicationStatus,
    OpportunityAuthorityLevel,
    OpportunityDeadlineStatus,
    OpportunityType,
)
from app.modules.opportunities.schemas import (
    OpportunityCreate,
    OpportunitySourceCreate,
    OpportunitySourceUpdate,
)


class OpportunityRepository:
    """Repository handling persistence for Opportunity discovery engine."""

    def __init__(self, session: Session) -> None:
        self.session = session

    # --- Sources ---

    def create_source(self, data: OpportunitySourceCreate) -> OpportunitySource:
        source = OpportunitySource(**data.model_dump())
        self.session.add(source)
        self.session.commit()
        self.session.refresh(source)
        return source

    def get_source(self, source_id: uuid.UUID) -> Optional[OpportunitySource]:
        return self.session.query(OpportunitySource).filter(OpportunitySource.id == source_id).first()

    def get_source_by_domain(self, domain: str) -> Optional[OpportunitySource]:
        return self.session.query(OpportunitySource).filter(OpportunitySource.domain == domain).first()

    def list_sources(self, enabled_only: bool = False) -> List[OpportunitySource]:
        query = self.session.query(OpportunitySource)
        if enabled_only:
            query = query.filter(OpportunitySource.enabled == True)
        return query.order_by(OpportunitySource.name).all()

    def update_source(self, source_id: uuid.UUID, data: OpportunitySourceUpdate) -> Optional[OpportunitySource]:
        source = self.get_source(source_id)
        if not source:
            return None
        for key, val in data.model_dump(exclude_unset=True).items():
            setattr(source, key, val)
        source.updated_at = datetime.now(timezone.utc)
        self.session.commit()
        self.session.refresh(source)
        return source

    # --- Opportunities ---

    def create_opportunity(self, data: OpportunityCreate, content_hash: str) -> Opportunity:
        opp_dict = data.model_dump()
        opp_dict["content_hash"] = content_hash
        opp = Opportunity(**opp_dict)
        self.session.add(opp)
        self.session.commit()
        self.session.refresh(opp)

        # Create version 1
        v1 = OpportunityVersion(
            opportunity_id=opp.id,
            version_number=1,
            payload=opp_dict,
            diff={"action": "created"},
        )
        self.session.add(v1)

        # Create primary link
        if opp.application_url or opp.source_url:
            url = opp.application_url or opp.source_url
            link = OpportunityLink(
                opportunity_id=opp.id,
                url=url,
                domain=opp.source_domain,
                is_official=True,
                is_valid=True,
            )
            self.session.add(link)

        self.session.commit()
        return opp

    def get_opportunity(self, opp_id: uuid.UUID) -> Optional[Opportunity]:
        return (
            self.session.query(Opportunity)
            .options(joinedload(Opportunity.links), joinedload(Opportunity.source))
            .filter(Opportunity.id == opp_id)
            .first()
        )

    def list_opportunities(
        self,
        query_str: Optional[str] = None,
        opp_type: Optional[OpportunityType] = None,
        types: Optional[List[OpportunityType]] = None,
        location: Optional[str] = None,
        remote: Optional[bool] = None,
        closing_soon: Optional[bool] = None,
        new_today: Optional[bool] = None,
        upcoming: Optional[bool] = None,
        is_government: Optional[bool] = None,
        status: Optional[OpportunityDeadlineStatus] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Opportunity], int]:
        q = self.session.query(Opportunity).filter(Opportunity.is_canonical == True)

        if query_str:
            pattern = f"%{query_str}%"
            q = q.filter(
                or_(
                    Opportunity.title.ilike(pattern),
                    Opportunity.organization.ilike(pattern),
                    Opportunity.description.ilike(pattern),
                    Opportunity.category.ilike(pattern),
                )
            )

        if opp_type:
            q = q.filter(Opportunity.type == opp_type)

        if types:
            q = q.filter(Opportunity.type.in_(types))

        if location:
            q = q.filter(Opportunity.location.ilike(f"%{location}%"))

        if remote is not None:
            q = q.filter(Opportunity.remote == remote)

        if closing_soon:
            q = q.filter(Opportunity.status == OpportunityDeadlineStatus.CLOSING_SOON)

        if status:
            q = q.filter(Opportunity.status == status)

        if is_government is not None:
            if is_government:
                q = q.filter(
                    or_(
                        Opportunity.source_type.ilike("%GOVERNMENT%"),
                        Opportunity.source_type.in_(["CENTRAL_GOVERNMENT", "STATE_GOVERNMENT", "PUBLIC_INSTITUTION", "PSU"]),
                    )
                )
            else:
                q = q.filter(Opportunity.source_type == "PRIVATE_COMPANY")

        total = q.count()
        items = q.order_by(desc(Opportunity.published_at), desc(Opportunity.created_at)).offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def get_source_counts(self) -> Tuple[int, int, Optional[datetime], Optional[datetime]]:
        total_sources = self.session.query(func.count(OpportunitySource.id)).scalar() or 0
        verified_sources = (
            self.session.query(func.count(OpportunitySource.id))
            .filter(OpportunitySource.authority_level.in_([OpportunityAuthorityLevel.OFFICIAL, OpportunityAuthorityLevel.VERIFIED_PARTNER]))
            .scalar()
            or 0
        )
        last_crawl = self.session.query(func.max(OpportunitySource.last_crawled_at)).scalar()
        last_verify = self.session.query(func.max(Opportunity.last_verified_at)).scalar()
        return total_sources, verified_sources, last_crawl, last_verify

    def get_opportunity_versions(self, opp_id: uuid.UUID) -> List[OpportunityVersion]:
        return (
            self.session.query(OpportunityVersion)
            .filter(OpportunityVersion.opportunity_id == opp_id)
            .order_by(desc(OpportunityVersion.version_number))
            .all()
        )

    def get_opportunity_links(self, opp_id: uuid.UUID) -> List[OpportunityLink]:
        return (
            self.session.query(OpportunityLink)
            .filter(OpportunityLink.opportunity_id == opp_id)
            .order_by(desc(OpportunityLink.is_official))
            .all()
        )

    def update_opportunity(self, opp: Opportunity, new_dict: dict, diff: dict) -> Opportunity:
        # Calculate new version number
        max_ver = (
            self.session.query(func.max(OpportunityVersion.version_number))
            .filter(OpportunityVersion.opportunity_id == opp.id)
            .scalar()
            or 1
        )
        new_ver_num = max_ver + 1

        for key, val in new_dict.items():
            if hasattr(opp, key) and val is not None:
                setattr(opp, key, val)
        opp.updated_at = datetime.now(timezone.utc)
        opp.last_verified_at = datetime.now(timezone.utc)

        version = OpportunityVersion(
            opportunity_id=opp.id,
            version_number=new_ver_num,
            payload=new_dict,
            diff=diff,
        )
        self.session.add(version)

        # Log change records if deadline or application_url changed
        if "application_deadline" in diff:
            chg = OpportunityChange(
                opportunity_id=opp.id,
                change_type="DEADLINE_CHANGED",
                old_value=str(diff["application_deadline"].get("old")),
                new_value=str(diff["application_deadline"].get("new")),
            )
            self.session.add(chg)

        if "application_url" in diff:
            chg = OpportunityChange(
                opportunity_id=opp.id,
                change_type="APPLY_LINK_CHANGED",
                old_value=str(diff["application_url"].get("old")),
                new_value=str(diff["application_url"].get("new")),
            )
            self.session.add(chg)

        self.session.commit()
        self.session.refresh(opp)
        return opp

    def list_crawl_runs(self, source_id: Optional[uuid.UUID] = None, limit: int = 50) -> List[CrawlRun]:
        query = self.session.query(CrawlRun)
        if source_id:
            query = query.filter(CrawlRun.source_id == source_id)
        return query.order_by(desc(CrawlRun.started_at)).limit(limit).all()

    # --- Subscriptions & Application Tracking ---

    def create_subscription(self, user_id: uuid.UUID, keywords: List[str], types: List[OpportunityType]) -> OpportunitySubscription:
        sub = OpportunitySubscription(user_id=user_id, keywords=keywords, types=[t.value for t in types])
        self.session.add(sub)
        self.session.commit()
        self.session.refresh(sub)
        return sub

    def delete_subscription(self, user_id: uuid.UUID, sub_id: uuid.UUID) -> bool:
        sub = self.session.query(OpportunitySubscription).filter(and_(OpportunitySubscription.id == sub_id, OpportunitySubscription.user_id == user_id)).first()
        if not sub:
            return False
        self.session.delete(sub)
        self.session.commit()
        return True

    def track_application(self, user_id: uuid.UUID, opp_id: uuid.UUID, status: OpportunityApplicationStatus, notes: Optional[str] = None) -> OpportunityApplicationTrack:
        track = self.session.query(OpportunityApplicationTrack).filter(and_(OpportunityApplicationTrack.user_id == user_id, OpportunityApplicationTrack.opportunity_id == opp_id)).first()
        if track:
            track.status = status
            track.notes = notes
            track.updated_at = datetime.now(timezone.utc)
        else:
            track = OpportunityApplicationTrack(user_id=user_id, opportunity_id=opp_id, status=status, notes=notes)
            self.session.add(track)
        self.session.commit()
        self.session.refresh(track)
        return track

