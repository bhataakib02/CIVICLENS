"""FastAPI router for Citizen Opportunity Discovery APIs (prompt §49)."""
from __future__ import annotations

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import db_session
from app.models.user import User
from app.models.enums import OpportunityType
from app.modules.auth.dependencies import get_current_user, get_optional_current_user
from app.modules.citizens.repository import CitizensRepository
from app.modules.opportunities.service import OpportunityService
from app.modules.opportunities.schemas import (
    ApplicationTrackCreate,
    ApplicationTrackResponse,
    OpportunityListResponse,
    OpportunityResponse,
    OpportunitySourceResponse,
    OpportunitySubscriptionCreate,
    OpportunitySubscriptionResponse,
)

opportunities_router = APIRouter(prefix="/opportunities", tags=["opportunities"])


@opportunities_router.get("", response_model=OpportunityListResponse)
def list_opportunities(
    query: Optional[str] = Query(None, description="Keyword query"),
    type: Optional[OpportunityType] = Query(None, description="Opportunity type filter"),
    location: Optional[str] = Query(None, description="Location filter"),
    remote: Optional[bool] = Query(None, description="Remote opportunities only"),
    closing_soon: Optional[bool] = Query(None, description="Closing soon filter"),
    is_government: Optional[bool] = Query(None, description="Government vs private filter"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(db_session),
) -> OpportunityListResponse:
    """Discover unified opportunities across government & private sources with personalization."""
    service = OpportunityService(db)
    profile = None
    if current_user:
        profile = CitizensRepository(db).get_profile_by_user_id(current_user.id)
    return service.list_opportunities(
        query=query,
        opp_type=type,
        location=location,
        remote=remote,
        closing_soon=closing_soon,
        is_government=is_government,
        page=page,
        page_size=page_size,
        profile=profile,
    )


@opportunities_router.get("/search", response_model=OpportunityListResponse)
def search_opportunities_natural_language(
    q: str = Query(..., description="Natural language search query"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(db_session),
) -> OpportunityListResponse:
    """Natural language search for opportunities (e.g. 'Find software internships in Bangalore for final year students')."""
    service = OpportunityService(db)
    profile = None
    if current_user:
        profile = CitizensRepository(db).get_profile_by_user_id(current_user.id)
    return service.search_natural_language(nl_query=q, page=page, page_size=page_size, profile=profile)


@opportunities_router.get("/recommended", response_model=List[OpportunityResponse])
def get_recommended_opportunities(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(db_session),
) -> List[OpportunityResponse]:
    """Personalized opportunity recommendations based on citizen profile."""
    profile = CitizensRepository(db).get_profile_by_user_id(current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="Citizen profile required for recommendations.")
    service = OpportunityService(db)
    return service.get_recommended(profile=profile, limit=limit)


@opportunities_router.get("/categories")
def list_categories() -> dict:
    """Available categories and opportunity types metadata."""
    return {
        "types": [t.value for t in OpportunityType],
        "categories": ["Technology", "Engineering", "Finance", "Healthcare", "Education", "Public Sector", "Research"],
    }


@opportunities_router.get("/sources", response_model=List[OpportunitySourceResponse])
def list_public_sources(db: Session = Depends(db_session)) -> List[OpportunitySourceResponse]:
    """List registered authoritative opportunity sources."""
    service = OpportunityService(db)
    return service.list_sources()


@opportunities_router.get("/{opportunity_id}", response_model=OpportunityResponse)
def get_opportunity_detail(
    opportunity_id: uuid.UUID,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(db_session),
) -> OpportunityResponse:
    """Get single opportunity detail with match breakdown and links."""
    service = OpportunityService(db)
    profile = None
    if current_user:
        profile = CitizensRepository(db).get_profile_by_user_id(current_user.id)
    opp = service.get_opportunity(opportunity_id, profile=profile)
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return opp


@opportunities_router.get("/{opportunity_id}/versions")
def get_opportunity_versions(
    opportunity_id: uuid.UUID,
    db: Session = Depends(db_session),
) -> List[dict]:
    """Get version history diff records for an opportunity."""
    service = OpportunityService(db)
    return service.get_opportunity_versions(opportunity_id)


@opportunities_router.get("/{opportunity_id}/links")
def get_opportunity_links(
    opportunity_id: uuid.UUID,
    db: Session = Depends(db_session),
) -> List[dict]:
    """Get extracted link provenance and verification status."""
    service = OpportunityService(db)
    return service.get_opportunity_links(opportunity_id)


@opportunities_router.post("/subscriptions", response_model=OpportunitySubscriptionResponse, status_code=status.HTTP_201_CREATED)
def create_subscription(
    data: OpportunitySubscriptionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(db_session),
) -> OpportunitySubscriptionResponse:
    """Subscribe to opportunity deadline & match alerts."""
    service = OpportunityService(db)
    sub = service.repo.create_subscription(current_user.id, data.keywords, data.types)
    return OpportunitySubscriptionResponse.model_validate(sub)


from fastapi import Response

@opportunities_router.delete("/subscriptions/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subscription(
    subscription_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(db_session),
) -> Response:
    """Delete alert subscription."""
    service = OpportunityService(db)
    success = service.repo.delete_subscription(current_user.id, subscription_id)
    if not success:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@opportunities_router.post("/{opportunity_id}/track", response_model=ApplicationTrackResponse)
def track_opportunity_application(
    opportunity_id: uuid.UUID,
    data: ApplicationTrackCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(db_session),
) -> ApplicationTrackResponse:
    """Track citizen external application status."""
    service = OpportunityService(db)
    track = service.repo.track_application(current_user.id, opportunity_id, data.status, data.notes)
    return ApplicationTrackResponse.model_validate(track)
