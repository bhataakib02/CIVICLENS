"""Real-time WebSocket tests (prompt §20, §21, §22, §42).

Authenticated connect, unauthenticated rejection, heartbeat, event delivery to a
connected user, and clean disconnect. Uses the in-memory pub/sub backend (dev)."""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select

from app.models.enums import DomainEventType
from app.modules.notifications.events import AggregateType, EventEnvelope
from app.modules.notifications.service import OutboxDispatcher, OutboxWriter

pytestmark = pytest.mark.integration

STRONG_PW = "CorrectHorse9Battery!"


def _register(client, email):
    return client.post("/api/v1/auth/register", json={"email": email, "password": STRONG_PW}).json()["access_token"]


def _profile_id(db_session_factory, email):
    from app.models.citizen_profile import CitizenProfile
    from app.models.user import User

    with db_session_factory() as s:
        uid = s.scalar(select(User.id).where(User.email == email))
        return uid, s.scalar(select(CitizenProfile.id).where(CitizenProfile.user_id == uid))


def test_ws_requires_authentication(client, db_session_factory):
    from starlette.websockets import WebSocketDisconnect

    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/api/v1/realtime") as ws:
            ws.send_json({"type": "notauth"})
            ws.receive_json()


def test_ws_rejects_invalid_token(client, db_session_factory):
    from starlette.websockets import WebSocketDisconnect

    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/api/v1/realtime?token=not-a-real-token") as ws:
            ws.receive_json()


def test_ws_authenticated_connect_and_heartbeat(client, db_session_factory):
    token = _register(client, "rt1@example.com")
    with client.websocket_connect(f"/api/v1/realtime?token={token}") as ws:
        assert ws.receive_json() == {"type": "connected"}
        ws.send_json({"type": "ping"})
        assert ws.receive_json() == {"type": "pong"}


def test_ws_auth_via_first_message(client, db_session_factory):
    token = _register(client, "rt2@example.com")
    with client.websocket_connect("/api/v1/realtime") as ws:
        ws.send_json({"type": "auth", "token": token})
        assert ws.receive_json() == {"type": "connected"}


def test_ws_receives_event_delivery(client, db_session_factory):
    """A notification produced by the worker is pushed to the connected user."""
    token = _register(client, "rt3@example.com")
    uid, pid = _profile_id(db_session_factory, "rt3@example.com")
    with client.websocket_connect(f"/api/v1/realtime?token={token}") as ws:
        assert ws.receive_json() == {"type": "connected"}
        # Emit an event and drain the outbox -> orchestrator publishes real-time.
        with db_session_factory() as s:
            OutboxWriter(s).enqueue(EventEnvelope(
                event_type=DomainEventType.APPLICATION_SUBMITTED,
                aggregate_type=AggregateType.APPLICATION, aggregate_id=uuid.uuid4(),
                payload={"citizen_profile_id": str(pid), "application_number": "CL-RT"},
            ))
            s.commit()
        with db_session_factory() as s:
            OutboxDispatcher(session=s).dispatch_pending()
        msg = ws.receive_json()
        assert msg["kind"] == "notification"
        assert msg["event_type"] == DomainEventType.APPLICATION_SUBMITTED.value
        assert msg["title"]


def test_ws_disconnect_deregisters(client, db_session_factory):
    from app.modules.notifications.realtime.manager import connection_manager

    token = _register(client, "rt4@example.com")
    uid, pid = _profile_id(db_session_factory, "rt4@example.com")
    with client.websocket_connect(f"/api/v1/realtime?token={token}") as ws:
        ws.receive_json()
        assert connection_manager.is_connected(uid)
    # After the context exits (disconnect), the connection is removed (no leak).
    assert not connection_manager.is_connected(uid)
