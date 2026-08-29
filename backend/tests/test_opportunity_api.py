"""Integration tests for Opportunity API endpoints and Natural Language Search."""
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.modules.opportunities.schemas import OpportunityListResponse, OpportunityResponse

client = TestClient(app)

MOCK_LIST_RESPONSE = OpportunityListResponse(
    items=[],
    total=0,
    page=1,
    page_size=20,
    indexed_sources=6,
    verified_sources=5,
    last_crawl_time=None,
    last_verification_time=None,
)


@patch("app.modules.opportunities.service.OpportunityService.list_opportunities", return_value=MOCK_LIST_RESPONSE)
def test_list_opportunities_api(mock_list):
    response = client.get("/api/v1/opportunities")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "indexed_sources" in data
    assert data["indexed_sources"] == 6


def test_categories_endpoint():
    response = client.get("/api/v1/opportunities/categories")
    assert response.status_code == 200
    data = response.json()
    assert "types" in data
    assert "categories" in data


@patch("app.modules.opportunities.service.OpportunityService.search_natural_language", return_value=MOCK_LIST_RESPONSE)
def test_natural_language_search_api(mock_search):
    response = client.get("/api/v1/opportunities/search?q=Find+software+internships+in+Bangalore")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data


def test_admin_sources_api_requires_admin():
    response = client.get("/api/v1/admin/opportunity-sources")
    assert response.status_code in [401, 403]
