"""Celery application instance and configuration.

Configures broker, result backend, task queues, and routing for background tasks.
Broker settings are sourced from ``app.core.config.Settings``.
"""

from __future__ import annotations

import os

from app.core.config import get_settings

# Determine Redis broker URL from settings or environment fallback
settings = get_settings()
broker_url = settings.redis_url or os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
result_backend = settings.redis_url or os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

# Lightweight dummy app if Celery isn't installed in pure-dev context
try:
    from celery import Celery

    celery_app = Celery(
        "civiclens_workers",
        broker=broker_url,
        backend=result_backend,
        include=[
            "workers.ocr.tasks",
            "workers.ingestion.tasks",
            "workers.notifications.tasks",
        ],
    )

    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_routes={
            "workers.ocr.*": {"queue": "ocr"},
            "workers.ingestion.*": {"queue": "ingestion"},
            "workers.notifications.*": {"queue": "notifications"},
        },
        task_annotations={
            "*": {"rate_limit": "100/m"},
        },
    )

except ImportError:
    # Fallback stub for environments where celery is optional
    class DummyCelery:
        def task(self, *args, **kwargs):
            def decorator(fn):
                return fn
            return decorator

    celery_app = DummyCelery()  # type: ignore
