"""Unit tests for specialized source adapters (prompt Phase 7, Phase 18)."""
from __future__ import annotations

import pytest

from app.modules.opportunities.ingestion.adapters.government.upsc_adapter import UPSCAdapter
from app.modules.opportunities.ingestion.adapters.government.csir_adapter import CSIRFellowshipAdapter
from app.modules.opportunities.ingestion.adapters.registry import get_adapter_for_domain


def test_adapter_registry_lookup():
    adapter_upsc = get_adapter_for_domain("upsc.gov.in")
    assert adapter_upsc is not None
    assert isinstance(adapter_upsc, UPSCAdapter)

    adapter_csir = get_adapter_for_domain("csirhrdg.res.in")
    assert adapter_csir is not None
    assert isinstance(adapter_csir, CSIRFellowshipAdapter)

    assert get_adapter_for_domain("unknown.com") is None


def test_csir_fellowship_adapter_extraction():
    adapter = CSIRFellowshipAdapter()
    html = "<html><body>CSIR JRF Fellowships 2026</body></html>"
    schemas = adapter.parse_opportunities(html, "https://csirhrdg.res.in/fellowships")
    assert len(schemas) == 1
    opp = schemas[0]
    assert opp.type == "FELLOWSHIP"
    assert "Junior Research Fellowship" in opp.title
    assert "CSIR" in opp.organization
