"""FastAPI router for Location hierarchy endpoints."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.modules.locations.service import LocationService

locations_router = APIRouter(prefix="/locations", tags=["locations"])


class LocationValidationRequest(BaseModel):
    state: str = Field(..., description="State or Union Territory name or code (e.g. 'West Bengal' or 'WB')")
    district: Optional[str] = Field(None, description="District name or code or 'ALL'")
    sub_district: Optional[str] = Field(None, description="Tehsil / Sub-District name or code or 'ALL'")
    block: Optional[str] = Field(None, description="Block name or code or 'ALL'")


class LocationValidationResponse(BaseModel):
    valid: bool
    error: Optional[str] = None
    state: Optional[Dict[str, Any]] = None
    district: Optional[Dict[str, Any]] = None
    sub_district: Optional[Dict[str, Any]] = None
    block: Optional[Dict[str, Any]] = None
    is_all_districts: bool = False
    is_all_sub_districts: bool = False
    is_all_blocks: bool = False


@locations_router.get("/states")
def list_states(
    query: Optional[str] = Query(None, description="Search filter for state name or code"),
    type: Optional[str] = Query(None, description="Filter by 'STATE' or 'UNION_TERRITORY'"),
) -> List[Dict[str, Any]]:
    """List all 28 States and 8 Union Territories of India with LGD metadata."""
    states = LocationService.get_all_states()

    if type:
        type_upper = type.strip().upper()
        states = [s for s in states if s["type"] == type_upper]

    if query:
        q = query.strip().lower()
        states = [s for s in states if q in s["name"].lower() or q in s["code"].lower()]

    return states


@locations_router.get("/states/{state_id}/districts")
def list_districts_by_state(
    state_id: str,
    query: Optional[str] = Query(None, description="Search filter for district name"),
) -> List[Dict[str, Any]]:
    """List official districts belonging to the specified State or Union Territory."""
    st = LocationService.get_state(state_id)
    if not st:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"State or Union Territory '{state_id}' not found.",
        )

    districts = LocationService.get_districts_by_state(st["id"])
    if query:
        q = query.strip().lower()
        districts = [d for d in districts if q in d["name"].lower()]

    return districts


@locations_router.get("/districts/{district_id}/sub-districts")
def list_sub_districts(
    district_id: str,
    query: Optional[str] = Query(None, description="Search filter for sub-district / tehsil name"),
) -> List[Dict[str, Any]]:
    """List Tehsils / Sub-Districts / Taluks / Mandals belonging to a district."""
    dt = LocationService.get_district(district_id)
    if not dt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"District '{district_id}' not found.",
        )

    sub_dists = LocationService.get_sub_districts_by_district(dt["id"])
    if query:
        q = query.strip().lower()
        sub_dists = [sd for sd in sub_dists if q in sd["name"].lower()]

    return sub_dists


@locations_router.get("/districts/{district_id}/blocks")
def list_blocks(
    district_id: str,
    sub_district_id: Optional[str] = Query(None, description="Filter blocks by sub-district"),
    query: Optional[str] = Query(None, description="Search filter for block name"),
) -> List[Dict[str, Any]]:
    """List Community Development Blocks belonging to a district or sub-district."""
    dt = LocationService.get_district(district_id)
    if not dt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"District '{district_id}' not found.",
        )

    blocks = LocationService.get_blocks_by_district_or_subdistrict(
        district_key=dt["id"], sub_district_key=sub_district_id
    )
    if query:
        q = query.strip().lower()
        blocks = [b for b in blocks if q in b["name"].lower()]

    return blocks


@locations_router.post("/validate", response_model=LocationValidationResponse)
def validate_location_hierarchy(req: LocationValidationRequest) -> LocationValidationResponse:
    """Validate administrative location hierarchy and reject invalid parent-child combinations."""
    is_valid, err_msg, resolved = LocationService.validate_location_hierarchy(
        state_key=req.state,
        district_key=req.district,
        sub_district_key=req.sub_district,
        block_key=req.block,
    )

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "INVALID_LOCATION_HIERARCHY", "message": err_msg},
        )

    return LocationValidationResponse(
        valid=True,
        error=None,
        state=resolved.get("state"),
        district=resolved.get("district"),
        sub_district=resolved.get("sub_district"),
        block=resolved.get("block"),
        is_all_districts=resolved.get("is_all_districts", False),
        is_all_sub_districts=resolved.get("is_all_sub_districts", False),
        is_all_blocks=resolved.get("is_all_blocks", False),
    )
