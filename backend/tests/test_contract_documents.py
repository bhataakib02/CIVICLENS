"""Contract test: documents slice paths/methods/schemas declared in openapi.yaml
and implemented by the app (prompt §55)."""
from __future__ import annotations

import os

import pytest
import yaml

pytestmark = pytest.mark.integration

SLICE_PATHS = {
    "/documents": {"get", "post"},
    "/documents/upload-init": {"post"},
    "/documents/{document_id}/complete": {"post"},
    "/documents/{document_id}": {"get", "delete"},
    "/documents/{document_id}/download": {"get"},
    "/documents/{document_id}/confirm": {"post"},
}
SLICE_SCHEMAS = {"Document", "DocumentDetail", "UploadInitResponse", "ExtractedField"}


def _contract() -> dict:
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    with open(os.path.join(root, "openapi.yaml"), encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def test_contract_declares_document_paths():
    c = _contract()
    for path, methods in SLICE_PATHS.items():
        assert path in c["paths"], f"contract missing {path}"
        for m in methods:
            assert m in c["paths"][path], f"{path} missing {m}"


def test_contract_declares_schemas():
    c = _contract()
    for name in SLICE_SCHEMAS:
        assert name in c["components"]["schemas"], f"contract missing schema {name}"


def test_generated_matches_contract_for_documents(client):
    gen = client.get("/openapi.json").json()["paths"]
    for path, methods in SLICE_PATHS.items():
        full = f"/api/v1{path}"
        assert full in gen, f"implementation missing {full}"
        impl = {m.lower() for m in gen[full]}
        assert methods <= impl, f"{full} missing {methods - impl}"


def test_document_status_enum_extended_but_retains_originals():
    c = _contract()
    status_enum = set(c["components"]["schemas"]["Document"]["properties"]["status"]["enum"])
    # Original data-dictionary values retained.
    assert {"uploaded", "processing", "verified", "rejected"} <= status_enum
    # Lifecycle extension present.
    assert {"verification_required", "validation_failed", "processing_failed"} <= status_enum
