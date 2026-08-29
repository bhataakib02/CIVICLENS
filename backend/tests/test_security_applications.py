"""Security tests: application object-level authorization + RBAC (prompt §49)."""
from __future__ import annotations

import uuid
from datetime import date

import pytest
from sqlalchemy import select

pytestmark = pytest.mark.security

STRONG_PW = "CorrectHorse9Battery!"


def _register(client, email):
    return client.post("/api/v1/auth/register", json={"email": email, "password": STRONG_PW}).json()["access_token"]


def _promote(db_session_factory, email, role):
    from app.models.enums import UserRole
    from app.models.user import User

    with db_session_factory() as s:
        u = s.scalar(select(User).where(User.email == email))
        u.role = UserRole(role)
        s.commit()


def _login(client, email):
    return client.post("/api/v1/auth/login", json={"email": email, "password": STRONG_PW}).json()["access_token"]


def _h(t):
    return {"Authorization": f"Bearer {t}"}


def _scheme_version(db_session_factory):
    from app.models.eligibility import EligibilityRule
    from app.models.scheme import Scheme, SchemeVersion

    with db_session_factory() as s:
        scheme = Scheme(canonical_name="Sec", category="employment", scope="central")
        s.add(scheme); s.flush()
        v = SchemeVersion(scheme_id=scheme.id, version_no=1, status="published",
                          benefits_summary="b", effective_from=date(2025, 1, 1))
        s.add(v); s.flush()
        s.add(EligibilityRule(scheme_version_id=v.id, rule_code="INCOME", field_key="declared_annual_income",
                              operator="lte", value=250000, mandatory=True, sort_order=0,
                              explanation_text="x"))
        s.commit()
        return str(v.id)


def _eligible_app(client, db_session_factory, email):
    version_id = _scheme_version(db_session_factory)
    token = _register(client, email)
    client.patch("/api/v1/me", headers=_h(token), json={"declared_annual_income": "100000"})
    app_id = client.post("/api/v1/applications", headers=_h(token), json={"scheme_version_id": version_id}).json()["id"]
    return token, app_id


def test_citizen_cannot_access_another_application(client, db_session_factory):
    token_a, app_a = _eligible_app(client, db_session_factory, "seca@example.com")
    token_b = _register(client, "secb@example.com")
    r = client.get(f"/api/v1/applications/{app_a}", headers=_h(token_b))
    assert r.status_code == 404  # no existence disclosure


def test_citizen_cannot_review_or_approve(client, db_session_factory):
    token_a, app_a = _eligible_app(client, db_session_factory, "secc@example.com")
    r = client.post(f"/api/v1/applications/{app_a}/review", headers=_h(token_a),
                    json={"action": "approve", "reason": "self approve"})
    assert r.status_code == 403


def test_citizen_cannot_assign(client, db_session_factory):
    token_a, app_a = _eligible_app(client, db_session_factory, "secd@example.com")
    r = client.post(f"/api/v1/applications/{app_a}/assign", headers=_h(token_a),
                    json={"case_worker_id": str(uuid.uuid4())})
    assert r.status_code == 403


def test_case_worker_cannot_access_unassigned(client, db_session_factory):
    token_a, app_a = _eligible_app(client, db_session_factory, "sece@example.com")
    _register(client, "cwx@example.com"); _promote(db_session_factory, "cwx@example.com", "agent")
    cw = _login(client, "cwx@example.com")
    # Not assigned -> cannot see it.
    assert client.get(f"/api/v1/applications/{app_a}", headers=_h(cw)).status_code == 404
    # And cannot review it.
    assert client.post(f"/api/v1/applications/{app_a}/review", headers=_h(cw),
                       json={"action": "approve", "reason": "x"}).status_code == 403


def test_case_worker_list_only_assigned(client, db_session_factory):
    token_a, app_a = _eligible_app(client, db_session_factory, "secf@example.com")
    _register(client, "cwy@example.com"); _promote(db_session_factory, "cwy@example.com", "agent")
    cw = _login(client, "cwy@example.com")
    listing = client.get("/api/v1/applications", headers=_h(cw)).json()
    assert all(item["id"] != app_a for item in listing["items"])  # unassigned not visible


def test_unauthenticated_application_access_fails(client):
    assert client.get("/api/v1/applications").status_code == 401
    assert client.post("/api/v1/applications", json={}).status_code == 401
    assert client.get(f"/api/v1/applications/{uuid.uuid4()}").status_code == 401


def test_citizen_cannot_change_scheme_version_after_create(client, db_session_factory):
    # There is no endpoint to mutate scheme_version_id; the field is not in any
    # request schema. Confirm create forbids extra fields (immutability by design).
    version_id = _scheme_version(db_session_factory)
    token = _register(client, "secg@example.com")
    client.patch("/api/v1/me", headers=_h(token), json={"declared_annual_income": "100000"})
    r = client.post("/api/v1/applications", headers=_h(token),
                    json={"scheme_version_id": version_id, "eligibility_snapshot": {"decision": "eligible"}})
    assert r.status_code == 422  # extra field forbidden -> cannot inject snapshot/version
