"""Dynamic Source Coverage Matrix Generator (prompt Part 7 & Part 21).

Generates machine-readable coverage matrix from actual DB source registry.
"""
from __future__ import annotations

from typing import Any, Dict, List
from sqlalchemy.orm import Session

from app.models.opportunity import OpportunitySource
from app.modules.opportunities.schemas import SourceCoverageMatrixResponse, StateCategoryCoverage


ALL_STATES = [
    "CENTRAL",
    "Maharashtra",
    "Karnataka",
    "Tamil Nadu",
    "Uttar Pradesh",
    "Bihar",
    "Rajasthan",
    "West Bengal",
    "Gujarat",
    "Kerala",
    "Madhya Pradesh",
    "Telangana",
    "Andhra Pradesh",
    "Odisha",
    "Punjab",
    "Haryana",
    "Assam",
    "Jharkhand",
    "Chhattisgarh",
    "Uttarakhand",
    "Himachal Pradesh",
    "Goa",
    "Delhi",
]


def generate_coverage_matrix(session: Session) -> SourceCoverageMatrixResponse:
    """Generate dynamic machine-readable source coverage matrix from database."""
    sources = session.query(OpportunitySource).filter(OpportunitySource.enabled == True).all()

    matrix_map: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}

    for state in ALL_STATES:
        matrix_map[state] = {
            "recruitment": [],
            "scholarship": [],
            "schemes": [],
            "skill_programs": [],
            "training": [],
            "competition": [],
            "admission": [],
            "apprenticeship": [],
            "fellowship": [],
            "grant": [],
        }

    mapped_count = 0

    for src in sources:
        st = src.state or "CENTRAL"
        if st not in matrix_map:
            matrix_map[st] = {
                "recruitment": [],
                "scholarship": [],
                "schemes": [],
                "skill_programs": [],
                "training": [],
                "competition": [],
                "admission": [],
                "apprenticeship": [],
                "fellowship": [],
                "grant": [],
            }

        src_info = {
            "id": str(src.id),
            "name": src.name,
            "domain": src.domain,
            "base_url": src.base_url,
            "authority_level": src.authority_level.value if hasattr(src.authority_level, "value") else str(src.authority_level),
            "health_status": src.health_status,
            "quality_score": src.overall_quality_score or 1.0,
        }

        # Categorize source into matrix categories based on opportunity_types / domain / category
        types = src.opportunity_types or []
        cat = (src.source_category or "").lower()
        domain = src.domain.lower()

        is_categorized = False

        if "JOB" in types or "recruitment" in cat or "psc" in domain or "ssc" in domain or "upsc" in domain:
            matrix_map[st]["recruitment"].append(src_info)
            is_categorized = True
        if "SCHOLARSHIP" in types or "scholarship" in cat or "scholarship" in domain:
            matrix_map[st]["scholarship"].append(src_info)
            is_categorized = True
        if "GOVERNMENT_SCHEME" in types or "scheme" in cat or "myscheme" in domain or "yojana" in domain:
            matrix_map[st]["schemes"].append(src_info)
            is_categorized = True
        if "SKILL_PROGRAM" in types or "skill" in cat or "pmkvy" in domain or "skillindia" in domain:
            matrix_map[st]["skill_programs"].append(src_info)
            is_categorized = True
        if "TRAINING" in types or "training" in cat or "nielit" in domain:
            matrix_map[st]["training"].append(src_info)
            is_categorized = True
        if "COMPETITION" in types or "competition" in cat or "sih" in domain or "hackathon" in domain:
            matrix_map[st]["competition"].append(src_info)
            is_categorized = True
        if "ADMISSION" in types or "admission" in cat or "nta" in domain or "cuet" in domain:
            matrix_map[st]["admission"].append(src_info)
            is_categorized = True
        if "APPRENTICESHIP" in types or "apprentice" in cat or "apprenticeship" in domain:
            matrix_map[st]["apprenticeship"].append(src_info)
            is_categorized = True
        if "FELLOWSHIP" in types or "fellowship" in cat or "pmrf" in domain or "csir" in domain:
            matrix_map[st]["fellowship"].append(src_info)
            is_categorized = True
        if "GRANT" in types or "grant" in cat or "birac" in domain or "dst" in domain:
            matrix_map[st]["grant"].append(src_info)
            is_categorized = True

        if not is_categorized:
            matrix_map[st]["recruitment"].append(src_info)

        mapped_count += 1

    matrix_list = [
        StateCategoryCoverage(state=state_name, sources=categories)
        for state_name, categories in matrix_map.items()
        if any(len(sources_list) > 0 for sources_list in categories.values()) or state_name in ["CENTRAL", "Maharashtra", "Karnataka", "Tamil Nadu", "Uttar Pradesh", "Bihar", "West Bengal", "Rajasthan"]
    ]

    active_states = set(s.state for s in sources if s.state)
    if any(s.state is None for s in sources):
        active_states.add("CENTRAL")

    return SourceCoverageMatrixResponse(
        matrix=matrix_list,
        total_states_covered=len(active_states),
        total_sources_mapped=mapped_count,
    )
