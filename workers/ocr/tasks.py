"""OCR and document extraction Celery tasks (ADR-006).

Wraps ``backend/app/modules/documents/worker.py`` execution logic for Celery queue execution.
"""

from __future__ import annotations

import uuid
from typing import Any

from app.modules.documents.worker import run_job_until_terminal
from workers.celery_app import celery_app


def _get_task_decorator():
    if hasattr(celery_app, "task"):
        return celery_app.task(name="workers.ocr.process_document", bind=True, max_retries=3)
    return lambda fn: fn


@_get_task_decorator()
def process_document_task(self_or_job_id: Any, job_id_arg: str | None = None) -> str:
    """Async task to process an uploaded document through OCR and extraction pipeline."""
    raw_id = job_id_arg if job_id_arg is not None else self_or_job_id
    job_uuid = uuid.UUID(str(raw_id))
    terminal_status = run_job_until_terminal(job_uuid)
    return terminal_status.value
