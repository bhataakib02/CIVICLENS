"""Tests for Location Hierarchy API endpoints and Validation logic."""
from fastapi.testclient import TestClient
import pytest

from app.main import create_app
from app.modules.locations.service import LocationService


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_location_service_counts():
    """Verify dataset contains all 28 States and 8 Union Territories."""
    states = LocationService.get_all_states()
    assert len(states) == 36

    only_states = [s for s in states if s["type"] == "STATE"]
    only_uts = [s for s in states if s["type"] == "UNION_TERRITORY"]

    assert len(only_states) == 28
    assert len(only_uts) == 8


def test_list_states_endpoint(client):
    """Test /api/v1/locations/states endpoint."""
    res = client.get("/api/v1/locations/states")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 36

    # Test filtering by type
    res_uts = client.get("/api/v1/locations/states?type=UNION_TERRITORY")
    assert res_uts.status_code == 200
    assert len(res_uts.json()) == 8

    # Test query filter
    res_search = client.get("/api/v1/locations/states?query=bengal")
    assert res_search.status_code == 200
    assert len(res_search.json()) == 1
    assert res_search.json()[0]["name"] == "West Bengal"


def test_list_districts_endpoint(client):
    """Test /api/v1/locations/states/{state_id}/districts endpoint."""
    res = client.get("/api/v1/locations/states/WB/districts")
    assert res.status_code == 200
    districts = res.json()
    assert len(districts) == 23
    names = [d["name"] for d in districts]
    assert "Kolkata" in names
    assert "Howrah" in names

    # 404 for invalid state
    res_404 = client.get("/api/v1/locations/states/INVALID_STATE/districts")
    assert res_404.status_code == 404


def test_list_sub_districts_and_blocks_endpoint(client):
    """Test sub-district and block endpoints for a valid district."""
    # Kolkata Sub-districts
    res_sd = client.get("/api/v1/locations/districts/WB_KLK/sub-districts")
    assert res_sd.status_code == 200
    sub_districts = res_sd.json()
    assert len(sub_districts) > 0

    # Kolkata Blocks
    res_bk = client.get("/api/v1/locations/districts/WB_KLK/blocks")
    assert res_bk.status_code == 200
    blocks = res_bk.json()
    assert len(blocks) > 0


def test_validate_location_hierarchy_success(client):
    """Test validation with valid hierarchy."""
    payload = {
        "state": "West Bengal",
        "district": "Kolkata"
    }
    res = client.post("/api/v1/locations/validate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["valid"] is True
    assert data["state"]["name"] == "West Bengal"
    assert data["district"]["name"] == "Kolkata"


def test_validate_location_hierarchy_wildcard_all(client):
    """Test validation with 'ALL' districts."""
    payload = {
        "state": "Maharashtra",
        "district": "ALL"
    }
    res = client.post("/api/v1/locations/validate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["valid"] is True
    assert data["is_all_districts"] is True


def test_validate_location_hierarchy_mismatch_rejection(client):
    """Test rejection when District does not belong to State (e.g. State=WB, District=Agra)."""
    payload = {
        "state": "West Bengal",
        "district": "Agra"
    }
    res = client.post("/api/v1/locations/validate", json=payload)
    assert res.status_code == 422
    err_body = res.json()
    assert "error" in err_body or "detail" in err_body
    msg = str(err_body)
    assert "Agra" in msg and "West Bengal" in msg
