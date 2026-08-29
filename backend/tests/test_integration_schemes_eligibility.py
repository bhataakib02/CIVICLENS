"""Integration tests: scheme catalog + versioning + lifecycle + eligibility
against a real PostgreSQL (pgserver). Asserts status, schema, DB state, and
authorization behavior."""
from __future__ import annotations

import pytest
from sqlalchemy import select

pytestmark = pytest.mark.integration

STRONG_PW = "CorrectHorse9Battery!"


# --------------------------- helpers ---------------------------------------- #
def _register(client, email):
    r = client.post("/api/v1/auth/register", json={"email": email, "password": STRONG_PW})
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


def _promote(db_session_factory, email, role):
    from app.models.enums import UserRole
    from app.models.user import User

    with db_session_factory() as s:
        u = s.scalar(select(User).where(User.email == email))
        u.role = UserRole(role)
        s.commit()


def _admin_token(client, db_session_factory, email="admin@example.com"):
    _register(client, email)
    _promote(db_session_factory, email, "scheme_admin")
    # re-login so the JWT carries the new role
    r = client.post("/api/v1/auth/login", json={"email": email, "password": STRONG_PW})
    return r.json()["access_token"]


def _h(token):
    return {"Authorization": f"Bearer {token}"}


SCHEME_A_RULES = [
    {"rule_code": "AGE", "type": "condition", "field_key": "age", "operator": "gte", "value": 18,
     "explanation_text": "You are at least 18."},
    {"rule_code": "INCOME", "type": "condition", "field_key": "declared_annual_income",
     "operator": "lte", "value": 250000, "explanation_text": "Income within the limit."},
    {"rule_code": "STATE", "type": "condition", "field_key": "state", "operator": "eq",
     "value": "West Bengal", "explanation_text": "You live in West Bengal."},
]


def _create_published_scheme(client, admin, author_admin_token=None):
    """Create scheme + version + rules, then publish with a DIFFERENT admin
    (four-eyes). Returns (scheme_id, version_id)."""
    sc = client.post(
        "/api/v1/schemes",
        headers=_h(admin),
        json={"canonical_name": "Test Income Support", "category": "social_security", "scope": "state"},
    )
    assert sc.status_code == 201, sc.text
    scheme_id = sc.json()["id"]

    ver = client.post(
        f"/api/v1/schemes/{scheme_id}/versions",
        headers=_h(admin),
        json={"benefits_summary": "Demo benefits", "effective_from": "2025-01-01"},
    )
    assert ver.status_code == 201, ver.text
    version_id = ver.json()["id"]

    rules = client.post(
        f"/api/v1/scheme-versions/{version_id}/rules", headers=_h(admin), json={"rules": SCHEME_A_RULES}
    )
    assert rules.status_code == 201, rules.text
    return scheme_id, version_id


# ------------------------------ scheme CRUD --------------------------------- #
def test_scheme_create_and_get_and_search(client, db_session_factory):
    admin = _admin_token(client, db_session_factory)
    sc = client.post(
        "/api/v1/schemes",
        headers=_h(admin),
        json={"canonical_name": "Farmer Support", "category": "agriculture", "scope": "central"},
    )
    assert sc.status_code == 201
    sid = sc.json()["id"]

    detail = client.get(f"/api/v1/schemes/{sid}", headers=_h(admin))
    assert detail.status_code == 200
    assert detail.json()["canonical_name"] == "Farmer Support"

    page = client.get("/api/v1/schemes?q=Farmer&category=agriculture&scope=central", headers=_h(admin))
    assert page.status_code == 200
    body = page.json()
    assert body["total"] >= 1
    assert any(i["canonical_name"] == "Farmer Support" for i in body["items"])
    assert body["page"] == 1 and body["page_size"] == 20


def test_scheme_pagination(client, db_session_factory):
    admin = _admin_token(client, db_session_factory)
    for i in range(3):
        client.post(
            "/api/v1/schemes", headers=_h(admin),
            json={"canonical_name": f"S{i}", "category": "education", "scope": "central"},
        )
    p1 = client.get("/api/v1/schemes?page=1&page_size=2", headers=_h(admin)).json()
    assert len(p1["items"]) == 2
    assert p1["total"] >= 3


