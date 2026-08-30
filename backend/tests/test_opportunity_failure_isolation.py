"""Integration test for crawler failure isolation (prompt Phase 14, Phase 18)."""
from __future__ import annotations

import pytest
from unittest.mock import patch

from app.models.enums import OpportunityAuthorityLevel, OpportunitySourceType
from app.models.opportunity import OpportunitySource
from app.modules.opportunities.service import OpportunityService


@pytest.mark.usefixtures("db_clean")
def test_failure_isolation_between_sources(pg_database_url):
    from app.db.session import get_sessionmaker
    SessionLocal = get_sessionmaker()
    session = SessionLocal()

    # Create Source A (which will fail/raise) and Source B (which should succeed)
    src_a = OpportunitySource(
        name="Failing Source A",
        domain="failing-a.gov.in",
        base_url="https://failing-a.gov.in",
        source_type=OpportunitySourceType.CENTRAL_GOVERNMENT,
        authority_level=OpportunityAuthorityLevel.OFFICIAL,
        enabled=True,
    )
    src_b = OpportunitySource(
        name="Healthy Source B",
        domain="healthy-b.gov.in",
        base_url="https://healthy-b.gov.in",
        source_type=OpportunitySourceType.CENTRAL_GOVERNMENT,
        authority_level=OpportunityAuthorityLevel.OFFICIAL,
        enabled=True,
    )
    session.add_all([src_a, src_b])
    session.commit()

    service = OpportunityService(session)

    # Crawl failing source A
    with patch("app.modules.opportunities.service.get_connector_for_source") as mock_conn_factory:
        pass  # ensure import path

    with patch("app.modules.opportunities.ingestion.connectors.base.get_connector_for_source") as mock_conn_factory:
        mock_conn_a = mock_conn_factory.return_value
        mock_conn_a.fetch_items.side_effect = RuntimeError("Network timeout on Source A")

        res_a = service.crawl_source(src_a.id)
        assert res_a["status"] == "FAILED"

    # Verify session is clean and Source B can crawl successfully after Source A failure
    session.refresh(src_a)
    assert src_a.consecutive_failures == 1
    assert src_a.health_status in ("DEGRADED", "STALE")

    with patch("app.modules.opportunities.ingestion.connectors.base.get_connector_for_source") as mock_conn_factory:
        mock_conn_b = mock_conn_factory.return_value
        mock_conn_b.fetch_items.return_value = []

        res_b = service.crawl_source(src_b.id)
        assert res_b["status"] == "COMPLETED"

    session.refresh(src_b)
    assert src_b.consecutive_failures == 0
    session.close()
