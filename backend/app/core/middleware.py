"""Request-ID middleware.

Assigns a stable request_id to every request (honoring an inbound
X-Request-ID header when present), exposes it via a contextvar so it can be
injected into log records and error envelopes, and echoes it back on the
response. request_id always correlates to a server-side trace (NFR-OBS-1).
"""
from __future__ import annotations

import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

_REQUEST_ID_HEADER = "X-Request-ID"
_request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")


def get_request_id() -> str:
    """Return the current request's id (or '-' outside a request)."""
    return _request_id_ctx.get()


def new_request_id() -> str:
    return f"req_{uuid.uuid4().hex}"


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        inbound = request.headers.get(_REQUEST_ID_HEADER)
        request_id = inbound.strip() if inbound and inbound.strip() else new_request_id()
        token = _request_id_ctx.set(request_id)
        request.state.request_id = request_id
        try:
            response = await call_next(request)
        finally:
            _request_id_ctx.reset(token)
        response.headers[_REQUEST_ID_HEADER] = request_id
        return response
