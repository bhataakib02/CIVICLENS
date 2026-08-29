"""Tests for admin backend API endpoints:
- GET /admin/dashboard
- GET /admin/audit-logs
- GET /admin/citizens
- GET /admin/citizens/{user_id}
- GET /admin/citizens/{user_id}/consents
- GET /admin/notifications
- POST /admin/notifications/{id}/retry
- GET /admin/users
- POST /admin/users
- PATCH /admin/users/{user_id}
- GET /admin/system-health
- GET /agent/citizens
- POST /admin/scheme-versions/{id}/submit-for-review
"""
import uuid
import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token, hash_password
from app.models.enums import NotificationChannel, NotificationStatus, UserRole, UserStatus
from app.models.user import User
from app.models.notification import Notification
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


def test_admin_dashboard(client: TestClient, db_session_factory):
    session = db_session_factory()
    admin = _create_user(session, "admin1@gov.in", UserRole.ADMIN)
    res = client.get("/api/v1/admin/dashboard", headers=_headers(admin))
    assert res.status_code == 200
    data = res.json()
    assert "applications_pending_review" in data
    assert "total_citizens" in data


def test_admin_audit_logs(client: TestClient, db_session_factory):
    session = db_session_factory()
    admin = _create_user(session, "admin2@gov.in", UserRole.ADMIN)
    res = client.get("/api/v1/admin/audit-logs", headers=_headers(admin))
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data


def test_admin_citizens_search(client: TestClient, db_session_factory):
    session = db_session_factory()
    admin = _create_user(session, "admin3@gov.in", UserRole.ADMIN)
    citizen = _create_user(session, "citizen1@gmail.com", UserRole.CITIZEN)

    res = client.get("/api/v1/admin/citizens?q=citizen1", headers=_headers(admin))
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1
    assert data["items"][0]["email"] == "citizen1@gmail.com"


def test_admin_citizen_detail(client: TestClient, db_session_factory):
    session = db_session_factory()
    admin = _create_user(session, "admin4@gov.in", UserRole.ADMIN)
    citizen = _create_user(session, "citizen2@gmail.com", UserRole.CITIZEN)

    res = client.get(f"/api/v1/admin/citizens/{citizen.id}", headers=_headers(admin))
    assert res.status_code == 200
    data = res.json()
    assert data["user_id"] == str(citizen.id)
    assert data["email"] == "citizen2@gmail.com"


def test_admin_notifications_ops_and_retry(client: TestClient, db_session_factory):
    session = db_session_factory()
    admin = _create_user(session, "admin5@gov.in", UserRole.ADMIN)

    # Create failed notification
    n = Notification(
        user_id=admin.id,
        channel=NotificationChannel.EMAIL,
        category="status_change",
        status=NotificationStatus.FAILED,
        title="Test Failed Notif",
        body="Body",
        failure_code="TRANSIENT_PROVIDER_ERROR",
        attempts=1,
    )
    session.add(n)
    session.commit()

    # List
    res = client.get("/api/v1/admin/notifications?status=failed", headers=_headers(admin))
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1

    # Retry
    res_retry = client.post(f"/api/v1/admin/notifications/{n.id}/retry", headers=_headers(admin))
    assert res_retry.status_code == 200
    assert res_retry.json()["status"] == "pending"


def test_admin_user_management(client: TestClient, db_session_factory):
    session = db_session_factory()
    admin = _create_user(session, "admin6@gov.in", UserRole.ADMIN)

    # Provision user
    res_create = client.post(
        "/api/v1/admin/users",
        headers=_headers(admin),
        json={"email": "agent_new@gov.in", "password": "Password123!@#", "role": "agent"},
    )
    assert res_create.status_code == 201
    new_user_id = res_create.json()["id"]

    # List users
    res_list = client.get("/api/v1/admin/users", headers=_headers(admin))
    assert res_list.status_code == 200
    assert res_list.json()["total"] >= 2

    # Suspend user
    res_update = client.patch(
        f"/api/v1/admin/users/{new_user_id}",
        headers=_headers(admin),
        json={"status": "suspended"},
    )
    assert res_update.status_code == 200
    assert res_update.json()["status"] == "suspended"


def test_admin_system_health(client: TestClient, db_session_factory):
    session = db_session_factory()
    admin = _create_user(session, "admin7@gov.in", UserRole.ADMIN)
    res = client.get("/api/v1/admin/system-health", headers=_headers(admin))
    assert res.status_code == 200
    assert res.json()["database"] == "ok"


def test_scheme_submit_for_review(client: TestClient, db_session_factory):
    session = db_session_factory()
    scheme_admin = _create_user(session, "sadmin@gov.in", UserRole.SCHEME_ADMIN)

    s = Scheme(canonical_name="Test Scheme Submit", category="Agri", scope="central")
    session.add(s)
    session.commit()

    v = SchemeVersion(scheme_id=s.id, version_no=1, benefits_summary="Benefits", effective_from="2026-01-01")
    session.add(v)
    session.commit()

    # Must fail with no rules
    res = client.post(f"/api/v1/admin/scheme-versions/{v.id}/submit-for-review", headers=_headers(scheme_admin))
    assert res.status_code == 409

    # Add rule
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

    # Submit for review
    res_ok = client.post(f"/api/v1/admin/scheme-versions/{v.id}/submit-for-review", headers=_headers(scheme_admin))
    assert res_ok.status_code == 200
    assert res_ok.json()["status"] == "in_review"