# --------------------------- versioning + lifecycle ------------------------- #
def test_version_lifecycle_and_four_eyes(client, db_session_factory):
    author = _admin_token(client, db_session_factory, "author@example.com")
    scheme_id, version_id = _create_published_scheme(client, author)

    # Same admin (author) cannot publish (four-eyes).
    r_self = client.post(f"/api/v1/admin/scheme-versions/{version_id}/publish", headers=_h(author))
    assert r_self.status_code == 409
    assert r_self.json()["error"]["code"] == "FOUR_EYES_REQUIRED"

    # A different admin publishes successfully.
    publisher = _admin_token(client, db_session_factory, "publisher@example.com")
    r_pub = client.post(f"/api/v1/admin/scheme-versions/{version_id}/publish", headers=_h(publisher))
    assert r_pub.status_code == 200, r_pub.text
    assert r_pub.json()["status"] == "published"

    # Now the scheme detail exposes a current published version.
    detail = client.get(f"/api/v1/schemes/{scheme_id}", headers=_h(author))
    assert detail.json()["scheme_version_id"] == version_id

    # Superseded lifecycle; cannot re-publish a superseded version.
    r_sup = client.post(f"/api/v1/admin/scheme-versions/{version_id}/supersede", headers=_h(publisher))
    assert r_sup.status_code == 200
    assert r_sup.json()["status"] == "superseded"
    r_republish = client.post(
        f"/api/v1/admin/scheme-versions/{version_id}/publish", headers=_h(publisher)
    )
    assert r_republish.status_code == 409  # superseded -> published is illegal


def test_publish_blocked_without_rules(client, db_session_factory):
    author = _admin_token(client, db_session_factory, "author2@example.com")
    sc = client.post(
        "/api/v1/schemes", headers=_h(author),
        json={"canonical_name": "NoRules", "category": "health", "scope": "state"},
    )
    sid = sc.json()["id"]
    ver = client.post(
        f"/api/v1/schemes/{sid}/versions", headers=_h(author),
        json={"benefits_summary": "x", "effective_from": "2025-01-01"},
    )
    vid = ver.json()["id"]
    publisher = _admin_token(client, db_session_factory, "publisher2@example.com")
    r = client.post(f"/api/v1/admin/scheme-versions/{vid}/publish", headers=_h(publisher))
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "VERSION_HAS_NO_RULES"


def test_rules_immutable_after_publish(client, db_session_factory):
    author = _admin_token(client, db_session_factory, "author3@example.com")
    scheme_id, version_id = _create_published_scheme(client, author)
    publisher = _admin_token(client, db_session_factory, "publisher3@example.com")
    client.post(f"/api/v1/admin/scheme-versions/{version_id}/publish", headers=_h(publisher))
    # Editing rules on a published version is rejected.
    r = client.post(
        f"/api/v1/scheme-versions/{version_id}/rules", headers=_h(author), json={"rules": SCHEME_A_RULES}
    )
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "VERSION_IMMUTABLE"


def test_rule_validation_endpoint(client, db_session_factory):
    admin = _admin_token(client, db_session_factory)
    ok = client.post("/api/v1/admin/rules/validate", headers=_h(admin), json={"rules": SCHEME_A_RULES})
    assert ok.status_code == 200
    assert ok.json()["valid"] is True
    assert ok.json()["normalized_rule_count"] == 3

    bad = client.post(
        "/api/v1/admin/rules/validate",
        headers=_h(admin),
        json={"rules": [{"rule_type": "NUMERIC_COMPARISON", "expression": {"field": "citizen.age", "operator": "DROP DATABASE"}}]},
    )
    assert bad.status_code == 422


# ------------------------------ eligibility --------------------------------- #
def _setup_scheme_and_citizen(client, db_session_factory, *, income, state, dob="2000-01-01"):
    author = _admin_token(client, db_session_factory, "eauthor@example.com")
    scheme_id, version_id = _create_published_scheme(client, author)
    publisher = _admin_token(client, db_session_factory, "epublisher@example.com")
    client.post(f"/api/v1/admin/scheme-versions/{version_id}/publish", headers=_h(publisher))

    citizen = _register(client, "ecitizen@example.com")
    patch = {"date_of_birth": dob}
    if income is not None:
        patch["declared_annual_income"] = str(income)
    client.patch("/api/v1/me", headers=_h(citizen), json=patch)
    if state:
        client.post(
            "/api/v1/me/addresses", headers=_h(citizen),
            json={"type": "current", "state": state, "district": "Kolkata", "pincode": "700001", "line1": "1 Rd"},
        )
    return scheme_id, version_id, citizen


