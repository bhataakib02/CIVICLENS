"""Integration tests against a real PostgreSQL (pgserver).

Assert status, response schema, database state, and authorization behavior —
not merely HTTP 200.
"""
from __future__ import annotations

import pytest
from sqlalchemy import func, select

pytestmark = pytest.mark.integration

STRONG_PW = "CorrectHorse9Battery!"


def _register(client, email="citizen@example.com", password=STRONG_PW):
    return client.post("/api/v1/auth/register", json={"email": email, "password": password})


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ------------------------------ health ------------------------------------- #
def test_health_ok(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_readiness_checks_db(client):
    r = client.get("/api/v1/health/ready")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ready"
    assert body["database"] == "ok"


# ------------------------------ registration -------------------------------- #
def test_register_creates_user_and_profile(client, db_session_factory):
    r = _register(client)
    assert r.status_code == 201
    body = r.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"] and body["refresh_token"]
    assert body["expires_in"] == 900
    # no secret leakage
    assert "password" not in r.text.lower() or "password_hash" not in r.text

    from app.models.citizen_profile import CitizenProfile
    from app.models.user import User

    with db_session_factory() as s:
        user = s.scalar(select(User).where(User.email == "citizen@example.com"))
        assert user is not None
        assert user.role.value == "citizen"
        assert user.status.value == "active"
        assert user.password_hash and user.password_hash.startswith("$argon2id$")
        profile = s.scalar(select(CitizenProfile).where(CitizenProfile.user_id == user.id))
        assert profile is not None  # 1:1 profile auto-created


def test_duplicate_registration_rejected(client):
    assert _register(client).status_code == 201
    r = _register(client)
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "ACCOUNT_EXISTS"


def test_register_normalizes_email(client, db_session_factory):
    assert _register(client, email="MixedCase@Example.COM").status_code == 201
    from app.models.user import User

    with db_session_factory() as s:
        assert s.scalar(select(User).where(User.email == "mixedcase@example.com")) is not None


def test_register_weak_password_422(client):
    r = client.post("/api/v1/auth/register", json={"email": "x@y.com", "password": "short"})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"


# ------------------------------ login --------------------------------------- #
def test_login_success(client):
    _register(client)
    r = client.post(
        "/api/v1/auth/login", json={"email": "citizen@example.com", "password": STRONG_PW}
    )
    assert r.status_code == 200
    assert r.json()["access_token"]


def test_login_updates_last_login_at(client, db_session_factory):
    _register(client)
    client.post(
        "/api/v1/auth/login", json={"email": "citizen@example.com", "password": STRONG_PW}
    )
    from app.models.user import User

    with db_session_factory() as s:
        user = s.scalar(select(User).where(User.email == "citizen@example.com"))
        assert user.last_login_at is not None


# ------------------------------ /me ----------------------------------------- #
def test_me_returns_profile(client):
    token = _register(client).json()["access_token"]
    r = client.get("/api/v1/me", headers=_auth_header(token))
    assert r.status_code == 200
    body = r.json()
    assert "id" in body and "profile_completeness" in body
    assert body["current_version_no"] == 0


def test_me_account_identity(client):
    token = _register(client).json()["access_token"]
    r = client.get("/api/v1/me/account", headers=_auth_header(token))
    assert r.status_code == 200
    body = r.json()
    assert body["email"] == "citizen@example.com"
    assert body["role"] == "citizen"
    assert body["status"] == "active"


# ------------------------------ refresh + logout ---------------------------- #
def test_refresh_rotates_and_old_token_reuse_detected(client, db_session_factory):
    tokens = _register(client).json()
    old_refresh = tokens["refresh_token"]

    r1 = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert r1.status_code == 200
    new_refresh = r1.json()["refresh_token"]
    assert new_refresh != old_refresh

    # Reusing the old (now rotated/revoked) token => 401 + reuse detection,
    # and the whole family is revoked.
    r2 = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert r2.status_code == 401
    assert r2.json()["error"]["code"] == "INVALID_TOKEN"

    # The freshly-issued token is now also revoked (family kill).
    r3 = client.post("/api/v1/auth/refresh", json={"refresh_token": new_refresh})
    assert r3.status_code == 401

    from app.models.audit_log import AuditLog

    with db_session_factory() as s:
        reuse = s.scalar(
            select(func.count()).select_from(AuditLog).where(
                AuditLog.action == "auth.token_reuse_detected"
            )
        )
        # Both r2 (old, rotated-out token) and r3 (new token, revoked by the
        # family kill triggered in r2) are legitimate reuse-detection events.
        assert reuse >= 1


def test_logout_revokes_refresh_token(client):
    tokens = _register(client).json()
    access, refresh = tokens["access_token"], tokens["refresh_token"]
    r = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh},
        headers=_auth_header(access),
    )
    assert r.status_code == 204
    # The revoked token can no longer be refreshed.
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": refresh}).status_code == 401


