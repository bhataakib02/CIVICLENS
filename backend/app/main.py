"""FastAPI application factory and global wiring.

- Health (liveness) + readiness (verifies PostgreSQL connectivity).
- Global exception handlers producing the stable error envelope; never leak
  tracebacks/SQL/secrets to clients.
- CORS from configuration (no hardcoded production wildcard).
- Request-ID middleware.
- Auth + citizens routers under /api/v1.
"""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import Settings, get_settings
from app.core.exceptions import AppError
from app.core.logging import configure_logging, get_logger
from app.core.middleware import RequestIDMiddleware, get_request_id
from app.db.session import get_sessionmaker
from app.modules.auth.router import auth_router, me_router
from app.modules.citizens.router import router as citizens_router
from app.modules.applications.router import applications_router
from app.modules.consents.router import consents_router
from app.modules.documents.router import documents_router
from app.modules.eligibility.router import eligibility_router
from app.modules.knowledge.router import assistant_router, knowledge_router
from app.modules.notifications.router import (
    me_notifications_router,
    notifications_router,
)
from app.modules.notifications.realtime.websocket import realtime_router
from app.modules.schemes.router import (
    admin_schemes_router,
    scheme_versions_router,
    schemes_router,
)
from app.modules.admin.router import admin_ops_router, agent_ops_router

logger = get_logger("civiclens.app")

API_PREFIX = "/api/v1"


def _error_payload(code: str, message: str, field_errors: list[dict] | None = None) -> dict:
    body: dict = {"code": code, "message": message, "request_id": get_request_id()}
    if field_errors:
        body["field_errors"] = field_errors
    return {"error": body}


def _register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        field_errors = getattr(exc, "field_errors", None)
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_payload(exc.code, exc.message, field_errors),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        field_errors = [
            {
                "field": ".".join(str(p) for p in err.get("loc", []) if p != "body"),
                "message": err.get("msg", "Invalid value."),
            }
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=_error_payload(
                "VALIDATION_ERROR", "Request failed validation.", field_errors
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code_map = {401: "INVALID_TOKEN", 403: "PERMISSION_DENIED", 404: "NOT_FOUND"}
        code = code_map.get(exc.status_code, "HTTP_ERROR")
        message = exc.detail if isinstance(exc.detail, str) else "Request could not be completed."
        return JSONResponse(
            status_code=exc.status_code, content=_error_payload(code, message)
        )

    @app.exception_handler(Exception)
    async def _unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
        # Log server-side with the request id; return a generic envelope. No
        # traceback/SQL/secret ever crosses the boundary to the client.
        logger.error(
            "unhandled_exception",
            extra={"request_id": get_request_id(), "path": request.url.path},
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content=_error_payload("INTERNAL_ERROR", "An unexpected error occurred."),
        )


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    settings.validate_production_config()
    configure_logging(logging.INFO)

    app = FastAPI(
        title="CivicLens API",
        version="1.0.0",
        description=(
            "AI-assisted public-service navigation API. This deployment implements "
            "the authentication + citizen-profile vertical slice."
        ),
        openapi_url="/openapi.json",
        docs_url="/docs",
    )

    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    _register_exception_handlers(app)

    # Health / readiness (public, unauthenticated).
    @app.get(f"{API_PREFIX}/health", tags=["health"])
    def health() -> dict:
        return {"status": "ok"}

    @app.get(f"{API_PREFIX}/health/ready", tags=["health"])
    def readiness() -> JSONResponse:
        """Verify required infrastructure. PostgreSQL is always required; Redis
        is required only when the realtime provider uses it (prompt §52)."""
        checks: dict = {}
        try:
            session = get_sessionmaker()()
            try:
                session.execute(text("SELECT 1"))
            finally:
                session.close()
            checks["database"] = "ok"
        except Exception:
            logger.warning("readiness_db_unavailable", extra={"request_id": get_request_id()})
            return JSONResponse(
                status_code=503, content={"status": "not_ready", "database": "unavailable"}
            )

        if settings.redis_required:
            try:
                import redis  # lazy, optional

                client = redis.Redis.from_url(settings.redis_url)
                client.ping()
                checks["redis"] = "ok"
            except Exception:
                logger.warning("readiness_redis_unavailable", extra={"request_id": get_request_id()})
                return JSONResponse(
                    status_code=503,
                    content={"status": "not_ready", "database": "ok", "redis": "unavailable"},
                )
        return JSONResponse(status_code=200, content={"status": "ready", **checks})

    @app.get(f"{API_PREFIX}/metrics", tags=["health"])
    def metrics_endpoint() -> dict:
        """In-process metrics snapshot (prompt §51). No notification content."""
        from app.core.metrics import metrics

        return metrics.snapshot()

    # Feature routers.
    app.include_router(auth_router, prefix=API_PREFIX)
    app.include_router(me_router, prefix=API_PREFIX)
    app.include_router(citizens_router, prefix=API_PREFIX)
    app.include_router(consents_router, prefix=API_PREFIX)
    app.include_router(schemes_router, prefix=API_PREFIX)
    app.include_router(scheme_versions_router, prefix=API_PREFIX)
    app.include_router(admin_schemes_router, prefix=API_PREFIX)
    app.include_router(eligibility_router, prefix=API_PREFIX)
    app.include_router(knowledge_router, prefix=API_PREFIX)
    app.include_router(assistant_router, prefix=API_PREFIX)
    app.include_router(documents_router, prefix=API_PREFIX)
    app.include_router(applications_router, prefix=API_PREFIX)
    app.include_router(notifications_router, prefix=API_PREFIX)
    app.include_router(me_notifications_router, prefix=API_PREFIX)
    app.include_router(realtime_router, prefix=API_PREFIX)
    app.include_router(admin_ops_router, prefix=API_PREFIX)
    app.include_router(agent_ops_router, prefix=API_PREFIX)

    return app


app = create_app()