def test_eligibility_eligible_persisted(client, db_session_factory):
    scheme_id, version_id, citizen = _setup_scheme_and_citizen(
        client, db_session_factory, income=100000, state="West Bengal"
    )
    r = client.post("/api/v1/eligibility/check", headers=_h(citizen), json={"scheme_id": scheme_id})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["result"] == "eligible"
    assert body["decision"] == "eligible"
    assert body["engine_version"] == "1.0.0"
    assert set(body["matched_rules"]) == {"AGE", "INCOME", "STATE"}
    assert body["scheme_version_id"] == version_id
    assert "You are at least 18." in body["explanation"]

    from app.models.eligibility import EligibilityCheck

    with db_session_factory() as s:
        rows = s.scalars(select(EligibilityCheck)).all()
        assert len(rows) == 1
        assert rows[0].engine_version == "1.0.0"
        assert rows[0].result == "eligible"


def test_eligibility_not_eligible(client, db_session_factory):
    scheme_id, _v, citizen = _setup_scheme_and_citizen(
        client, db_session_factory, income=900000, state="West Bengal"
    )
    r = client.post("/api/v1/eligibility/check", headers=_h(citizen), json={"scheme_id": scheme_id})
    assert r.json()["result"] == "not_eligible"
    assert "INCOME" in r.json()["failed_rules"]


def test_eligibility_insufficient_data(client, db_session_factory):
    scheme_id, _v, citizen = _setup_scheme_and_citizen(
        client, db_session_factory, income=None, state="West Bengal"
    )
    r = client.post("/api/v1/eligibility/check", headers=_h(citizen), json={"scheme_id": scheme_id})
    body = r.json()
    assert body["result"] == "insufficient_data"
    assert any(m["field"] == "declared_annual_income" for m in body["missing_information"])


def test_eligibility_conflicting_information(client, db_session_factory):
    scheme_id, _v, citizen = _setup_scheme_and_citizen(
        client, db_session_factory, income=200000, state="West Bengal"
    )
    # Supply a conflicting income via request facts.
    r = client.post(
        "/api/v1/eligibility/check",
        headers=_h(citizen),
        json={"scheme_id": scheme_id, "facts": {"citizen.annual_income": 350000}},
    )
    body = r.json()
    assert body["result"] == "insufficient_data"
    assert any(c["field"] == "declared_annual_income" for c in body["conflicts"])


def test_eligibility_idempotency(client, db_session_factory):
    scheme_id, _v, citizen = _setup_scheme_and_citizen(
        client, db_session_factory, income=100000, state="West Bengal"
    )
    headers = {**_h(citizen), "Idempotency-Key": "abc-123"}
    r1 = client.post("/api/v1/eligibility/check", headers=headers, json={"scheme_id": scheme_id})
    r2 = client.post("/api/v1/eligibility/check", headers=headers, json={"scheme_id": scheme_id})
    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.json()["id"] == r2.json()["id"]  # same persisted row, no duplicate

    from app.models.eligibility import EligibilityCheck

    with db_session_factory() as s:
        assert len(s.scalars(select(EligibilityCheck)).all()) == 1


def test_eligibility_determinism_repeated(client, db_session_factory):
    scheme_id, _v, citizen = _setup_scheme_and_citizen(
        client, db_session_factory, income=100000, state="West Bengal"
    )
    outcomes = []
    for _ in range(3):
        r = client.post("/api/v1/eligibility/check", headers=_h(citizen), json={"scheme_id": scheme_id})
        b = r.json()
        outcomes.append((b["result"], tuple(sorted(b["matched_rules"])), tuple(sorted(b["failed_rules"]))))
    assert len(set(outcomes)) == 1


def test_seed_data_runs(client, db_session_factory):
    # The seed script must run against the real DB and produce demo schemes.
    from app.seeds.seed_demo import seed

    with db_session_factory() as s:
        summary = seed(s)
    assert summary["scheme_a_version_id"]

    from app.models.scheme import Scheme

    with db_session_factory() as s:
        codes = set(s.scalars(select(Scheme.code)).all())
    assert {"CIVIC-DEMO-001", "CIVIC-DEMO-002", "CIVIC-DEMO-003"} <= codes
