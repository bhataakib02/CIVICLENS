"""Service layer orchestrating Opportunity Engine features."""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import func
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
from app.modules.opportunities.ingestion.connectors.base import HTMLConnector, RSSConnector, JSONConnector, get_connector_for_source


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
        from datetime import datetime, timezone, timedelta
        from app.models.opportunity import CrawlRun, RawCrawlSnapshot, OpportunityVersion, OpportunityChange
        from app.core.metrics import metrics
        from app.models.enums import DomainEventType
        from app.modules.notifications.events import AggregateType
        from app.modules.notifications.service import OutboxWriter
        from app.modules.opportunities.ingestion.connectors.base import get_connector_for_source
        from app.modules.opportunities.ingestion.robots import RobotsPolicyChecker
        from app.modules.opportunities.ingestion.rate_limiter import DomainRateLimiter

        start_time = time.time()
        metrics.incr("opportunity_crawl_runs_total")

        source = self.repo.get_source(source_id)
        if not source:
            metrics.incr("opportunity_crawl_failures_total")
            return {"status": "FAILED", "error": "Source not found"}

        now_utc = datetime.now(timezone.utc)
        source.last_crawl_started_at = now_utc

        run = CrawlRun(
            source_id=source.id,
            status="RUNNING",
            started_at=now_utc,
        )
        self.session.add(run)
        self.session.commit()

        # Enforce rate limits & robots.txt compliance (prompt §8, §9)
        DomainRateLimiter().acquire(source.domain)
        robots_checker = RobotsPolicyChecker()
        if not robots_checker.is_allowed(source.base_url):
            run.status = "FAILED"
            run.error_summary = "Disallowed by robots.txt policy"
            run.completed_at = datetime.now(timezone.utc)

            source.health_status = "BLOCKED"
            source.consecutive_failures = (source.consecutive_failures or 0) + 1
            source.last_error = "Disallowed by robots.txt policy"
            source.last_error_at = datetime.now(timezone.utc)
            source.last_failed_at = datetime.now(timezone.utc)
            self.session.commit()

            metrics.incr("opportunity_crawl_failures_total")
            return {"status": "FAILED", "error": "Disallowed by robots.txt policy", "source": source.name}

        extractor = OpportunityExtractor()
        source_type_str = source.source_type.value if hasattr(source.source_type, "value") else str(source.source_type)
        connector = get_connector_for_source(source.crawl_policy, source_type_str, source.base_url)
        dedup_engine = DeduplicationEngine(self.session)
        link_validator = LinkValidator()

        discovered = 0
        updated = 0
        duplicates = 0

        from app.modules.opportunities.ingestion.adapters.registry import get_adapter_for_domain
        adapter = get_adapter_for_domain(source.domain)

        try:
            docs = connector.fetch_items(source.base_url)
            run.pages_fetched = len(docs)

            for doc in docs:
                # Generic Extraction First (Phase 4 Requirement 3)
                generic_item = extractor.extract(doc.content, doc.url, default_org=source.name)
                extracted_items = []

                if generic_item and generic_item.title and generic_item.title != "Opportunity Notice":
                    extracted_items = [generic_item]
                elif adapter:
                    # Fall back to Source Adapter if generic extraction produced generic placeholder
                    extracted_items = adapter.parse_opportunities(doc.content, doc.url)
                else:
                    extracted_items = [generic_item] if generic_item else []

                for extracted in extracted_items:
                    content_hash = compute_content_hash(extracted.organization, extracted.title, extracted.application_deadline)

                    # Store raw content snapshot with 30-day retention cutoff (prompt §10)
                    clean_content = doc.content.replace("\x00", "")
                    snapshot = RawCrawlSnapshot(
                        source_id=source.id,
                        url=doc.url,
                        content_hash=content_hash,
                        content_type=doc.content_type,
                        size_bytes=len(clean_content.encode("utf-8")),
                        raw_content=clean_content[:50000],  # snapshot limit
                        retrieved_at=datetime.now(timezone.utc),
                        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
                    )
                    self.session.add(snapshot)

                existing = dedup_engine.find_duplicate(content_hash, source_identifier=doc.source_identifier, organization=extracted.organization, title=extracted.title)

                parsed_deadline = DateClassifier.parse_datetime(extracted.application_deadline)
                parsed_open_date = DateClassifier.parse_datetime(extracted.application_open_date)
                parsed_pub_date = DateClassifier.parse_datetime(extracted.published_at)

                if existing:
                    duplicates += 1
                    existing.last_seen_at = datetime.now(timezone.utc)
                    existing.last_verified_at = datetime.now(timezone.utc)

                    # Versioning & Change detection (prompt §21, §53)
                    diffs = {}
                    if parsed_deadline and existing.application_deadline != parsed_deadline:
                        diffs["application_deadline"] = {
                            "old": existing.application_deadline.isoformat() if existing.application_deadline else None,
                            "new": parsed_deadline.isoformat(),
                        }
                        self.session.add(
                            OpportunityChange(
                                opportunity_id=existing.id,
                                change_type="DEADLINE_CHANGED",
                                old_value=existing.application_deadline.isoformat() if existing.application_deadline else None,
                                new_value=parsed_deadline.isoformat(),
                            )
                        )
                        existing.application_deadline = parsed_deadline

                    if extracted.application_url and existing.application_url != extracted.application_url:
                        diffs["application_url"] = {"old": existing.application_url, "new": extracted.application_url}
                        self.session.add(
                            OpportunityChange(
                                opportunity_id=existing.id,
                                change_type="APPLY_LINK_CHANGED",
                                old_value=existing.application_url,
                                new_value=extracted.application_url,
                            )
                        )
                        existing.application_url = extracted.application_url

                    if diffs:
                        updated += 1
                        latest_ver_num = (
                            self.session.query(OpportunityVersion.version_number)
                            .filter(OpportunityVersion.opportunity_id == existing.id)
                            .order_by(OpportunityVersion.version_number.desc())
                            .first()
                        )
                        next_ver = (latest_ver_num[0] + 1) if latest_ver_num else 2
                        self.session.add(
                            OpportunityVersion(
                                opportunity_id=existing.id,
                                version_number=next_ver,
                                payload={"title": existing.title, "organization": existing.organization, "application_deadline": parsed_deadline.isoformat() if parsed_deadline else None},
                                diff=diffs,
                            )
                        )

                    # Canonical authority escalation check
                    if dedup_engine.select_canonical(existing, source.authority_level):
                        existing.is_canonical = True

                    self.session.commit()
                    continue

                opp_type = OpportunityType[extracted.type] if extracted.type in OpportunityType.__members__ else OpportunityType.JOB

                # Validate application link (prompt §18, §52)
                app_link_res = link_validator.validate_link(extracted.application_url or doc.url, source.domain)

                # Calculate tiered quality score (0.85 for official government/scheme vs 0.75 for private)
                score, decision = QualityScorer.calculate_quality_score(
                    authority_level=source.authority_level,
                    has_title=bool(extracted.title),
                    has_org=bool(extracted.organization),
                    has_deadline=bool(extracted.application_deadline),
                    has_eligibility=bool(extracted.eligibility),
                    has_application_url=bool(app_link_res.is_valid),
                    extraction_confidence=1.0,
                    opp_type=opp_type,
                )

                deadline_status = DateClassifier.calculate_status(
                    open_date=parsed_open_date,
                    deadline=parsed_deadline,
                )

                opp_create = OpportunityCreate(
                    type=opp_type,
                    title=extracted.title,
                    organization=extracted.organization,
                    description=extracted.description,
                    summary=extracted.summary,
                    source_url=doc.url,
                    application_url=app_link_res.url,
                    source_domain=source.domain,
                    source_name=source.name,
                    source_type=source.source_type.value if hasattr(source.source_type, "value") else str(source.source_type),
                    source_identifier=doc.source_identifier,
                    source_id=source.id,
                    eligibility=extracted.eligibility,
                    application_open_date=parsed_open_date,
                    application_deadline=parsed_deadline,
                    published_at=parsed_pub_date or datetime.now(timezone.utc),
                    status=deadline_status,
                )
                opp = self.repo.create_opportunity(opp_create, content_hash)
                opp.quality_score = score
                opp.last_seen_at = datetime.now(timezone.utc)
                opp.last_verified_at = datetime.now(timezone.utc)
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
            run.opportunities_updated = updated
            run.duplicates_detected = duplicates
            run.duration_ms = duration_sec * 1000.0
            run.completed_at = datetime.now(timezone.utc)
            # Structure-Change Detection (Phase 4 requirement)
            total_historical_opps = self.session.query(Opportunity).filter(Opportunity.source_id == source.id).count()
            is_structure_collapse = (len(docs) > 0 and discovered == 0 and duplicates == 0 and total_historical_opps > 0)

            if is_structure_collapse:
                run.failure_stage = "PARSER_STRUCTURE_CHANGED"
                source.health_status = "DEGRADED"
                source.last_error = "Structure change detected: extraction yield collapsed from historical baseline"
                logger.warning("structure_change_detected", extra={"source_id": str(source.id), "source_name": source.name})
            else:
                run.failure_stage = "CRAWL_SUCCESS_ZERO_OPPORTUNITIES" if (discovered == 0 and duplicates == 0) else "NONE"
                source.health_status = "HEALTHY"
                source.last_error = None

            # Update Source Health & Quality Metrics (Phase 4 Requirement)
            source.consecutive_failures = 0 if not is_structure_collapse else (source.consecutive_failures + 1)
            source.last_failure_stage = run.failure_stage
            source.last_crawl_completed_at = datetime.now(timezone.utc)
            source.last_crawled_at = datetime.now(timezone.utc)
            source.last_successful_crawl_at = datetime.now(timezone.utc)

            # Calculate Quality & Reliability Profile (Phase 4 Weighted Score)
            recent_runs = self.session.query(CrawlRun).filter(CrawlRun.source_id == source.id).order_by(CrawlRun.started_at.desc()).limit(10).all()
            pages_cnt = max(len(docs), 1)
            source.crawl_success_rate = 1.0 if not is_structure_collapse else 0.5
            source.extraction_success_rate = round(float(discovered + duplicates) / float(pages_cnt), 2)
            
            # Deterministic Reliability Score (Phase 4)
            auth_val = source.authority_level.value if hasattr(source.authority_level, "value") else str(source.authority_level)
            auth_scores = {"OFFICIAL": 1.0, "VERIFIED_PARTNER": 0.85, "KNOWN_PRIVATE": 0.7, "UNVERIFIED": 0.5}
            auth_score = auth_scores.get(auth_val, 0.5)
            crawl_rate = sum(1 for r in recent_runs if r.status == "COMPLETED") / max(len(recent_runs), 1)
            freshness_score = 1.0 if source.last_successful_crawl_at else 0.5
            stability_score = max(1.0 - ((source.consecutive_failures or 0) * 0.2), 0.0)

            rel_score = (
                (0.25 * auth_score) +
                (0.25 * crawl_rate) +
                (0.15 * freshness_score) +
                (0.15 * min(source.extraction_success_rate, 1.0)) +
                (0.10 * (source.link_success_rate or 1.0)) +
                (0.10 * stability_score)
            )
            source.reliability_score = round(rel_score, 2)
            source.overall_quality_score = round(
                (0.4 * auth_score) +
                (0.3 * source.reliability_score) +
                (0.3 * min(source.extraction_success_rate, 1.0)),
                2
            )
            self.session.commit()

            metrics.incr("opportunity_discovered_total", discovered)
            metrics.observe("opportunity_crawl_duration_seconds", duration_sec)

            return {
                "status": "COMPLETED",
                "discovered": discovered,
                "updated": updated,
                "duplicates": duplicates,
                "failure_stage": run.failure_stage,
                "source": source.name,
            }

        except Exception as exc:
            self.session.rollback()
            duration_sec = time.time() - start_time
            now_utc = datetime.now(timezone.utc)

            # Determine failure stage from exception
            exc_str = str(exc).lower()
            if "dns" in exc_str or "getaddrinfo" in exc_str:
                stage = "DNS_FAILED"
            elif "timeout" in exc_str:
                stage = "TIMEOUT"
            elif "robots" in exc_str:
                stage = "ROBOTS_BLOCKED"
            elif "http" in exc_str or "40" in exc_str or "50" in exc_str:
                stage = "HTTP_ERROR"
            elif "extract" in exc_str or "parse" in exc_str:
                stage = "EXTRACTION_FAILED"
            else:
                stage = "HTTP_ERROR"

            # Persist CrawlRun terminal failure status
            run_rec = self.session.query(CrawlRun).filter(CrawlRun.id == run.id).first()
            if run_rec:
                run_rec.status = "FAILED"
                run_rec.completed_at = now_utc
                run_rec.failure_stage = stage
                run_rec.error_summary = str(exc)[:500]
                run_rec.duration_ms = duration_sec * 1000

            source_rec = self.repo.get_source(source_id)
            if source_rec:
                source_rec.consecutive_failures = (source_rec.consecutive_failures or 0) + 1
                source_rec.health_status = "STALE" if source_rec.consecutive_failures >= 3 else "DEGRADED"
                source_rec.last_failure_stage = stage
                source_rec.last_failed_at = now_utc
                source_rec.last_error_at = now_utc
                source_rec.last_error = str(exc)[:500]

            self.session.commit()

            metrics.incr("opportunity_crawl_failures_total")
            metrics.observe("opportunity_crawl_duration_seconds", duration_sec)
            return {"status": "FAILED", "error": str(exc), "failure_stage": stage, "source": source.name if source else "Unknown"}

    def propose_candidate(self, name: str, domain: str, base_url: str, state: str | None = None) -> OpportunitySource:
        """Propose a new candidate source into the DISCOVERED lifecycle state (Phase 3)."""
        from app.models.enums import OpportunitySourceLifecycleState, OpportunitySourceType, OpportunityAuthorityLevel

        source = OpportunitySource(
            name=name,
            domain=domain,
            base_url=base_url,
            state=state,
            source_type=OpportunitySourceType.STATE_GOVERNMENT if state else OpportunitySourceType.PUBLIC_INSTITUTION,
            authority_level=OpportunityAuthorityLevel.UNVERIFIED,
            enabled=False,
            lifecycle_state=OpportunitySourceLifecycleState.DISCOVERED,
            health_status="HEALTHY",
        )
        self.session.add(source)
        self.session.commit()
        self.session.refresh(source)
        return source

    def validate_candidate_source(self, source_id: uuid.UUID) -> Dict[str, Any]:
        """Validate candidate source using SourceValidator, transitioning DISCOVERED -> VALIDATING -> PENDING_REVIEW (Phase 3)."""
        from app.models.enums import OpportunitySourceLifecycleState
        from app.modules.opportunities.ingestion.validator import SourceValidator

        source = self.repo.get_source(source_id)
        if not source:
            raise ValueError("Source not found")

        source.lifecycle_state = OpportunitySourceLifecycleState.VALIDATING
        self.session.commit()

        validator = SourceValidator()
        val_res = validator.validate_source(source.base_url, domain=source.domain)

        is_valid = val_res.dns_valid and val_res.https_valid and val_res.robots_allowed and val_res.sample_pages > 0

        if is_valid:
            source.lifecycle_state = OpportunitySourceLifecycleState.PENDING_REVIEW
        else:
            source.lifecycle_state = OpportunitySourceLifecycleState.FAILED

        self.session.commit()
        return {
            "source_id": str(source.id),
            "lifecycle_state": source.lifecycle_state.value if hasattr(source.lifecycle_state, "value") else str(source.lifecycle_state),
            "validation_details": val_res.__dict__,
        }

    def approve_candidate_source(self, source_id: uuid.UUID) -> OpportunitySource:
        """Explicit admin approval transitioning candidate PENDING_REVIEW -> APPROVED -> ACTIVE (Phase 3)."""
        from app.models.enums import OpportunitySourceLifecycleState

        source = self.repo.get_source(source_id)
        if not source:
            raise ValueError("Source not found")

        if source.lifecycle_state not in (OpportunitySourceLifecycleState.PENDING_REVIEW, OpportunitySourceLifecycleState.APPROVED):
            raise ValueError(f"Source in state '{source.lifecycle_state}' cannot be approved")

        source.lifecycle_state = OpportunitySourceLifecycleState.ACTIVE
        source.enabled = True
        self.session.commit()
        self.session.refresh(source)
        return source

    def discover_source(self, organization: str, domain: str):
        from app.modules.opportunities.ingestion.discovery import SourceDiscoveryAssistant
        assistant = SourceDiscoveryAssistant()
        return assistant.discover(organization, domain)

    def get_coverage_matrix(self):
        from app.modules.opportunities.coverage_matrix import generate_coverage_matrix
        return generate_coverage_matrix(self.session)

    def get_national_dashboard(self):
        from app.models.enums import OpportunityType
        from app.modules.opportunities.coverage_matrix import ALL_STATES

        sources = self.repo.list_sources()

        healthy = sum(1 for s in sources if s.health_status == "HEALTHY")
        degraded = sum(1 for s in sources if s.health_status == "DEGRADED")
        blocked = sum(1 for s in sources if s.health_status == "BLOCKED")
        failed = sum(1 for s in sources if s.health_status == "FAILED")
        stale = sum(1 for s in sources if s.health_status == "STALE")

        states = set(s.state for s in sources if s.state)
        if any(s.state is None for s in sources):
            states.add("CENTRAL")

        opp_types_set = set(t.value for t in OpportunityType)

        opps_by_type = {}
        for t in OpportunityType:
            cnt = self.session.query(Opportunity).filter(Opportunity.type == t).count()
            opps_by_type[t.value] = cnt

        opps_by_state = {}
        sources_by_state = {}
        for s in sources:
            st = s.state or "CENTRAL"
            sources_by_state[st] = sources_by_state.get(st, 0) + 1
            opp_cnt = self.session.query(Opportunity).filter(Opportunity.source_id == s.id).count()
            opps_by_state[st] = opps_by_state.get(st, 0) + opp_cnt

        sources_by_type = {}
        for s in sources:
            types = s.opportunity_types or ["JOB"]
            for t in types:
                sources_by_type[t] = sources_by_type.get(t, 0) + 1

        from app.modules.opportunities.schemas import NationalCoverageDashboardResponse
        return NationalCoverageDashboardResponse(
            total_sources=len(sources),
            healthy_sources=healthy,
            degraded_sources=degraded,
            blocked_sources=blocked,
            failed_sources=failed,
            stale_sources=stale,
            states_covered_count=len(states),
            states_covered=sorted(list(states)),
            opportunity_types_count=len(opp_types_set),
            opportunity_types=sorted(list(opp_types_set)),
            opportunities_by_type=opps_by_type,
            opportunities_by_state=opps_by_state,
            sources_by_state=sources_by_state,
            sources_by_opportunity_type=sources_by_type,
        )

    def get_citizen_coverage(self):
        sources = self.repo.list_sources(enabled_only=True)
        states = set(s.state for s in sources if s.state)
        if any(s.state is None for s in sources):
            states.add("CENTRAL")

        latest_crawl = self.session.query(func.max(OpportunitySource.last_crawled_at)).scalar()

        from app.modules.opportunities.schemas import CitizenCoverageSummaryResponse
        return CitizenCoverageSummaryResponse(
            sources_monitored=len(sources),
            states_covered=len(states),
            last_updated_at=latest_crawl,
        )




