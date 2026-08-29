"""Contract test: applications slice paths/methods/schemas (prompt §39)."""
from __future__ import annotations

import os

import pytest
import yaml

pytestmark = pytest.mark.integration

SLICE_PATHS = {
    "/applications": {"get", "post"},
    "/applications/{application_id}": {"get"},
    "/applications/{application_id}/submit": {"post"},
    "/applications/{application_id}/withdraw": {"post"},
    "/applications/{application_id}/checklist": {"get"},
    "/applications/{application_id}/assign": {"post"},
    "/applications/{application_id}/review": {"post"},
    "/applications/{application_id}/resolve-action": {"post"},
    "/applications/{application_id}/complete": {"post"},
    "/notifications": {"get"},
}
SLICE_SCHEMAS = {"Application", "ApplicationDetail", "ApplicationCreate", "ApplicationChecklist", "ApplicationPage"}


def _contract() -> dict:
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    with open(os.path.join(root, "openapi.yaml"), encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def test_contract_declares_application_paths():
    c = _contract()
    for path, methods in SLICE_PATHS.items():
        assert path in c["paths"], f"contract missing {path}"
        for m in methods:
            assert m in c["paths"][path], f"{path} missing {m}"


def test_contract_declares_schemas():
    c = _contract()
    for name in SLICE_SCHEMAS:
        assert name in c["components"]["schemas"], f"contract missing schema {name}"


def test_generated_matches_contract_for_applications(client):
    gen = client.get("/openapi.json").json()["paths"]
    for path, methods in SLICE_PATHS.items():
        full = f"/api/v1{path}"
        assert full in gen, f"implementation missing {full}"
        impl = {m.lower() for m in gen[full]}
        assert methods <= impl, f"{full} missing {methods - impl}"


def test_status_enum_extended_but_retains_originals():
    c = _contract()
    status_enum = set(c["components"]["schemas"]["Application"]["properties"]["status"]["enum"])
    assert {"draft", "submitted", "under_review", "info_requested", "approved", "rejected", "withdrawn"} <= status_enum
    assert {"ready_for_submission", "action_required", "completed"} <= status_enum
