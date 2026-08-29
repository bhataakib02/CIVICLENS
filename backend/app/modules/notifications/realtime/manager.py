"""Real-time connection manager + cross-instance pub/sub (prompt §22, §23).

Design:
  * ConnectionManager tracks per-user WebSocket connections in THIS process and
    fans a message out to all of a user's local connections.
  * A PubSub abstraction decouples "publish an event for user X" from "which
    process holds X's connection". The in-memory backend (dev/tests, single
    process) delivers directly. A Redis backend (production, multi-instance)
    publishes to a channel every instance subscribes to, so a user connected to
    instance B receives an event generated on instance A (prompt §23).
  * Redis is imported lazily and is OPTIONAL — the package works with the
    in-memory backend and never hard-depends on redis being installed.

Stale connections are dropped on send failure; connections are always removed on
disconnect so nothing leaks (prompt §22).
"""
from __future__ import annotations

import asyncio
import json
import uuid
from collections import defaultdict
from typing import Any, Protocol

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.core.metrics import metrics

logger = get_logger("civiclens.notifications.realtime")


class _WebSocketLike(Protocol):
    async def send_json(self, data: Any) -> None: ...


class ConnectionManager:
    """Tracks active WebSocket connections per user (this process)."""

    def __init__(self) -> None:
        self._by_user: dict[uuid.UUID, set[_WebSocketLike]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, user_id: uuid.UUID, ws: _WebSocketLike) -> None:
        async with self._lock:
            self._by_user[user_id].add(ws)
        metrics.gauge("websocket_connections", self.connection_count())

    async def disconnect(self, user_id: uuid.UUID, ws: _WebSocketLike) -> None:
        async with self._lock:
            conns = self._by_user.get(user_id)
            if conns:
                conns.discard(ws)
                if not conns:
                    self._by_user.pop(user_id, None)
        metrics.gauge("websocket_connections", self.connection_count())

    async def deliver_local(self, user_id: uuid.UUID, message: dict) -> int:
        """Send to all local connections for the user; drop stale ones."""
        async with self._lock:
            conns = list(self._by_user.get(user_id, ()))
        delivered = 0
        stale: list[_WebSocketLike] = []
        for ws in conns:
            try:
                await ws.send_json(message)
                delivered += 1
            except Exception:
                metrics.incr("websocket_delivery_failures")
                stale.append(ws)
        for ws in stale:
            await self.disconnect(user_id, ws)
        return delivered

    def connection_count(self) -> int:
        return sum(len(c) for c in self._by_user.values())

    def is_connected(self, user_id: uuid.UUID) -> bool:
        return bool(self._by_user.get(user_id))


class PubSub(Protocol):
    async def publish(self, user_id: uuid.UUID, message: dict) -> None: ...
    async def start(self) -> None: ...
    async def stop(self) -> None: ...


class InMemoryPubSub:
    """Single-process backend (dev/tests): delivers straight to the local manager."""

    def __init__(self, manager: ConnectionManager) -> None:
        self._manager = manager

    async def publish(self, user_id: uuid.UUID, message: dict) -> None:
        await self._manager.deliver_local(user_id, message)

    async def start(self) -> None:  # no-op
        return None

    async def stop(self) -> None:  # no-op
        return None


class RedisPubSub:
    """Multi-instance backend (prompt §23). Lazily imports redis.asyncio; every
    instance subscribes to a shared channel and re-delivers to local connections.

    This is only selected when REALTIME_PROVIDER=redis and REDIS_URL is set.
    """

    CHANNEL = "civiclens:realtime"

    def __init__(self, manager: ConnectionManager, redis_url: str) -> None:
        self._manager = manager
        self._redis_url = redis_url
        self._redis = None
        self._pubsub = None
        self._task: asyncio.Task | None = None

    async def start(self) -> None:  # pragma: no cover - requires a real redis
        import redis.asyncio as aioredis  # lazy, optional dependency

        self._redis = aioredis.from_url(self._redis_url, encoding="utf-8", decode_responses=True)
        self._pubsub = self._redis.pubsub()
        await self._pubsub.subscribe(self.CHANNEL)
        self._task = asyncio.create_task(self._listen())

    async def _listen(self) -> None:  # pragma: no cover - requires a real redis
        assert self._pubsub is not None
        async for msg in self._pubsub.listen():
            if msg.get("type") != "message":
                continue
            try:
                data = json.loads(msg["data"])
                user_id = uuid.UUID(data["user_id"])
                await self._manager.deliver_local(user_id, data["message"])
            except Exception:
                logger.warning("realtime_redis_message_error")

    async def publish(self, user_id: uuid.UUID, message: dict) -> None:  # pragma: no cover
        assert self._redis is not None
        await self._redis.publish(
            self.CHANNEL, json.dumps({"user_id": str(user_id), "message": message})
        )

    async def stop(self) -> None:  # pragma: no cover
        if self._task:
            self._task.cancel()
        if self._pubsub:
            await self._pubsub.unsubscribe(self.CHANNEL)
        if self._redis:
            await self._redis.close()


# Process-wide singletons.
connection_manager = ConnectionManager()
_pubsub: PubSub | None = None


def get_pubsub(settings: Settings | None = None) -> PubSub:
    global _pubsub
    if _pubsub is None:
        settings = settings or get_settings()
        if settings.realtime_provider.lower() == "redis" and settings.redis_url:
            _pubsub = RedisPubSub(connection_manager, settings.redis_url)
        else:
            _pubsub = InMemoryPubSub(connection_manager)
    return _pubsub


def reset_pubsub() -> None:
    """Test hook to clear the cached pub/sub singleton."""
    global _pubsub
    _pubsub = None
