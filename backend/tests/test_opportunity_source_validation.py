"""Unit & Integration tests for Source Pre-Enablement Validator (prompt Phase 4, Phase 5, Phase 18)."""
from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

from app.modules.opportunities.ingestion.validator import SourceValidator, SourceValidationResult


def test_source_validator_invalid_domain():
    validator = SourceValidator()
    res = validator.validate_source("invalid-url-schema")
    assert res.dns_valid is False
    assert res.health_status == "FAILED"


def test_source_validator_successful_validation():
    validator = SourceValidator()

    mock_doc = MagicMock()
    mock_doc.content = "Job Title: Civil Assistant Engineer Recruitment 2026. Organization: Government of India."
    mock_doc.url = "https://valid-govt.gov.in/recruitment/job1"

    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.text = "<html><body><h1>Recruitment 2026</h1><p>Organization: Government of India</p></body></html>"
    mock_res.content = b"<html><body><h1>Recruitment 2026</h1><p>Organization: Government of India</p></body></html>"
    mock_res.headers = {"content-type": "text/html"}

    with patch("socket.gethostbyname", return_value="1.2.3.4"):
        with patch.object(validator.fetcher, "fetch", return_value=mock_res):
            with patch.object(validator.robots_checker, "is_allowed", return_value=True):
                with patch("app.modules.opportunities.ingestion.validator.get_connector_for_source") as mock_conn_factory:
                    mock_conn = mock_conn_factory.return_value
                    mock_conn.fetch_items.return_value = [mock_doc]
                    res = validator.validate_source("https://valid-govt.gov.in/recruitment")
                    assert res.dns_valid is True
                    assert res.https_valid is True
                    assert res.robots_allowed is True
                    assert res.sample_pages == 1
                    assert res.health_status == "HEALTHY"
