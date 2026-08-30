"""Service layer orchestrating Opportunity Engine features."""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.opportunity import Opportunity, OpportunitySource
from app.models.citizen_profile import CitizenProfile
from app.models.enums import OpportunityDeadlineStatus, OpportunityType
from app.modules.opportunities.repository import OpportunityRepository
from app.modules.opportunities.matching_engine import OpportunityMatchingEngine, MatchBreakdown
from app.modules.opportunities.search_engine import NaturalLanguageSearchParser, OpportunitySearchFilter
from app.modules.opportunities.schemas import (
    OpportunityCreate,
    OpportunityListResponse,
    OpportunityResponse,
    OpportunitySourceCreate,
    OpportunitySourceResponse,
    OpportunitySourceUpdate,
)
from app.modules.opportunities.ingestion.extractor import OpportunityExtractor
from app.modules.opportunities.ingestion.date_extractor import DateClassifier
from app.modules.opportunities.ingestion.link_validator import LinkValidator
from app.modules.opportunities.ingestion.deduplicator import compute_content_hash, DeduplicationEngine
from app.modules.opportunities.ingestion.quality import QualityScorer
from app.modules.opportunities.ingestion.connectors.base import HTMLConnector, RSSConnector, JSONConnector


class OpportunityService:
    """Service layer for opportunities discovery engine."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.repo = OpportunityRepository(session)
        self.matching_engine = OpportunityMatchingEngine()
        self.search_parser = NaturalLanguageSearchParser()

    def list_opportunities(
        self,
        query: Optional[str] = None,
        opp_type: Optional[OpportunityType] = None,
        location: Optional[str] = None,
        remote: Optional[bool] = None,
        closing_soon: Optional[bool] = None,
        is_government: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20,
        profile: Optional[CitizenProfile] = None,
    ) -> OpportunityListResponse:
        items, total = self.repo.list_opportunities(
            query_str=query,
            opp_type=opp_type,
            location=location,
            remote=remote,
            closing_soon=closing_soon,
            is_government=is_government,
            page=page,
            page_size=page_size,
        )

        resp_items = []
        for opp in items:
            opp_resp = OpportunityResponse.model_validate(opp)
            if profile:
                breakdown = self.matching_engine.match(opp, profile)
                opp_resp.match_breakdown = breakdown.__dict__
            resp_items.append(opp_resp)

        total_sources, verified_sources, last_crawl, last_verify = self.repo.get_source_counts()

        return OpportunityListResponse(
            items=resp_items,
            total=total,
            page=page,
            page_size=page_size,
            indexed_sources=total_sources,
            verified_sources=verified_sources,
            last_crawl_time=last_crawl,
            last_verification_time=last_verify,
        )

    def search_natural_language(
        self,
        nl_query: str,
        page: int = 1,
        page_size: int = 20,
        profile: Optional[CitizenProfile] = None,
    ) -> OpportunityListResponse:
        parsed_filter = self.search_parser.parse(nl_query)
        items, total = self.repo.list_opportunities(
            query_str=parsed_filter.query,
            opp_type=parsed_filter.type,
            location=parsed_filter.location,
            remote=parsed_filter.remote,
            closing_soon=parsed_filter.closing_soon,
            is_government=parsed_filter.is_government,
            page=page,
            page_size=page_size,
        )

        resp_items = []
        for opp in items:
            opp_resp = OpportunityResponse.model_validate(opp)
            if profile:
                breakdown = self.matching_engine.match(opp, profile)
                opp_resp.match_breakdown = breakdown.__dict__
            resp_items.append(opp_resp)

        total_sources, verified_sources, last_crawl, last_verify = self.repo.get_source_counts()

        return OpportunityListResponse(
            items=resp_items,
            total=total,
            page=page,
            page_size=page_size,
            indexed_sources=total_sources,
            verified_sources=verified_sources,
            last_crawl_time=last_crawl,
            last_verification_time=last_verify,
        )

    def get_opportunity(self, opp_id: uuid.UUID, profile: Optional[CitizenProfile] = None) -> Optional[OpportunityResponse]:
        opp = self.repo.get_opportunity(opp_id)
        if not opp:
            return None
        opp_resp = OpportunityResponse.model_validate(opp)
        if profile:
            breakdown = self.matching_engine.match(opp, profile)
            opp_resp.match_breakdown = breakdown.__dict__
        return opp_resp

    def get_recommended(self, profile: CitizenProfile, limit: int = 10) -> List[OpportunityResponse]:
        items, _ = self.repo.list_opportunities(page=1, page_size=50)
        scored = []
        for opp in items:
            breakdown = self.matching_engine.match(opp, profile)
            opp_resp = OpportunityResponse.model_validate(opp)
            opp_resp.match_breakdown = breakdown.__dict__
            scored.append((breakdown.overall_score, opp_resp))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:limit]]

    def get_opportunity_versions(self, opp_id: uuid.UUID) -> List[dict]:
        versions = self.repo.get_opportunity_versions(opp_id)
        return [
            {
                "id": str(v.id),
                "opportunity_id": str(v.opportunity_id),
                "version_number": v.version_number,
                "payload": v.payload,
                "diff": v.diff,
                "created_at": v.created_at.isoformat() if v.created_at else None,
            }
            for v in versions
        ]

    def get_opportunity_links(self, opp_id: uuid.UUID) -> List[dict]:
        links = self.repo.get_opportunity_links(opp_id)
        return [
            {
                "id": str(l.id),
                "opportunity_id": str(l.opportunity_id),
                "url": l.url,
                "domain": l.domain,
                "link_type": l.link_type.value if hasattr(l.link_type, "value") else str(l.link_type),
                "is_official": l.is_official,
                "is_valid": l.is_valid,
                "http_status": l.http_status,
                "redirect_target": l.redirect_target,
                "verified_at": l.verified_at.isoformat() if l.verified_at else None,
            }
            for l in links
        ]

    def list_crawl_runs(self, source_id: Optional[uuid.UUID] = None) -> List[dict]:
        runs = self.repo.list_crawl_runs(source_id=source_id)
        return [
            {
                "id": str(r.id),
                "source_id": str(r.source_id),
                "status": r.status,
                "pages_fetched": r.pages_fetched,
                "pages_changed": r.pages_changed,
                "opportunities_found": r.opportunities_found,
                "opportunities_updated": r.opportunities_updated,
                "duplicates_detected": r.duplicates_detected,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            }
            for r in runs
        ]

    # --- Source Management & Ingestion Pipeline ---

    def create_source(self, data: OpportunitySourceCreate) -> OpportunitySourceResponse:
        source = self.repo.create_source(data)
        return OpportunitySourceResponse.model_validate(source)

    def list_sources(self) -> List[OpportunitySourceResponse]:
        sources = self.repo.list_sources()
        return [OpportunitySourceResponse.model_validate(s) for s in sources]

    def crawl_source(self, source_id: uuid.UUID) -> Dict[str, Any]:
        import time
        from datetime import datetime, timezone
        from app.models.opportunity import CrawlRun
        from app.core.metrics import metrics
        from app.models.enums import DomainEventType
        from app.modules.notifications.events import AggregateType
        from app.modules.notifications.service import OutboxWriter

        start_time = time.time()
        metrics.incr("opportunity_crawl_runs_total")

        source = self.repo.get_source(source_id)
        if not source:
            metrics.incr("opportunity_crawl_failures_total")
            return {"status": "FAILED", "error": "Source not found"}

        run = CrawlRun(
            source_id=source.id,
            status="RUNNING",
            started_at=datetime.now(timezone.utc),
        )
        self.session.add(run)
        self.session.commit()

        extractor = OpportunityExtractor()
        connector = HTMLConnector()
        dedup_engine = DeduplicationEngine(self.session)
        link_validator = LinkValidator()

        discovered = 0
        updated = 0
        duplicates = 0

        try:
            docs = connector.fetch_items(source.base_url)
            run.pages_fetched = len(docs)

            for doc in docs:
                extracted = extractor.extract(doc.content, doc.url, default_org=source.name)
                content_hash = compute_content_hash(extracted.organization, extracted.title, extracted.application_deadline)

                # Store raw content snapshot with retention policy (prompt amendment §2)
                from datetime import timedelta
                from app.models.opportunity import RawCrawlSnapshot
                snapshot = RawCrawlSnapshot(
                    source_id=source.id,
                    url=doc.url,
                    content_hash=content_hash,
                    content_type=doc.content_type,
                    size_bytes=len(doc.content.encode("utf-8")),
                    raw_content=doc.content[:50000],  # snapshot limit
                    retrieved_at=datetime.now(timezone.utc),
                    expires_at=datetime.now(timezone.utc) + timedelta(days=30),  # 30-day retention
                )
                self.session.add(snapshot)

                existing = dedup_engine.find_duplicate(content_hash, source_identifier=doc.source_identifier)

                if existing:
                    duplicates += 1
                    # Check if canonical upgrade needed
                    if dedup_engine.select_canonical(existing, source.authority_level):
                        existing.is_canonical = True
                        self.session.commit()
                    continue

                opp_type = OpportunityType[extracted.type] if extracted.type in OpportunityType.__members__ else OpportunityType.JOB

                # Calculate tiered quality score (0.85 for official government/scheme vs 0.75 for private)
                score, decision = QualityScorer.calculate_quality_score(
                    authority_level=source.authority_level,
                    has_title=bool(extracted.title),
                    has_org=bool(extracted.organization),
                    has_deadline=bool(extracted.application_deadline),
                    has_eligibility=bool(extracted.eligibility),
                    has_application_url=bool(extracted.application_url),
                    opp_type=opp_type,
                )

                opp_create = OpportunityCreate(
                    type=opp_type,
                    title=extracted.title,
                    organization=extracted.organization,
                    description=extracted.description,
                    summary=extracted.summary,
                    source_url=doc.url,
                    application_url=extracted.application_url or doc.url,
                    source_domain=source.domain,
                    source_name=source.name,
                    source_type=source.source_type.value,
                    source_identifier=doc.source_identifier,
                    source_id=source.id,
                    eligibility=extracted.eligibility,
                    status=OpportunityDeadlineStatus.OPEN if extracted.application_deadline else OpportunityDeadlineStatus.DATE_UNKNOWN,
                )
                opp = self.repo.create_opportunity(opp_create, content_hash)
                opp.quality_score = score
                self.session.commit()
                discovered += 1

                # Enqueue Outbox domain event for realtime fanout if AUTO_PUBLISH
                if decision == "AUTO_PUBLISH":
                    OutboxWriter(self.session).enqueue_simple(
                        event_type=DomainEventType.OPPORTUNITY_PUBLISHED,
                        aggregate_type=AggregateType.OPPORTUNITY,
                        aggregate_id=opp.id,
                        payload={
                            "opportunity_id": str(opp.id),
                            "title": opp.title,
                            "organization": opp.organization,
                            "type": opp.type.value,
                            "source_domain": opp.source_domain,
                            "quality_score": opp.quality_score,
                        },
                    )
                    self.session.commit()

            duration_sec = time.time() - start_time
            run.status = "COMPLETED"
            run.pages_changed = discovered
            run.opportunities_found = discovered
            run.duplicates_detected = duplicates
            run.duration_ms = duration_sec * 1000.0
            run.completed_at = datetime.now(timezone.utc)
            self.session.commit()

            metrics.incr("opportunity_discovered_total", discovered)
            metrics.observe("opportunity_crawl_duration_seconds", duration_sec)

            return {
                "status": "COMPLETED",
                "discovered": discovered,
                "duplicates": duplicates,
                "source": source.name,
            }

        except Exception as exc:
            duration_sec = time.time() - start_time
            run.status = "FAILED"
            run.error_summary = str(exc)[:500]
            run.duration_ms = duration_sec * 1000.0
            run.completed_at = datetime.now(timezone.utc)
            self.session.commit()

            metrics.incr("opportunity_crawl_failures_total")
            metrics.observe("opportunity_crawl_duration_seconds", duration_sec)
            return {"status": "FAILED", "error": str(exc), "source": source.name}


