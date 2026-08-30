"""Location service layer providing LGD hierarchy queries and strict parent-child validation."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from app.modules.locations.data import (
    ALL_BLOCKS,
    ALL_DISTRICTS,
    ALL_SUB_DISTRICTS,
    BLOCK_MAP,
    DISTRICT_MAP,
    INDIA_STATES,
    STATE_MAP_BY_KEY,
    SUB_DISTRICT_MAP,
    BlockData,
    DistrictData,
    StateData,
    SubDistrictData,
)

WILDCARD_DISTRICTS = {"ALL", "ALL_DISTRICTS", "ALL DISTRICTS", "*"}
WILDCARD_TEHSILS = {"ALL", "ALL_TEHSILS", "ALL TEHSILS", "ALL_SUB_DISTRICTS", "*"}
WILDCARD_BLOCKS = {"ALL", "ALL_BLOCKS", "ALL BLOCKS", "*"}


def is_wildcard(val: Optional[str], wildcard_set: set[str]) -> bool:
    if not val:
        return True
    norm = val.strip().upper()
    return norm in wildcard_set


class LocationService:
    @staticmethod
    def get_all_states() -> List[StateData]:
        """Returns all 36 States and Union Territories sorted by type and name."""
        return sorted(INDIA_STATES, key=lambda s: (0 if s["type"] == "STATE" else 1, s["name"]))

    @staticmethod
    def get_state(state_key: str) -> Optional[StateData]:
        if not state_key:
            return None
        key = state_key.strip()
        # Check by uppercase ID/code or lowercase name
        return STATE_MAP_BY_KEY.get(key.upper()) or STATE_MAP_BY_KEY.get(key.lower())

    @staticmethod
    def get_districts_by_state(state_key: str) -> List[DistrictData]:
        st = LocationService.get_state(state_key)
        if not st:
            return []
        st_id = st["id"]
        districts = [d for d in ALL_DISTRICTS if d["state_id"] == st_id]
        return sorted(districts, key=lambda d: d["name"])

    @staticmethod
    def get_district(district_key: str) -> Optional[DistrictData]:
        if not district_key:
            return None
        key = district_key.strip().upper()
        if key in DISTRICT_MAP:
            return DISTRICT_MAP[key]
        # Fallback name search
        norm_name = district_key.strip().lower()
        for d in ALL_DISTRICTS:
            if d["name"].lower() == norm_name or d["code"].upper() == key:
                return d
        return None

    @staticmethod
    def get_sub_districts_by_district(district_key: str) -> List[SubDistrictData]:
        dt = LocationService.get_district(district_key)
        if not dt:
            return []
        dt_id = dt["id"]
        sub_dists = [sd for sd in ALL_SUB_DISTRICTS if sd["district_id"] == dt_id]
        return sorted(sub_dists, key=lambda sd: sd["name"])

    @staticmethod
    def get_sub_district(sub_district_key: str) -> Optional[SubDistrictData]:
        if not sub_district_key:
            return None
        key = sub_district_key.strip().upper()
        if key in SUB_DISTRICT_MAP:
            return SUB_DISTRICT_MAP[key]
        norm_name = sub_district_key.strip().lower()
        for sd in ALL_SUB_DISTRICTS:
            if sd["name"].lower() == norm_name or sd["code"].upper() == key:
                return sd
        return None

    @staticmethod
    def get_blocks_by_district_or_subdistrict(
        district_key: Optional[str] = None, sub_district_key: Optional[str] = None
    ) -> List[BlockData]:
        if sub_district_key:
            sd = LocationService.get_sub_district(sub_district_key)
            if sd:
                sd_id = sd["id"]
                blocks = [b for b in ALL_BLOCKS if b["sub_district_id"] == sd_id]
                return sorted(blocks, key=lambda b: b["name"])

        if district_key:
            dt = LocationService.get_district(district_key)
            if dt:
                dt_id = dt["id"]
                blocks = [b for b in ALL_BLOCKS if b["district_id"] == dt_id]
                return sorted(blocks, key=lambda b: b["name"])

        return []

    @staticmethod
    def validate_location_hierarchy(
        state_key: str,
        district_key: Optional[str] = None,
        sub_district_key: Optional[str] = None,
        block_key: Optional[str] = None,
    ) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """Strict validation of administrative hierarchy.

        Returns (is_valid, error_message, resolved_metadata).
        Rejects invalid parent-child relationships (e.g. State=West Bengal, District=Agra).
        """
        resolved: Dict[str, Any] = {
            "state": None,
            "district": None,
            "sub_district": None,
            "block": None,
            "is_all_districts": False,
            "is_all_sub_districts": False,
            "is_all_blocks": False,
        }

        # 1. Validate State/UT
        st = LocationService.get_state(state_key)
        if not st:
            return False, f"Invalid State or Union Territory: '{state_key}'", resolved
        resolved["state"] = st

        # 2. Validate District
        if is_wildcard(district_key, WILDCARD_DISTRICTS):
            resolved["is_all_districts"] = True
            resolved["is_all_sub_districts"] = True
            resolved["is_all_blocks"] = True
            return True, None, resolved

        dt = LocationService.get_district(district_key)  # type: ignore[arg-type]
        if not dt:
            return False, f"District '{district_key}' not found", resolved

        # Parent check: District -> State
        if dt["state_id"] != st["id"]:
            return (
                False,
                f"District '{dt['name']}' does not belong to {st['type']} '{st['name']}' (belongs to '{dt['state_id']}')",
                resolved,
            )
        resolved["district"] = dt

        # 3. Validate Sub-District (Tehsil / Taluk / Mandal)
        if is_wildcard(sub_district_key, WILDCARD_TEHSILS):
            resolved["is_all_sub_districts"] = True
            resolved["is_all_blocks"] = True
            return True, None, resolved

        sd = LocationService.get_sub_district(sub_district_key)  # type: ignore[arg-type]
        if not sd:
            return False, f"Tehsil/Sub-District '{sub_district_key}' not found", resolved

        # Parent check: Sub-District -> District
        if sd["district_id"] != dt["id"]:
            return (
                False,
                f"Tehsil/Sub-District '{sd['name']}' does not belong to District '{dt['name']}'",
                resolved,
            )
        resolved["sub_district"] = sd

        # 4. Validate Block
        if is_wildcard(block_key, WILDCARD_BLOCKS):
            resolved["is_all_blocks"] = True
            return True, None, resolved

        block = BLOCK_MAP.get(block_key.strip().upper()) if block_key else None
        if not block and block_key:
            norm_name = block_key.strip().lower()
            for b in ALL_BLOCKS:
                if b["name"].lower() == norm_name or b["code"].upper() == block_key.strip().upper():
                    block = b
                    break

        if not block and block_key:
            return False, f"Block '{block_key}' not found", resolved

        if block:
            if block["district_id"] != dt["id"]:
                return (
                    False,
                    f"Block '{block['name']}' does not belong to District '{dt['name']}'",
                    resolved,
                )
            if sd and block["sub_district_id"] and block["sub_district_id"] != sd["id"]:
                return (
                    False,
                    f"Block '{block['name']}' does not belong to Sub-District '{sd['name']}'",
                    resolved,
                )
            resolved["block"] = block

        return True, None, resolved
