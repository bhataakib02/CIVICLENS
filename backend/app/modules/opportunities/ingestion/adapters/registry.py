"""Adapter registry mapping domain names to specialized source adapters (prompt Phase 7)."""
from __future__ import annotations

from typing import Dict, Optional

from app.modules.opportunities.ingestion.adapters.base import BaseSourceAdapter
from app.modules.opportunities.ingestion.adapters.government.upsc_adapter import UPSCAdapter
from app.modules.opportunities.ingestion.adapters.government.csir_adapter import CSIRFellowshipAdapter
from app.modules.opportunities.ingestion.adapters.government.birac_grant_adapter import BIRACGrantAdapter
from app.modules.opportunities.ingestion.adapters.government.pmkvy_skill_adapter import PMKVYSkillAdapter
from app.modules.opportunities.ingestion.adapters.government.sih_competition_adapter import SIHCompetitionAdapter
from app.modules.opportunities.ingestion.adapters.government.nta_admission_adapter import NTAAdmissionAdapter

_ADAPTER_MAP: Dict[str, BaseSourceAdapter] = {
    "upsc.gov.in": UPSCAdapter(),
    "csirhrdg.res.in": CSIRFellowshipAdapter(),
    "csir.res.in": CSIRFellowshipAdapter(),
    "birac.nic.in": BIRACGrantAdapter(),
    "pmkvyofficial.org": PMKVYSkillAdapter(),
    "sih.gov.in": SIHCompetitionAdapter(),
    "nta.ac.in": NTAAdmissionAdapter(),
    "cuet.samarth.ac.in": NTAAdmissionAdapter(),
}


def get_adapter_for_domain(domain: str) -> Optional[BaseSourceAdapter]:
    """Retrieve specialized adapter for a domain if registered, else None."""
    norm_domain = (domain or "").lower().strip()
    if norm_domain in _ADAPTER_MAP:
        return _ADAPTER_MAP[norm_domain]
    for key, adapter in _ADAPTER_MAP.items():
        if norm_domain.endswith("." + key):
            return adapter
    return None
