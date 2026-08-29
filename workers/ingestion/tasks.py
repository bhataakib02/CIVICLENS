"""Knowledge source ingestion Celery tasks (ADR-006).

Wraps ``backend/app/modules/knowledge/worker.py`` execution logic for Celery queue execution.
"""

from __future__ import annotations

import uuid
from typing import Any

from app.modules.knowledge.worker import run_job_until_terminal
from workers.celery_app import celery_app


def _get_task_decorator():
    if hasattr(celery_app, "task"):
        return celery_app.task(name="workers.ingestion.ingest_source", bind=True, max_retries=3)
    return lambda fn: fn


@_get_task_decorator()
def ingest_knowledge_source_task(self_or_job_id: Any, job_id_arg: str | None = None) -> str:
    """Async task to ingest, parse, chunk, and embed a government knowledge source."""
    raw_id = job_id_arg if job_id_arg is not None else self_or_job_id
    job_uuid = uuid.UUID(str(raw_id))
    terminal_status = run_job_until_terminal(job_uuid)
    return terminal_status.value