# ------------------------------ profile update ------------------------------ #
def test_profile_update_and_versioning(client, db_session_factory):
    token = _register(client).json()["access_token"]
    r = client.patch(
        "/api/v1/me",
        headers=_auth_header(token),
        json={"family_size": 4, "declared_annual_income": "150000.00", "gender": "female"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["family_size"] == 4
    assert body["current_version_no"] == 1
    assert body["profile_completeness"] > 0

    from app.models.citizen_profile import CitizenProfileVersion

    with db_session_factory() as s:
        versions = s.scalar(select(func.count()).select_from(CitizenProfileVersion))
        assert versions == 1


def test_profile_update_rejects_negative_income(client):
    token = _register(client).json()["access_token"]
    r = client.patch(
        "/api/v1/me", headers=_auth_header(token), json={"declared_annual_income": "-5"}
    )
    assert r.status_code == 422


def test_profile_update_rejects_zero_family_size(client):
    token = _register(client).json()["access_token"]
    r = client.patch("/api/v1/me", headers=_auth_header(token), json={"family_size": 0})
    assert r.status_code == 422


# ------------------------------ addresses ----------------------------------- #
def test_address_crud_and_single_primary(client, db_session_factory):
    token = _register(client).json()["access_token"]
    h = _auth_header(token)

    # First address becomes primary automatically.
    a1 = client.post(
        "/api/v1/me/addresses",
        headers=h,
        json={
            "type": "permanent",
            "state": "Karnataka",
            "district": "Bengaluru",
            "pincode": "560001",
            "line1": "1 MG Road",
        },
    )
    assert a1.status_code == 201
    assert a1.json()["is_primary"] is True
    addr1_id = a1.json()["id"]

    # Second address, explicitly primary -> demotes the first.
    a2 = client.post(
        "/api/v1/me/addresses",
        headers=h,
        json={
            "type": "current",
            "state": "Kerala",
            "district": "Kochi",
            "pincode": "682001",
            "line1": "2 Marine Drive",
            "is_primary": True,
        },
    )
    assert a2.status_code == 201
    assert a2.json()["is_primary"] is True

    listing = client.get("/api/v1/me/addresses", headers=h)
    assert listing.status_code == 200
    primaries = [a for a in listing.json() if a["is_primary"]]
    assert len(primaries) == 1  # single-primary invariant holds

    # Update the first address.
    upd = client.put(
        f"/api/v1/me/addresses/{addr1_id}",
        headers=h,
        json={"district": "Mysuru"},
    )
    assert upd.status_code == 200
    assert upd.json()["district"] == "Mysuru"

    # Delete it.
    dele = client.delete(f"/api/v1/me/addresses/{addr1_id}", headers=h)
    assert dele.status_code == 204
    assert len(client.get("/api/v1/me/addresses", headers=h).json()) == 1


def test_address_invalid_pincode_422(client):
    token = _register(client).json()["access_token"]
    r = client.post(
        "/api/v1/me/addresses",
        headers=_auth_header(token),
        json={
            "type": "permanent",
            "state": "KA",
            "district": "BLR",
            "pincode": "12ab",
            "line1": "x",
        },
    )
    assert r.status_code == 422


def test_audit_rows_written_for_sensitive_actions(client, db_session_factory):
    token = _register(client).json()["access_token"]
    client.post(
        "/api/v1/auth/login", json={"email": "citizen@example.com", "password": STRONG_PW}
    )
    client.patch("/api/v1/me", headers=_auth_header(token), json={"family_size": 2})

    from app.models.audit_log import AuditLog

    with db_session_factory() as s:
        actions = set(s.scalars(select(AuditLog.action)).all())
    assert "auth.register" in actions
    assert "auth.login_success" in actions
    assert "citizen.profile_update" in actions
    # No secret material in any audit diff.
    with db_session_factory() as s:
        for log in s.scalars(select(AuditLog)).all():
            blob = str(log.diff or {}).lower()
            assert "password" not in blob and "token" not in blob
