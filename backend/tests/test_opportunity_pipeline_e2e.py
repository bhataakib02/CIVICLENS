"""End-to-end integration test for the full Opportunity Intelligence Pipeline (Section 15).

Exercises the full chain:
Source Registration -> Scheduler Execution -> Raw Content Snapshot Persistence ->
Extraction -> Validation -> Normalization -> Deduplication -> Tiered Quality Scoring ->
Outbox Event Emission -> Database Persistence -> Natural Language Search ->
Matching Engine Scoring -> Notification Deduplication.
"""
from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

from app.models.enums import OpportunityAuthorityLevel, OpportunityType, DomainEventType
from app.models.opportunity import Opportunity, RawCrawlSnapshot, OpportunityAlert
from app.modules.opportunities.repository import OpportunityRepository
from app.modules.opportunities.schemas import OpportunitySourceCreate
from app.modules.opportunities.service import OpportunityService
from app.modules.opportunities.matching_engine import OpportunityMatchingEngine
from app.modules.opportunities.search_engine import NaturalLanguageSearchParser
from app.models.citizen_profile import CitizenProfile
from app.models.notification import OutboxEvent


def test_full_opportunity_end_to_end_pipeline(db_session_factory):
    session = db_session_factory()
    try:
        repo = OpportunityRepository(session)
        service = OpportunityService(session)

        # 1. Register Source
        source = repo.create_source(
            OpportunitySourceCreate(
                name="National Career Service E2E Portal",
                domain="ncs.gov.in",
                base_url="https://ncs.gov.in/e2e-jobs",
                authority_level=OpportunityAuthorityLevel.OFFICIAL.value,
                crawl_frequency="30_minutes",
                enabled=True,
            )
        )
        assert source.id is not None
        assert source.authority_level == OpportunityAuthorityLevel.OFFICIAL

        # Mock HTMLConnector fetch_items to return real document
        mock_html = """
        <html>
            <body>
                <h1>Recruitment: Software Engineer Vacancy 2026</h1>
                <p>Organization: National Informatics Centre (NIC)</p>
                <p>Description: Development of public software systems and citizen portals.</p>
                <p>Deadline: 2026-10-31</p>
                <a href="https://ncs.gov.in/apply/software-engineer">Apply Now</a>
            </body>
        </html>
        """

        mock_doc = MagicMock()
        mock_doc.url = "https://ncs.gov.in/e2e-jobs/notice-01"
        mock_doc.content = mock_html
        mock_doc.content_type = "text/html"
        mock_doc.source_identifier = "NIC-SE-2026"

        with patch("app.modules.opportunities.service.HTMLConnector.fetch_items", return_value=[mock_doc]):
            # 2. Run crawl for source
            crawl_res = service.crawl_source(source.id)
            assert crawl_res["status"] == "COMPLETED"
            assert crawl_res["discovered"] == 1

        # 3. Verify Raw Content Snapshot stored (Section 2)
        snapshot = session.query(RawCrawlSnapshot).filter(RawCrawlSnapshot.source_id == source.id).first()
        assert snapshot is not None
        assert snapshot.content_type == "text/html"
        assert "Software Engineer" in snapshot.raw_content
        assert snapshot.expires_at is not None

        # 4. Verify Opportunity persisted in DB with quality score and canonical status
        opp = session.query(Opportunity).filter(Opportunity.source_id == source.id).first()
        assert opp is not None
        assert "National Informatics Centre" in opp.organization
        assert opp.quality_score >= 0.85  # Stricter official threshold
        assert opp.is_canonical is True


        # 5. Verify Outbox Domain Event emitted (Section 4)
        outbox = session.query(OutboxEvent).filter(OutboxEvent.aggregate_id == opp.id).first()
        assert outbox is not None
        assert outbox.event_type == DomainEventType.OPPORTUNITY_PUBLISHED.value

        # 6. Verify Natural Language Search translation (Section 25)
        parser = NaturalLanguageSearchParser()
        parsed_filter = parser.parse("software engineer jobs in Delhi closing this month")
        assert parsed_filter.type == OpportunityType.JOB
        assert parsed_filter.closing_soon is True

        # 7. Verify Transparent Matching Engine Scoring (Section 26, 27)
        matching_engine = OpportunityMatchingEngine()
        mock_profile = MagicMock()
        mock_profile.highest_qualification = "Graduate B.Tech"
        mock_profile.skills = ["Python", "Software Engineering"]
        mock_profile.age = 25
        mock_profile.addresses = []
        breakdown = matching_engine.match(opp, mock_profile)
        assert breakdown.overall_score > 0.0
        assert len(breakdown.reasons) > 0

        # 8. Verify Notification Deduplication against real User model (Section 1 & 5)
        from app.models.user import User
        from app.models.enums import UserRole, UserStatus
        test_user = User(
            email="e2ecitizen@civiclens.gov.in",
            password_hash="secretpasswordhash",
            role=UserRole.CITIZEN,
            status=UserStatus.ACTIVE,
        )
        session.add(test_user)
        session.commit()


        is_dup_1 = repo.is_alert_duplicate(test_user.id, opp.id, "NEW_MATCH", version=1)
        assert is_dup_1 is False

        # Record first alert
        repo.record_alert(test_user.id, opp.id, "NEW_MATCH", "New Software Engineer opportunity published", version=1)

        # Second alert attempt must be detected as duplicate
        is_dup_2 = repo.is_alert_duplicate(test_user.id, opp.id, "NEW_MATCH", version=1)
        assert is_dup_2 is True


    finally:
        session.close()
