"""Ingestion job worker (prompt §30-§32, ADR-006).

Processes an ingestion_jobs row end-to-end:
    PENDING -> PROCESSING -> (fetch -> pipeline) -> COMPLETED | FAILED

Bounded retries: on a transient failure the attempt counter increments and the
job stays retryable until max_attempts; permanent errors (SSRF, empty content,
disallowed content-type) fail immediately without wasting retries. Failure
metadata is stored on the job.

Execution seam: `run_job` is a pure function taking a job_id + a session
factory + provider deps. In this environment it is invoked synchronously by a
BackgroundTasks callback (no broker available); the SAME function is what a
Celery task would call. The API never blocks on ingestion — it returns 202 +
the job id, and this runs after the response (or via a worker).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.db.session import get_sessionmaker
from app.models.enums import IngestionJobStatus, VerificationStatus
from app.modules.knowledge.embeddings.provider import get_embedding_provider
from app.modules.knowledge.ingestion.fetcher import FetchError, SafeFetcher, SsrfError
from app.modules.knowledge.ingestion.pipeline import (
    EmptyContentError,
    IngestionPipeline,
)
from app.modules.knowledge.repository import KnowledgeRepository

logger = get_logger("civiclens.knowledge.worker")

# Errors that must NOT be retried (retrying can't fix them).
_PERMANENT = (SsrfError, EmptyContentError)


def run_job(
    job_id: uuid.UUID,
    *,
    session: Session | None = None,
    settings: Settings | None = None,
    fetcher: SafeFetcher | None = None,
) -> IngestionJobStatus:
    """Process one ingestion job. Returns the terminal status."""
    settings = settings or get_settings()
    own_session = session is None
    session = session or get_sessionmaker()()
    try:
        repo = KnowledgeRepository(session)
        job = repo.get_job(job_id)
        if job is None:
            return IngestionJobStatus.FAILED
        if job.status is IngestionJobStatus.COMPLETED:
            return job.status

        job.status = IngestionJobStatus.PROCESSING
        job.attempts += 1
        session.flush()

        try:
            fetcher = fetcher or SafeFetcher(settings)
            result = fetcher.fetch(job.url)
            pipeline = IngestionPipeline(
                session, embedder=get_embedding_provider(settings), settings=settings
            )
            outcome = pipeline.ingest(
                title=_title_from_job(job),
                url=job.url,
                publisher=_publisher_from_job(job),
                content=result.content,
                content_type=result.content_type,
                scheme_id=job.scheme_id,
                scheme_version_id=job.scheme_version_id,
                retrieved_at=result.retrieved_at,
            )
            job.knowledge_source_id = outcome.source_id
            job.status = IngestionJobStatus.COMPLETED
            job.error = None
            job.result = {
                "chunk_count": outcome.chunk_count,
                "content_hash": outcome.content_hash,
                "duplicate": outcome.duplicate,
                "verification_status": outcome.verification_status.value,
            }
            job.updated_at = datetime.now(timezone.utc)
            session.commit()
            logger.info("ingestion_job_completed", extra={"job_id": str(job_id)})
            return IngestionJobStatus.COMPLETED

        except EmptyContentError as exc:
            return _fail(session, job, str(exc), permanent=True)
        except _PERMANENT as exc:
            return _fail(session, job, f"{type(exc).__name__}: {exc}", permanent=True)
        except (FetchError, Exception) as exc:  # transient by default
            permanent = job.attempts >= job.max_attempts
            return _fail(session, job, f"{type(exc).__name__}: {exc}", permanent=permanent)
    finally:
        if own_session:
            session.close()


def _fail(session: Session, job, message: str, *, permanent: bool) -> IngestionJobStatus:
    job.error = message[:2000]
    job.updated_at = datetime.now(timezone.utc)
    if permanent or job.attempts >= job.max_attempts:
        job.status = IngestionJobStatus.FAILED
    else:
        # Leave retryable (PENDING) for a subsequent worker pass.
        job.status = IngestionJobStatus.PENDING
    session.commit()
    logger.warning(
        "ingestion_job_failed",
        extra={"job_id": str(job.id), "status": job.status.value, "attempts": job.attempts},
    )
    return job.status


def run_job_until_terminal(
    job_id: uuid.UUID, *, settings: Settings | None = None, fetcher: SafeFetcher | None = None
) -> IngestionJobStatus:
    """Drive a job through its bounded retries to a terminal state.

    Used by the in-process background runner (no external broker). A Celery
    deployment would instead re-enqueue on the retryable PENDING state.
    """
    settings = settings or get_settings()
    status = IngestionJobStatus.PENDING
    for _ in range(settings.fetch_max_retries + 2):
        status = run_job(job_id, settings=settings, fetcher=fetcher)
        if status in (IngestionJobStatus.COMPLETED, IngestionJobStatus.FAILED):
            break
    return status


def _title_from_job(job) -> str:
    meta = (job.result or {}).get("_input", {})
    return meta.get("title") or f"Source {job.url[:80]}"


def _publisher_from_job(job) -> str:
    meta = (job.result or {}).get("_input", {})
    return meta.get("publisher") or "Unknown"
