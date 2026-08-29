"""Integration tests for citizen consent management."""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration


def test_grant_and_revoke_consent_flow(client):
    # 1. Register a citizen and get token
    reg = client.post("/api/v1/auth/register", json={"email": "consent_citizen@example.com", "password": "StrongPassword123!"})
    assert reg.status_code == 201
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. List initial consents (empty)
    resp = client.get("/api/v1/me/consents", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == []

    # 3. Grant consent
    grant_payload = {
        "consent_type": "agent_assistance",
        "purpose": "CSC agent assisting with housing scheme application",
        "scope": {"scheme_categories": ["housing"]},
        "version": "1.0",
    }
    resp = client.post("/api/v1/me/consents", json=grant_payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    consent_id = data["id"]
    assert data["consent_type"] == "agent_assistance"
    assert data["revoked_at"] is None

    # 4. List consents (should contain 1)
    resp = client.get("/api/v1/me/consents", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    # 5. Revoke consent
    resp = client.post(f"/api/v1/me/consents/{consent_id}/revoke", headers=headers)
    assert resp.status_code == 200
    revoked_data = resp.json()
    assert revoked_data["revoked_at"] is not None
