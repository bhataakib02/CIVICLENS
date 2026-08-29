"""Authenticated real-time WebSocket endpoint (prompt §20, §21, §22).

Authentication: the client presents its access token AFTER connecting, as the
first message ({"type":"auth","token":"..."}) OR via the `token` query param.
We validate identity + expiry with the same decode_access_token used by HTTP
(prompt §21). No anonymous connections; unauthenticated sockets are closed with
policy-violation code 4401.

The token is validated but NOT logged (prompt §37). Connection lifecycle:
connect -> authenticate -> register -> receive loop (handles client heartbeat
"ping") -> always deregister on disconnect (no leaks, prompt §22).
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.logging import get_logger
from app.core.security import decode_access_token
from app.db.session import get_sessionmaker
from app.models.enums import UserStatus
from app.models.user import User
from app.modules.audit.service import AuditAction, AuditService
from app.modules.notifications.realtime.manager import connection_manager

logger = get_logger("civiclens.notifications.realtime")

realtime_router = APIRouter(tags=["realtime"])

WS_POLICY_VIOLATION = 4401  # our "unauthenticated" close code


def _authenticate(token: str | None) -> uuid.UUID | None:
    if not token:
        return None
    try:
        claims = decode_access_token(token)
        user_id = uuid.UUID(str(claims["sub"]))
    except Exception:
        return None
    # Confirm the account still exists and is active (a valid token must not
    # outlive suspension/deletion — same rule as HTTP auth).
    session = get_sessionmaker()()
    try:
        user = session.get(User, user_id)
        if user is None or user.status is UserStatus.SUSPENDED:
            return None
        return user.id
    finally:
        session.close()


@realtime_router.websocket("/realtime")
async def realtime_ws(websocket: WebSocket, token: str | None = Query(default=None)) -> None:
    await websocket.accept()

    # Authenticate: prefer the query token, else the first auth message.
    user_id = _authenticate(token)
    if user_id is None:
        try:
            first = await websocket.receive_json()
            if isinstance(first, dict) and first.get("type") == "auth":
                user_id = _authenticate(first.get("token"))
        except Exception:
            user_id = None

    if user_id is None:
        await websocket.close(code=WS_POLICY_VIOLATION)
        return

    await connection_manager.connect(user_id, websocket)
    # Audit the established connection (not heartbeats — prompt §39).
    _audit_connection(user_id)
    await websocket.send_json({"type": "connected"})

    try:
        while True:
            data = await websocket.receive_json()
            if isinstance(data, dict) and data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            # Server ignores other client messages; it is a push channel.
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.info("realtime_receive_ended")
    finally:
        await connection_manager.disconnect(user_id, websocket)


def _audit_connection(user_id: uuid.UUID) -> None:
    session = get_sessionmaker()()
    try:
        AuditService(session).record(
            action=AuditAction.REALTIME_CONNECTION_ESTABLISHED, entity_type="user",
            entity_id=user_id, actor_user_id=user_id,
        )
        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()
