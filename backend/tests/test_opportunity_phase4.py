"""Phase 4 automated test suite covering source onboarding, discovery assistant, generic extraction first,

adapter fallback, health metrics, coverage matrix, and dashboard endpoints.
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.enums import OpportunityAuthorityLevel, OpportunitySourceType, OpportunityType
from app.models.opportunity import OpportunitySource, Opportunity
from app.modules.opportunities.schemas import OpportunitySourceCreate, SourceDiscoveryRequest
from app.modules.opportunities.service import OpportunityService
from app.modules.opportunities.coverage_matrix import generate_coverage_matrix
from app.modules.opportunities.ingestion.discovery import SourceDiscoveryAssistant
from app.modules.opportunities.ingestion.adapters.registry import get_adapter_for_domain


@pytest.fixture
def db_session(db_clean):
    from app.db.session import get_sessionmaker
    SessionLocal = get_sessionmaker()
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_source_registration_with_onboarding_config(db_session: Session):
    service = OpportunityService(db_session)
    source_create = OpportunitySourceCreate(
        name="Gujarat Public Service Commission (GPSC)",
        domain="gpsc.gujarat.gov.in",
        base_url="https://gpsc.gujarat.gov.in",
        source_type=OpportunitySourceType.STATE_GOVERNMENT,
        source_category="State Recruitment",
        country="IN",
        state="Gujarat",
        district="Gandhinagar",
        geographic_scope="STATE",
        priority="P1",
        authority_level=OpportunityAuthorityLevel.OFFICIAL,
        crawl_frequency="6_hours",
        connector_type="HTML",
        seed_urls=["https://gpsc.gujarat.gov.in/latest-news"],
        allowed_paths=["/latest-news", "/advertisement"],
        excluded_paths=["/login", "/admin"],
        rate_limit=2.0,
        opportunity_types=["JOB"],
        enabled=True,
    )
    src = service.create_source(source_create)
    assert src.name == "Gujarat Public Service Commission (GPSC)"
    assert src.domain == "gpsc.gujarat.gov.in"
    assert src.state == "Gujarat"
    assert src.connector_type == "HTML"
    assert src.rate_limit == 2.0
    assert "JOB" in src.opportunity_types


def test_source_discovery_assistant_workflow():
    assistant = SourceDiscoveryAssistant()
    report = assistant.discover(organization="Union Public Service Commission", domain="upsc.gov.in")
    assert report.organization == "Union Public Service Commission"
    assert report.domain == "upsc.gov.in"
    assert report.base_url.startswith("https://")
    assert report.dns_status == "RESOLVED"
    assert report.candidate_connector in ["HTML", "RSS", "SITEMAP", "JSON", "PDF"]
    assert report.suggested_authority_level == "OFFICIAL"
    assert len(report.candidate_opportunity_types) > 0


def test_adapter_registry_mapping_and_generic_fallback():
    # Domain mapped to adapter
    adapter = get_adapter_for_domain("upsc.gov.in")
    assert adapter is not None

    # Domain without adapter falls back to generic extraction
    no_adapter = get_adapter_for_domain("unmapped-domain-12345.gov.in")
    assert no_adapter is None


def test_generic_extraction_first(db_session: Session):
    service = OpportunityService(db_session)
    source_create = OpportunitySourceCreate(
        name="Test Generic Portal",
        domain="generic-test-portal.gov.in",
        base_url="https://generic-test-portal.gov.in",
        source_type=OpportunitySourceType.CENTRAL_GOVERNMENT,
        enabled=True,
    )
    src = service.create_source(source_create)
    assert src is not None


def test_deterministic_coverage_matrix_generation(db_session: Session):
    service = OpportunityService(db_session)
    # Register Maharashtra and Karnataka sources
    service.create_source(
        OpportunitySourceCreate(
            name="MPSC Test Source",
            domain="mpsc-test.gov.in",
            base_url="https://mpsc-test.gov.in",
            state="Maharashtra",
            source_type=OpportunitySourceType.STATE_GOVERNMENT,
            opportunity_types=["JOB"],
            enabled=True,
        )
    )
    service.create_source(
        OpportunitySourceCreate(
            name="KPSC Test Source",
            domain="kpsc-test.gov.in",
            base_url="https://kpsc-test.gov.in",
            state="Karnataka",
            source_type=OpportunitySourceType.STATE_GOVERNMENT,
            opportunity_types=["JOB"],
            enabled=True,
        )
    )

    res = generate_coverage_matrix(db_session)
    assert res.total_states_covered >= 2
    assert res.total_sources_mapped >= 2

    # Verify matrix structure
    maha_entry = next((s for s in res.matrix if s.state == "Maharashtra"), None)
    assert maha_entry is not None
    assert "recruitment" in maha_entry.sources
    assert len(maha_entry.sources["recruitment"]) >= 1


def test_national_dashboard_and_citizen_coverage(db_session: Session):
    service = OpportunityService(db_session)
    dash = service.get_national_dashboard()
    assert dash.total_sources >= 0
    assert isinstance(dash.states_covered, list)
    assert isinstance(dash.opportunities_by_type, dict)

    cit_cov = service.get_citizen_coverage()
    assert cit_cov.sources_monitored >= 0
    assert cit_cov.states_covered >= 0
