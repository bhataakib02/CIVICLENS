"""Unit & Integration tests for Phase 3: Failed Source Recovery, Failure Diagnostics, Priority Tiers, and Category Coverage (prompt Part 17)."""
from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

from app.models.enums import OpportunityAuthorityLevel, OpportunitySourceType
from app.models.opportunity import OpportunitySource, CrawlRun
from app.modules.opportunities.service import OpportunityService
from app.modules.knowledge.ingestion.fetcher import SafeFetcher
from app.modules.opportunities.ingestion.validator import SourceValidator


def test_safe_fetcher_urllib_fallback_for_remote_protocol_error():
    """Verify urllib.request fallback handles malformed server headers cleanly (fixing KPSC)."""
    fetcher = SafeFetcher()

    mock_ures = MagicMock()
    mock_ures.__enter__.return_value = mock_ures
    mock_ures.status = 200
    mock_ures.geturl.return_value = "https://kpsc.kar.nic.in"
    mock_ures.read.return_value = b"<html><body>KPSC Recruitment 2026 Notification</body></html>"
    mock_ures.headers = {"Content-Type": "text/html"}

    with patch("httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_client
        mock_client.stream.side_effect = __import__("httpx").RemoteProtocolError("illegal header line")

        with patch("urllib.request.urlopen", return_value=mock_ures):
            res = fetcher._fetch_once("https://kpsc.kar.nic.in", allow_private=False, max_redirects=0)
            assert res.status_code == 200
            assert b"KPSC Recruitment" in res.content


@pytest.mark.usefixtures("db_clean")
def test_failure_stage_diagnostics_and_zero_opportunity_distinction(pg_database_url):
    from app.db.session import get_sessionmaker
    SessionLocal = get_sessionmaker()
    session = SessionLocal()

    src = OpportunitySource(
        name="Test Zero Opportunity Source",
        domain="zero-opps.gov.in",
        base_url="https://zero-opps.gov.in",
        source_type=OpportunitySourceType.CENTRAL_GOVERNMENT,
        authority_level=OpportunityAuthorityLevel.OFFICIAL,
        priority="P0",
        geographic_scope="NATIONAL",
        enabled=True,
    )
    session.add(src)
    session.commit()

    service = OpportunityService(session)

    with patch("app.modules.opportunities.ingestion.connectors.base.get_connector_for_source") as mock_conn_factory:
        mock_conn = mock_conn_factory.return_value
        mock_conn.fetch_items.return_value = []

        res = service.crawl_source(src.id)
        assert res["status"] == "COMPLETED"
        assert res["discovered"] == 0
        assert res["failure_stage"] == "CRAWL_SUCCESS_ZERO_OPPORTUNITIES"

    session.refresh(src)
    assert src.health_status == "HEALTHY"
    assert src.last_failure_stage == "CRAWL_SUCCESS_ZERO_OPPORTUNITIES"
    session.close()


def test_admin_source_validator_phase3_fields():
    validator = SourceValidator()

    mock_doc = MagicMock()
    mock_doc.content = "BIRAC Grant Announcement 2026. Organization: BIRAC."
    mock_doc.url = "https://birac.nic.in/grants"

    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.text = "<html><body><h1>BIRAC Grants</h1></body></html>"
    mock_res.content = b"<html><body><h1>BIRAC Grants</h1></body></html>"

    with patch("socket.gethostbyname", return_value="1.2.3.4"):
        with patch.object(validator.fetcher, "fetch", return_value=mock_res):
            with patch.object(validator.robots_checker, "is_allowed", return_value=True):
                with patch("app.modules.opportunities.ingestion.validator.get_connector_for_source") as mock_conn_factory:
                    mock_conn = mock_conn_factory.return_value
                    mock_conn.fetch_items.return_value = [mock_doc]

                    res = validator.validate_source("https://birac.nic.in/grants")
                    assert res.domain_valid is True
                    assert res.dns_valid is True
                    assert res.https_valid is True
                    assert res.robots_allowed is True
                    assert res.recommended_authority == "OFFICIAL"
                    assert res.health_status == "HEALTHY"
