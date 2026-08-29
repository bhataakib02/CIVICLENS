"""Document processing worker (prompt §16, §17, §18, §46, ADR-006).

Drives a document_processing_jobs row through the pipeline. Async seam: the API
enqueues (PENDING) and schedules run_job_until_terminal via BackgroundTasks
(no broker available here); a Celery task would call the same run_job.

Bounded retries: transient errors (OCR/extraction infra) increment attempts and
stay retryable until max_attempts; permanent errors (validation/malware/corrupt)
fail immediately. PII-safe: only document_id/job_id/status/error_code are logged,
never document contents.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.db.session import get_sessionmaker
from app.models.enums import DocumentStatus, ProcessingJobStatus
from app.modules.audit.service import AuditAction, AuditService
from app.modules.documents.processing.extractor import get_extraction_provider
from app.modules.documents.processing.ocr import get_ocr_provider
from app.modules.documents.processing.pipeline import (
    PermanentProcessingError,
    ProcessingPipeline,
    TransientProcessingError,
)
from app.modules.documents.processing.scanner import get_malware_scanner
from app.modules.documents.repository import DocumentsRepository
from app.modules.documents.storage import ObjectNotFoundError, get_storage_provider

logger = get_logger("civiclens.documents.worker")


def run_job(
    job_id: uuid.UUID,
    *,
    session: Session | None = None,
    settings: Settings | None = None,
) -> ProcessingJobStatus:
    settings = settings or get_settings()
    own_session = session is None
    session = session or get_sessionmaker()()
    try:
        repo = DocumentsRepository(session)
        job = repo.get_job(job_id)
        if job is None:
            return ProcessingJobStatus.FAILED
        if job.status is ProcessingJobStatus.COMPLETED:
            return job.status

        document = repo.get_including_deleted(job.document_id)
        if document is None or document.deleted_at is not None:
            return _fail(session, job, "DOCUMENT_GONE", permanent=True)

        job.status = ProcessingJobStatus.PROCESSING
        job.attempt_count += 1
        job.started_at = job.started_at or datetime.now(timezone.utc)
        document.status = DocumentStatus.VALIDATING
        session.flush()

        audit = AuditService(session)
        audit.record(
            action=AuditAction.DOCUMENT_PROCESSING_STARTED, entity_type="document",
            entity_id=document.id, actor_user_id=None,
        )
        logger.info("document_processing_started", extra={"document_id": str(document.id), "job_id": str(job.id)})

        storage = get_storage_provider(settings)
        try:
            data = storage.get_object(document.storage_key)
        except ObjectNotFoundError:
            return _fail(session, job, "OBJECT_MISSING", permanent=True, document=document, audit=audit)

        pipeline = ProcessingPipeline(
            session,
            scanner=get_malware_scanner(settings),
            ocr=get_ocr_provider(settings),
            extractor=get_extraction_provider(settings),
            settings=settings,
        )
        try:
            result = pipeline.process(document, data)
        except PermanentProcessingError as exc:
            return _fail(session, job, exc.code, permanent=True, document=document, audit=audit)
        except TransientProcessingError as exc:
            permanent = job.attempt_count >= job.max_attempts
            return _fail(session, job, exc.code, permanent=permanent, document=document, audit=audit)
        except Exception:
            permanent = job.attempt_count >= job.max_attempts
            return _fail(session, job, "UNKNOWN_ERROR", permanent=permanent, document=document, audit=audit)

        job.status = ProcessingJobStatus.COMPLETED
        job.completed_at = datetime.now(timezone.utc)
        job.error_code = None
        # Record identity mismatch / conflict audit events (PII-safe: no values
        # for identity; conflict field names only).
        if result.identity_match is False:
            audit.record(
                action=AuditAction.IDENTITY_MISMATCH_DETECTED, entity_type="document",
                entity_id=document.id, actor_user_id=None,
            )
        if result.conflicts:
            audit.record(
                action=AuditAction.FACT_CONFLICT_DETECTED, entity_type="document",
                entity_id=document.id, actor_user_id=None,
                diff={"fields": [c["field"] for c in result.conflicts]},
            )
        audit.record(
            action=AuditAction.DOCUMENT_PROCESSING_COMPLETED, entity_type="document",
            entity_id=document.id, actor_user_id=None,
            diff={"status": result.status.value, "field_count": result.field_count},
        )
        session.commit()
        logger.info(
            "document_processing_completed",
            extra={"document_id": str(document.id), "job_id": str(job.id), "status": result.status.value},
        )
        return ProcessingJobStatus.COMPLETED
    finally:
        if own_session:
            session.close()


def _fail(session, job, error_code, *, permanent, document=None, audit=None) -> ProcessingJobStatus:
    job.error_code = error_code
    now = datetime.now(timezone.utc)
    job.updated_at = now
    if permanent or job.attempt_count >= job.max_attempts:
        job.status = ProcessingJobStatus.FAILED
        job.failed_at = now
        if document is not None and document.status not in (
            DocumentStatus.VALIDATION_FAILED, DocumentStatus.REJECTED,
        ):
            document.status = DocumentStatus.PROCESSING_FAILED
    else:
        job.status = ProcessingJobStatus.PENDING  # retryable
    if audit is not None and document is not None:
        audit.record(
            action=AuditAction.DOCUMENT_PROCESSING_FAILED, entity_type="document",
            entity_id=document.id, actor_user_id=None,
            diff={"error_code": error_code, "status": job.status.value},
        )
    session.commit()
    logger.warning(
        "document_processing_failed",
        extra={"job_id": str(job.id), "error_code": error_code, "status": job.status.value},
    )
    return job.status


def run_job_until_terminal(job_id: uuid.UUID, *, settings: Settings | None = None) -> ProcessingJobStatus:
    settings = settings or get_settings()
    status = ProcessingJobStatus.PENDING
    for _ in range(4):  # max_attempts (3) + 1 safety
        status = run_job(job_id, settings=settings)
        if status in (ProcessingJobStatus.COMPLETED, ProcessingJobStatus.FAILED):
            break
    return status
