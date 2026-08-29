"""Security + API tests: notification object-level authorization + in-app
endpoints + preferences (prompt §16, §18, §19, §42)."""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select

from app.models.enums import DomainEventType
from app.modules.notifications.events import AggregateType, EventEnvelope
from app.modules.notifications.service import OutboxDispatcher, OutboxWriter

pytestmark = pytest.mark.security

STRONG_PW = "CorrectHorse9Battery!"


def _register(client, email):
    return client.post("/api/v1/auth/register", json={"email": email, "password": STRONG_PW}).json()["access_token"]


def _h(t):
    return {"Authorization": f"Bearer {t}"}


def _profile_id(db_session_factory, email):
    from app.models.citizen_profile import CitizenProfile
    from app.models.user import User

    with db_session_factory() as s:
        uid = s.scalar(select(User.id).where(User.email == email))
        return uid, s.scalar(select(CitizenProfile.id).where(CitizenProfile.user_id == uid))


def _emit_and_drain(db_session_factory, profile_id):
    with db_session_factory() as s:
        OutboxWriter(s).enqueue(EventEnvelope(
            event_type=DomainEventType.APPLICATION_SUBMITTED,
            aggregate_type=AggregateType.APPLICATION, aggregate_id=uuid.uuid4(),
            payload={"citizen_profile_id": str(profile_id), "application_number": "CL-X"},
        ))
        s.commit()
    with db_session_factory() as s:
        OutboxDispatcher(session=s).dispatch_pending()


def _first_notification_id(db_session_factory, user_id):
    from app.models.notification import Notification

    with db_session_factory() as s:
        return s.scalar(select(Notification.id).where(Notification.recipient_user_id == user_id))


# ------------------------------ in-app feed --------------------------------- #
def test_list_unread_count_and_read_flow(client, db_session_factory):
    token = _register(client, "n1@example.com")
    uid, pid = _profile_id(db_session_factory, "n1@example.com")
    _emit_and_drain(db_session_factory, pid)

    page = client.get("/api/v1/notifications", headers=_h(token)).json()
    assert page["total"] >= 1 and page["items"]
    nid = page["items"][0]["id"]
    assert client.get("/api/v1/notifications/unread-count", headers=_h(token)).json()["unread"] >= 1

    r = client.post(f"/api/v1/notifications/{nid}/read", headers=_h(token))
    assert r.status_code == 200 and r.json()["read"] is True

    # read-all clears the rest.
    client.post("/api/v1/notifications/read-all", headers=_h(token))
    assert client.get("/api/v1/notifications/unread-count", headers=_h(token)).json()["unread"] == 0


def test_pagination(client, db_session_factory):
    token = _register(client, "n2@example.com")
    uid, pid = _profile_id(db_session_factory, "n2@example.com")
    for _ in range(3):
        _emit_and_drain(db_session_factory, pid)
    page = client.get("/api/v1/notifications?page=1&page_size=2", headers=_h(token)).json()
    assert len(page["items"]) == 2 and page["total"] == 3


# ------------------------------ object-level auth (§19) --------------------- #
def test_citizen_cannot_read_another_users_notification(client, db_session_factory):
    token_a = _register(client, "own@example.com")
    uid_a, pid_a = _profile_id(db_session_factory, "own@example.com")
    _emit_and_drain(db_session_factory, pid_a)
    nid = _first_notification_id(db_session_factory, uid_a)

    token_b = _register(client, "other@example.com")
    # B cannot see A's notification in their feed.
    page_b = client.get("/api/v1/notifications", headers=_h(token_b)).json()
    assert all(item["id"] != str(nid) for item in page_b["items"])
    # B cannot mark A's notification read -> 404 (no existence disclosure).
    r = client.post(f"/api/v1/notifications/{nid}/read", headers=_h(token_b))
    assert r.status_code == 404


def test_unauthenticated_notifications_rejected(client):
    assert client.get("/api/v1/notifications").status_code == 401
    assert client.get("/api/v1/notifications/unread-count").status_code == 401
    assert client.post(f"/api/v1/notifications/{uuid.uuid4()}/read").status_code == 401
    assert client.get("/api/v1/me/notification-preferences").status_code == 401


# ------------------------------ preferences (§16, §17) ---------------------- #
def test_default_preferences_are_safe(client, db_session_factory):
    token = _register(client, "pf1@example.com")
    prefs = client.get("/api/v1/me/notification-preferences", headers=_h(token)).json()
    assert prefs["application_updates"] is True
    assert prefs["document_updates"] is True
    assert prefs["security_alerts"] is True
    assert prefs["in_app_enabled"] is True
    # No marketing opt-in: email/sms default off.
    assert prefs["email_enabled"] is False and prefs["sms_enabled"] is False


def test_update_preferences_persists(client, db_session_factory):
    token = _register(client, "pf2@example.com")
    r = client.put("/api/v1/me/notification-preferences", headers=_h(token),
                   json={"email_enabled": True, "application_updates": False})
    assert r.status_code == 200
    body = r.json()
    assert body["email_enabled"] is True and body["application_updates"] is False
    # Persisted across requests.
    again = client.get("/api/v1/me/notification-preferences", headers=_h(token)).json()
    assert again["email_enabled"] is True and again["application_updates"] is False


def test_security_alerts_cannot_be_disabled(client, db_session_factory):
    token = _register(client, "pf3@example.com")
    # Attempting to send security_alerts is rejected (extra field forbidden).
    r = client.put("/api/v1/me/notification-preferences", headers=_h(token),
                   json={"security_alerts": False})
    assert r.status_code == 422  # additionalProperties: false
    # And it remains True.
    prefs = client.get("/api/v1/me/notification-preferences", headers=_h(token)).json()
    assert prefs["security_alerts"] is True
