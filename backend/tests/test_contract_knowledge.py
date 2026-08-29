"""Contract test: knowledge + assistant slice paths/methods/schemas are declared
in openapi.yaml and implemented by the app (prompt §39)."""
from __future__ import annotations

import os

import pytest
import yaml

pytestmark = pytest.mark.integration

SLICE_PATHS = {
    "/knowledge/search": {"post"},
    "/knowledge/sources": {"get", "post"},
    "/knowledge/jobs/{job_id}": {"get"},
    "/knowledge/sources/{source_id}/verify": {"post"},
    "/assistant/query": {"post"},
}

SLICE_SCHEMAS = {
    "KnowledgeSource",
    "KnowledgeSourceInput",
    "IngestionJob",
    "KnowledgeSearchResult",
    "AssistantResponse",
}


def _contract() -> dict:
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    with open(os.path.join(root, "openapi.yaml"), encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def test_contract_declares_knowledge_paths():
    c = _contract()
    for path, methods in SLICE_PATHS.items():
        assert path in c["paths"], f"contract missing {path}"
        for m in methods:
            assert m in c["paths"][path], f"{path} missing {m}"


def test_contract_declares_schemas():
    c = _contract()
    for name in SLICE_SCHEMAS:
        assert name in c["components"]["schemas"], f"contract missing schema {name}"


def test_generated_matches_contract_for_knowledge(client):
    gen = client.get("/openapi.json").json()["paths"]
    for path, methods in SLICE_PATHS.items():
        full = f"/api/v1{path}"
        assert full in gen, f"implementation missing {full}"
        impl = {m.lower() for m in gen[full]}
        assert methods <= impl, f"{full} missing {methods - impl}"


def test_assistant_messages_preserved():
    # The pre-existing conversational endpoint must remain in the contract.
    c = _contract()
    assert "/assistant/messages" in c["paths"]
