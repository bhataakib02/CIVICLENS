"""Contract test: the app's generated OpenAPI must cover the slice's paths
declared in the repository's authoritative openapi.yaml.

Scope: the auth + citizen-profile vertical slice (the only implemented
module). Future modules (schemes, eligibility, ...) are intentionally not yet
implemented and are excluded from this check.
"""
from __future__ import annotations

import os

import pytest
import yaml

pytestmark = pytest.mark.integration

# Paths owned by this slice (contract path -> methods we implement).
SLICE_PATHS = {
    "/health": {"get"},
    "/health/ready": {"get"},
    "/auth/register": {"post"},
    "/auth/login": {"post"},
    "/auth/refresh": {"post"},
    "/auth/logout": {"post"},
    "/me": {"get", "patch"},
    "/me/account": {"get"},
    "/me/profile": {"get", "put", "patch"},
    "/me/addresses": {"get", "post"},
    "/me/addresses/{address_id}": {"put", "delete"},
    # Application workflow + case management slice (Phase 5).
    "/applications": {"get", "post"},
    "/applications/{application_id}": {"get"},
    "/applications/{application_id}/checklist": {"get"},
    "/applications/{application_id}/submit": {"post"},
    "/applications/{application_id}/withdraw": {"post"},
    "/applications/{application_id}/assign": {"post"},
    "/applications/{application_id}/review": {"post"},
    "/applications/{application_id}/resolve-action": {"post"},
    "/applications/{application_id}/complete": {"post"},
}


def _load_contract() -> dict:
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    with open(os.path.join(repo_root, "openapi.yaml"), encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def test_contract_declares_all_slice_paths():
    contract = _load_contract()
    paths = contract["paths"]
    for path, methods in SLICE_PATHS.items():
        assert path in paths, f"contract missing {path}"
        for m in methods:
            assert m in paths[path], f"contract {path} missing method {m}"


def test_generated_openapi_matches_contract_for_slice(client):
    generated = client.get("/openapi.json").json()
    gen_paths = generated["paths"]
    prefix = "/api/v1"

    for path, methods in SLICE_PATHS.items():
        full = f"{prefix}{path}"
        assert full in gen_paths, f"implementation missing {full}"
        impl_methods = {m.lower() for m in gen_paths[full].keys()}
        missing = methods - impl_methods
        assert not missing, f"{full} missing implemented methods {missing}"


def test_otp_endpoints_preserved_in_contract():
    # The deliberate extension must NOT have removed the primary phone+OTP flow.
    contract = _load_contract()
    for p in ("/auth/otp/request", "/auth/otp/verify", "/auth/token/refresh"):
        assert p in contract["paths"], f"OTP contract endpoint {p} was lost"


def test_applications_contract_fully_synchronized(client):
    """Every /applications* path+method declared in the canonical contract must
    be implemented, and vice-versa (prompt §39 — OpenAPI synchronized)."""
    contract = _load_contract()
    generated = client.get("/openapi.json").json()["paths"]
    prefix = "/api/v1"

    contract_ops = {
        (path, method)
        for path, item in contract["paths"].items()
        if path.startswith("/applications")
        for method in item
        if method in {"get", "post", "patch", "put", "delete"}
    }
    impl_ops = {
        (path[len(prefix):], method)
        for path, item in generated.items()
        if path.startswith(f"{prefix}/applications")
        for method in item
        if method in {"get", "post", "patch", "put", "delete"}
    }
    # Contract paths must all be implemented (no aspirational endpoints).
    missing_impl = contract_ops - impl_ops
    assert not missing_impl, f"contract declares unimplemented application ops: {missing_impl}"
    # Implemented paths must all be declared in the contract.
    missing_contract = impl_ops - contract_ops
    assert not missing_contract, f"implemented application ops missing from contract: {missing_contract}"
