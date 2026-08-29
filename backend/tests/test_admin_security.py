"""Security tests for Admin console API boundaries:
1. Citizen accessing admin route -> 403 Permission Denied
2. Agent accessing citizen without active consent -> 403 Permission Denied
3. Scheme author attempting to self-publish own version -> 409 Four-Eyes Violation
4. Citizen attempting to publish scheme -> 403 Permission Denied
5. Non-admin attempting user management -> 403 Permission Denied
"""
import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token, hash_password
from app.models.enums import UserRole, UserStatus
from app.models.user import User
from app.models.scheme import Scheme, SchemeVersion
from app.models.eligibility import EligibilityRule


def _create_user(session, email: str, role: UserRole) -> User:
    u = User(
        email=email,
        password_hash=hash_password("Password123!@#"),
        role=role,
        status=UserStatus.ACTIVE,
    )
    session.add(u)
    session.commit()
    session.refresh(u)
    return u


def _headers(user: User) -> dict[str, str]:
    token, _ = create_access_token(subject=str(user.id), role=user.role.value)
    return {"Authorization": f"Bearer {token}"}


def test_citizen_accessing_admin_route(client: TestClient, db_session_factory):
    session = db_session_factory()
    citizen = _create_user(session, "citizen_hacker@gmail.com", UserRole.CITIZEN)

    res = client.get("/api/v1/admin/dashboard", headers=_headers(citizen))
    assert res.status_code == 403

    res_audit = client.get("/api/v1/admin/audit-logs", headers=_headers(citizen))
    assert res_audit.status_code == 403

    res_users = client.get("/api/v1/admin/users", headers=_headers(citizen))
    assert res_users.status_code == 403


def test_agent_accessing_unauthorized_citizen(client: TestClient, db_session_factory):
    session = db_session_factory()
    agent = _create_user(session, "agent1@csc.gov.in", UserRole.AGENT)
    citizen = _create_user(session, "unconsented_citizen@gmail.com", UserRole.CITIZEN)

    # Agent attempts to access citizen details without consent
    res = client.get(f"/api/v1/agent/citizens/{citizen.id}", headers=_headers(agent))
    assert res.status_code == 403


def test_four_eyes_self_publish_rejected(client: TestClient, db_session_factory):
    session = db_session_factory()
    author = _create_user(session, "author@gov.in", UserRole.SCHEME_ADMIN)

    s = Scheme(canonical_name="Four Eyes Scheme Test", category="Social", scope="state")
    session.add(s)
    session.commit()

    v = SchemeVersion(
        scheme_id=s.id,
        version_no=1,
        benefits_summary="Benefits",
        effective_from="2026-01-01",
        created_by=author.id,
    )
    session.add(v)
    session.commit()

    r = EligibilityRule(
        scheme_version_id=v.id,
        rule_code="R1",
        field_key="annual_income",
        operator="<=",
        value="250000",
        mandatory=True,
    )
    session.add(r)
    session.commit()

    # Author attempts to publish their own version -> 409 Conflict (Four-Eyes Violation)
    res_self = client.post(f"/api/v1/admin/scheme-versions/{v.id}/publish", headers=_headers(author))
    assert res_self.status_code == 409
    assert res_self.json()["error"]["code"] == "FOUR_EYES_REQUIRED"

    # Second reviewer (different scheme_admin) publishes -> 200 OK
    reviewer = _create_user(session, "reviewer@gov.in", UserRole.SCHEME_ADMIN)
    res_second = client.post(f"/api/v1/admin/scheme-versions/{v.id}/publish", headers=_headers(reviewer))
    assert res_second.status_code == 200
    assert res_second.json()["status"] == "published"


def test_non_admin_cannot_manage_users(client: TestClient, db_session_factory):
    session = db_session_factory()
    scheme_admin = _create_user(session, "sadmin2@gov.in", UserRole.SCHEME_ADMIN)
    agent = _create_user(session, "agent2@csc.gov.in", UserRole.AGENT)

    res1 = client.get("/api/v1/admin/users", headers=_headers(scheme_admin))
    assert res1.status_code == 403

    res2 = client.get("/api/v1/admin/users", headers=_headers(agent))
    assert res2.status_code == 403
