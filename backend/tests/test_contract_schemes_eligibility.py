"""Contract test: scheme catalog + eligibility slice paths/methods/schemas are
declared in openapi.yaml and implemented by the app (prompt §29)."""
from __future__ import annotations

import os

import pytest
import yaml

pytestmark = pytest.mark.integration

SLICE_PATHS = {
    "/schemes": {"get", "post"},
    "/schemes/{scheme_id}": {"get"},
    "/schemes/{scheme_id}/versions": {"get", "post"},
    "/scheme-versions/{scheme_version_id}/rules": {"get", "post"},
    "/eligibility/check": {"post"},
    "/admin/scheme-versions/{scheme_version_id}/publish": {"post"},
    "/admin/scheme-versions/{scheme_version_id}/supersede": {"post"},
    "/admin/rules/validate": {"post"},
}

SLICE_SCHEMAS = {
    "SchemeCreate",
    "SchemeSummary",
    "SchemePage",
    "SchemeDetail",
    "SchemeVersion",
    "SchemeVersionInput",
    "EligibilityRule",
    "RuleSetInput",
    "RuleValidateResult",
    "EligibilityResult",
    "RuleOutcome",
}


def _contract() -> dict:
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    with open(os.path.join(root, "openapi.yaml"), encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def test_contract_declares_scheme_eligibility_paths():
    c = _contract()
    for path, methods in SLICE_PATHS.items():
        assert path in c["paths"], f"contract missing {path}"
        for m in methods:
            assert m in c["paths"][path], f"{path} missing {m}"


def test_contract_declares_schemas():
    c = _contract()
    for name in SLICE_SCHEMAS:
        assert name in c["components"]["schemas"], f"contract missing schema {name}"


def test_generated_matches_contract_for_scheme_eligibility(client):
    gen = client.get("/openapi.json").json()["paths"]
    for path, methods in SLICE_PATHS.items():
        full = f"/api/v1{path}"
        assert full in gen, f"implementation missing {full}"
        impl = {m.lower() for m in gen[full]}
        assert methods <= impl, f"{full} missing {methods - impl}"


def test_result_enums_match_authoritative_vocabulary():
    c = _contract()
    res = c["components"]["schemas"]["EligibilityResult"]["properties"]["result"]["enum"]
    assert set(res) == {"eligible", "not_eligible", "likely_eligible", "insufficient_data"}
    outcome = c["components"]["schemas"]["RuleOutcome"]["properties"]["outcome"]["enum"]
    assert set(outcome) == {"pass", "fail", "unknown"}
