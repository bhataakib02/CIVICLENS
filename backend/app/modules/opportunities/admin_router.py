"""FastAPI router for Admin Opportunity Source and Crawler Management (prompt §37, §38, §39, §49)."""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import db_session
from app.models.user import User
from app.models.opportunity import Opportunity, OpportunityLink, CrawlRun
from app.modules.auth.dependencies import require_admin
from app.modules.opportunities.service import OpportunityService
from app.modules.opportunities.schemas import (
    OpportunitySourceCreate,
    OpportunitySourceResponse,
    OpportunitySourceUpdate,
)

admin_opportunities_router = APIRouter(prefix="/admin", tags=["admin-opportunities"])


@admin_opportunities_router.get("/opportunity-sources", response_model=List[OpportunitySourceResponse])
def list_admin_sources(
    current_admin: User = Depends(require_admin),
    db: Session = Depends(db_session),
) -> List[OpportunitySourceResponse]:
    """Admin: List all opportunity sources with health and crawl status."""
    service = OpportunityService(db)
    return service.list_sources()


@admin_opportunities_router.post("/opportunity-sources/validate")
def validate_admin_source(
    url: str = Query(..., description="Target candidate source URL"),
    domain: Optional[str] = Query(None, description="Optional target domain"),
    current_admin: User = Depends(require_admin),
) -> Dict[str, Any]:
    """Admin: Run pre-enablement validation checks (DNS, HTTPS, robots.txt, connector test)."""
    from app.modules.opportunities.ingestion.validator import SourceValidator
    validator = SourceValidator()
    res = validator.validate_source(url, domain=domain)
    return res.__dict__


@admin_opportunities_router.post("/opportunity-sources", response_model=OpportunitySourceResponse, status_code=status.HTTP_201_CREATED)
def create_admin_source(
    data: OpportunitySourceCreate,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(db_session),
) -> OpportunitySourceResponse:
    """Admin: Register a new authoritative opportunity source."""
    service = OpportunityService(db)
    return service.create_source(data)


@admin_opportunities_router.patch("/opportunity-sources/{source_id}", response_model=OpportunitySourceResponse)
def update_admin_source(
    source_id: uuid.UUID,
    data: OpportunitySourceUpdate,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(db_session),
) -> OpportunitySourceResponse:
    """Admin: Update source configuration, authority level, or crawl frequency."""
    service = OpportunityService(db)
    updated = service.repo.update_source(source_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Source not found")
    return OpportunitySourceResponse.model_validate(updated)


@admin_opportunities_router.post("/opportunity-sources/{source_id}/crawl")
def trigger_manual_crawl(
    source_id: uuid.UUID,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(db_session),
) -> Dict[str, Any]:
    """Admin: Trigger an immediate manual crawl for a source."""
    service = OpportunityService(db)
    return service.crawl_source(source_id)


@admin_opportunities_router.get("/crawl-runs")
def list_crawl_runs(
    source_id: Optional[uuid.UUID] = Query(None, description="Optional filter by source"),
    current_admin: User = Depends(require_admin),
    db: Session = Depends(db_session),
) -> List[Dict[str, Any]]:
    """Admin: Get crawl run logs and metrics history."""
    service = OpportunityService(db)
    return service.list_crawl_runs(source_id=source_id)


@admin_opportunities_router.get("/opportunity-quality")
def get_opportunity_quality_review_queue(
    current_admin: User = Depends(require_admin),
    db: Session = Depends(db_session),
) -> List[Dict[str, Any]]:
    """Admin: Review queue for medium and low confidence extracted opportunities."""
    from sqlalchemy import or_, and_
    high_impact = or_(
        Opportunity.source_type == "OFFICIAL",
        Opportunity.type == OpportunityType.GOVERNMENT_SCHEME,
    )
    review_filter = or_(
        and_(high_impact, Opportunity.quality_score < 0.85),
        and_(~high_impact, Opportunity.quality_score < 0.75),
    )
    opps = db.query(Opportunity).filter(review_filter).all()
    return [
        {
            "id": str(o.id),
            "title": o.title,
            "organization": o.organization,
            "quality_score": o.quality_score,
            "extraction_confidence": o.extraction_confidence,
            "source_name": o.source_name,
            "source_url": o.source_url,
            "created_at": o.created_at.isoformat() if o.created_at else None,
        }
        for o in opps
    ]


@admin_opportunities_router.get("/broken-links")
def get_broken_links_report(
    current_admin: User = Depends(require_admin),
    db: Session = Depends(db_session),
) -> List[Dict[str, Any]]:
    """Admin: Monitor invalid and broken application links."""
    links = db.query(OpportunityLink).filter(OpportunityLink.is_valid == False).all()
    return [
        {
            "id": str(l.id),
            "opportunity_id": str(l.opportunity_id),
            "url": l.url,
            "domain": l.domain,
            "http_status": l.http_status,
            "verified_at": l.verified_at.isoformat() if l.verified_at else None,
        }
        for l in links
    ]


@admin_opportunities_router.get("/metrics/crawl-runs")
@admin_opportunities_router.get("/opportunity-sources/metrics/crawl-runs")
def get_crawl_metrics(
    current_admin: User = Depends(require_admin),
    db: Session = Depends(db_session),
) -> Dict[str, Any]:
    """Admin: Get crawl runs observability metrics and quality summary."""
    service = OpportunityService(db)
    total_sources, verified_sources, last_crawl, last_verify = service.repo.get_source_counts()
    broken_links = db.query(OpportunityLink).filter(OpportunityLink.is_valid == False).count()
    from sqlalchemy import or_, and_
    high_impact = or_(
        Opportunity.source_type == "OFFICIAL",
        Opportunity.type == OpportunityType.GOVERNMENT_SCHEME,
    )
    review_filter = or_(
        and_(high_impact, Opportunity.quality_score < 0.85),
        and_(~high_impact, Opportunity.quality_score < 0.75),
    )
    review_queue = db.query(Opportunity).filter(review_filter).count()

    total_runs = db.query(CrawlRun).count()
    completed_runs = db.query(CrawlRun).filter(CrawlRun.status == "COMPLETED").count()
    success_rate = (completed_runs / total_runs) if total_runs > 0 else 1.0

    return {
        "active_sources": total_sources,
        "verified_sources": verified_sources,
        "last_crawl_time": last_crawl,
        "last_verification_time": last_verify,
        "crawl_success_rate": round(success_rate, 2),
        "broken_links_count": broken_links,
        "review_queue_count": review_queue,
    }
