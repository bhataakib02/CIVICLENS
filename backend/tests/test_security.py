"""Security tests (maps to threat-model.md #2, #6 and the prompt's checklist).

Covers: wrong password, expired/invalid/missing/tampered tokens, suspended
user, and cross-citizen (horizontal) access isolation.
"""
from __future__ import annotations

from datetime import timedelta

import pytest
from sqlalchemy import select

from app.core.security import create_access_token

pytestmark = pytest.mark.security

STRONG_PW = "CorrectHorse9Battery!"


def _register(client, email, password=STRONG_PW):
    return client.post("/api/v1/auth/register", json={"email": email, "password": password})


def _h(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_wrong_password_401_without_enumeration(client):
    _register(client, "citizen@example.com")
    r = client.post(
        "/api/v1/auth/login",
        json={"email": "citizen@example.com", "password": "totally-wrong-123456"},
    )
    assert r.status_code == 401
    body = r.json()
    assert body["error"]["code"] == "INVALID_CREDENTIALS"
    # Same code/message whether or not the email exists (no enumeration).
    r2 = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "totally-wrong-123456"},
    )
    assert r2.status_code == 401
    assert r2.json()["error"]["code"] == body["error"]["code"]
    assert r2.json()["error"]["message"] == body["error"]["message"]


def test_missing_token_401(client):
    r = client.get("/api/v1/me")
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "INVALID_TOKEN"


def test_invalid_token_401(client):
    r = client.get("/api/v1/me", headers=_h("not-a-jwt"))
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "INVALID_TOKEN"


def test_tampered_token_401(client):
    token = _register(client, "citizen@example.com").json()["access_token"]
    tampered = token[:-3] + ("aaa" if token[-3:] != "aaa" else "bbb")
    r = client.get("/api/v1/me", headers=_h(tampered))
    assert r.status_code == 401


def test_expired_token_401(client, db_session_factory):
    _register(client, "citizen@example.com")
    from app.models.user import User

    with db_session_factory() as s:
        user = s.scalar(select(User).where(User.email == "citizen@example.com"))
        uid = str(user.id)
    expired, _ = create_access_token(
        subject=uid, role="citizen", expires_delta=timedelta(seconds=-1)
    )
    r = client.get("/api/v1/me", headers=_h(expired))
    assert r.status_code == 401


def test_suspended_user_denied(client, db_session_factory):
    token = _register(client, "citizen@example.com").json()["access_token"]
    # Suspend the account directly in the DB.
    from app.models.enums import UserStatus
    from app.models.user import User

    with db_session_factory() as s:
        user = s.scalar(select(User).where(User.email == "citizen@example.com"))
        user.status = UserStatus.SUSPENDED
        s.commit()

    # Existing access token must now be rejected (403 ACCOUNT_SUSPENDED).
    r = client.get("/api/v1/me", headers=_h(token))
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "ACCOUNT_SUSPENDED"

    # And login is refused.
    r2 = client.post(
        "/api/v1/auth/login", json={"email": "citizen@example.com", "password": STRONG_PW}
    )
    assert r2.status_code == 403
    assert r2.json()["error"]["code"] == "ACCOUNT_SUSPENDED"


def test_cross_citizen_address_access_isolated(client):
    # Citizen A creates an address.
    token_a = _register(client, "a@example.com").json()["access_token"]
    addr = client.post(
        "/api/v1/me/addresses",
        headers=_h(token_a),
        json={
            "type": "permanent",
            "state": "KA",
            "district": "BLR",
            "pincode": "560001",
            "line1": "A road",
        },
    ).json()
    addr_id = addr["id"]

    # Citizen B must not be able to update or delete A's address.
    token_b = _register(client, "b@example.com").json()["access_token"]

    upd = client.put(
        f"/api/v1/me/addresses/{addr_id}", headers=_h(token_b), json={"district": "hacked"}
    )
    assert upd.status_code == 404  # no horizontal escalation, no existence disclosure
    assert upd.json()["error"]["code"] == "NOT_FOUND"

    dele = client.delete(f"/api/v1/me/addresses/{addr_id}", headers=_h(token_b))
    assert dele.status_code == 404

    # B's own listing does not contain A's address.
    listing_b = client.get("/api/v1/me/addresses", headers=_h(token_b))
    assert all(a["id"] != addr_id for a in listing_b.json())

    # A can still access its own address (control).
    listing_a = client.get("/api/v1/me/addresses", headers=_h(token_a))
    assert any(a["id"] == addr_id for a in listing_a.json())
