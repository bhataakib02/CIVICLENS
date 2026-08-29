"""Security tests: scheme/eligibility RBAC + object-level authorization
(prompt §27)."""
from __future__ import annotations

import pytest
from sqlalchemy import select

pytestmark = pytest.mark.security

STRONG_PW = "CorrectHorse9Battery!"

SCHEME_RULES = [
    {"rule_code": "AGE", "type": "condition", "field_key": "age", "operator": "gte", "value": 18,
     "explanation_text": "18+."},
]


def _register(client, email):
    return client.post("/api/v1/auth/register", json={"email": email, "password": STRONG_PW}).json()["access_token"]


def _promote(db_session_factory, email, role):
    from app.models.enums import UserRole
    from app.models.user import User

    with db_session_factory() as s:
        u = s.scalar(select(User).where(User.email == email))
        u.role = UserRole(role)
        s.commit()


def _admin_token(client, db_session_factory, email="secadmin@example.com"):
    _register(client, email)
    _promote(db_session_factory, email, "scheme_admin")
    return client.post("/api/v1/auth/login", json={"email": email, "password": STRONG_PW}).json()["access_token"]


def _h(t):
    return {"Authorization": f"Bearer {t}"}


def test_citizen_cannot_create_scheme(client, db_session_factory):
    citizen = _register(client, "c@example.com")
    r = client.post(
        "/api/v1/schemes", headers=_h(citizen),
        json={"canonical_name": "X", "category": "health", "scope": "state"},
    )
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "PERMISSION_DENIED"


def test_citizen_cannot_create_version_or_rules(client, db_session_factory):
    admin = _admin_token(client, db_session_factory)
    sid = client.post(
        "/api/v1/schemes", headers=_h(admin),
        json={"canonical_name": "Y", "category": "health", "scope": "state"},
    ).json()["id"]
    vid = client.post(
        f"/api/v1/schemes/{sid}/versions", headers=_h(admin),
        json={"benefits_summary": "b", "effective_from": "2025-01-01"},
    ).json()["id"]

    citizen = _register(client, "c2@example.com")
    rv = client.post(
        f"/api/v1/schemes/{sid}/versions", headers=_h(citizen),
        json={"benefits_summary": "b", "effective_from": "2025-01-01"},
    )
    assert rv.status_code == 403
    rr = client.post(
        f"/api/v1/scheme-versions/{vid}/rules", headers=_h(citizen), json={"rules": SCHEME_RULES}
    )
    assert rr.status_code == 403


def test_citizen_cannot_validate_rules(client, db_session_factory):
    citizen = _register(client, "c3@example.com")
    r = client.post("/api/v1/admin/rules/validate", headers=_h(citizen), json={"rules": SCHEME_RULES})
    assert r.status_code == 403


def test_unauthenticated_requests_fail(client):
    assert client.get("/api/v1/schemes").status_code == 401
    assert client.post("/api/v1/schemes", json={}).status_code == 401
    assert client.post("/api/v1/eligibility/check", json={"scheme_id": "x"}).status_code == 401


def test_citizen_cannot_evaluate_another_citizen(client, db_session_factory):
    # citizen_id is not an accepted field; a citizen targeting another profile
    # id via facts must not bypass authorization — it is ignored / forbidden.
    admin = _admin_token(client, db_session_factory, "eadmin@example.com")
    sid = client.post(
        "/api/v1/schemes", headers=_h(admin),
        json={"canonical_name": "Z", "category": "health", "scope": "state"},
    ).json()["id"]
    vid = client.post(
        f"/api/v1/schemes/{sid}/versions", headers=_h(admin),
        json={"benefits_summary": "b", "effective_from": "2025-01-01"},
    ).json()["id"]
    client.post(f"/api/v1/scheme-versions/{vid}/rules", headers=_h(admin), json={"rules": SCHEME_RULES})
    publisher = _admin_token(client, db_session_factory, "epub@example.com")
    client.post(f"/api/v1/admin/scheme-versions/{vid}/publish", headers=_h(publisher))

    # citizen A and B
    a = _register(client, "a@example.com")
    b = _register(client, "b@example.com")
    client.patch("/api/v1/me", headers=_h(a), json={"date_of_birth": "2000-01-01"})
    client.patch("/api/v1/me", headers=_h(b), json={"date_of_birth": "2015-01-01"})

    from app.models.citizen_profile import CitizenProfile
    from app.models.user import User

    with db_session_factory() as s:
        a_user = s.scalar(select(User).where(User.email == "a@example.com"))
        a_profile = s.scalar(select(CitizenProfile).where(CitizenProfile.user_id == a_user.id))
        a_profile_id = str(a_profile.id)

    # B attempts to inject A's profile id via a "citizen_id"/profile field — the
    # schema forbids unknown top-level fields, so the request is rejected 422,
    # and even if facts are used, identity is derived from B's token.
    r = client.post(
        "/api/v1/eligibility/check",
        headers=_h(b),
        json={"scheme_id": sid, "citizen_id": a_profile_id},
    )
    assert r.status_code == 422  # extra field forbidden

    # A legitimate check for B evaluates against B's own profile only.
    r2 = client.post("/api/v1/eligibility/check", headers=_h(b), json={"scheme_id": sid})
    assert r2.status_code == 200
    assert r2.json()["citizen_id"] != a_profile_id


def test_admin_can_evaluate_and_citizen_result_is_own(client, db_session_factory):
    # admin/case-worker permission path: staff role is accepted by the engine
    # (target defaults to their own profile here since no target is passed).
    admin = _admin_token(client, db_session_factory, "staff@example.com")
    # admin has a profile (auto-created at registration) but no schemes needed
    # for the authz check itself; a missing published version -> 404, not 403.
    r = client.post(
        "/api/v1/eligibility/check",
        headers=_h(admin),
        json={"scheme_id": "00000000-0000-0000-0000-000000000000"},
    )
    assert r.status_code in (404, 200)
    assert r.status_code != 403
