"""Knowledge + assistant HTTP routes.

    POST /knowledge/search                 (authenticated)
    POST /knowledge/sources                (admin -> 202 + ingestion job)
    GET  /knowledge/sources                (admin)
    GET  /knowledge/jobs/{job_id}          (admin — ingestion status)
    POST /knowledge/sources/{id}/verify    (admin)
    POST /assistant/query                  (authenticated)

Ingestion runs asynchronously: the source-create endpoint enqueues a job and
schedules the worker via BackgroundTasks, returning 202 immediately (the API
never blocks on fetch/parse/embed). A Celery deployment would swap the
BackgroundTasks call for a task .delay() with no router change.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.db.session import db_session
from app.modules.auth.dependencies import CurrentUser
from app.modules.knowledge.assistant_service import AssistantService
from app.modules.knowledge.dependencies import require_knowledge_admin, require_reader
from app.modules.knowledge.schemas import (
    AssistantQueryInput,
    AssistantResponse,
    IngestionJobOut,
    KnowledgeSearchInput,
    KnowledgeSourceInput,
    KnowledgeSourceOut,
    SearchResultItem,
    SourceVerifyInput,
)
from app.modules.knowledge.service import KnowledgeService
from app.modules.knowledge.worker import run_job_until_terminal

knowledge_router = APIRouter(prefix="/knowledge", tags=["knowledge"])
assistant_router = APIRouter(prefix="/assistant", tags=["assistant"])


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@knowledge_router.post("/search", response_model=list[SearchResultItem])
def search(
    body: KnowledgeSearchInput,
    request: Request,
    current: CurrentUser = Depends(require_reader),
    session: Session = Depends(db_session),
) -> list[SearchResultItem]:
    results = KnowledgeService(session).search(
        query=body.query,
        scheme_id=body.scheme_id,
        scheme_version_id=body.scheme_version_id,
        limit=body.limit,
        authoritative_only=True,
        actor_user_id=current.id,
        ip=_ip(request),
    )
    return [
        SearchResultItem(
            chunk_id=str(r.chunk_id),
            source_id=str(r.source_id),
            content=r.content,
            source_url=r.source_url,
            page_number=r.page_number,
            section=r.section,
            score=round(r.score, 6),
        )
        for r in results
    ]


@knowledge_router.post(
    "/sources", response_model=IngestionJobOut, status_code=status.HTTP_202_ACCEPTED
)
def create_source(
    body: KnowledgeSourceInput,
    request: Request,
    background: BackgroundTasks,
    current: CurrentUser = Depends(require_knowledge_admin),
    session: Session = Depends(db_session),
) -> IngestionJobOut:
    job = KnowledgeService(session).create_ingestion_job(
        title=body.title,
        url=body.url,
        publisher=body.publisher,
        scheme_id=body.scheme_id,
        scheme_version_id=body.scheme_version_id,
        actor_user_id=current.id,
        ip=_ip(request),
    )
    # Process after the response is sent (async; API does not block on ingestion).
    background.add_task(run_job_until_terminal, job.id)
    return _job_out(job)


@knowledge_router.get("/sources", response_model=list[KnowledgeSourceOut])
def list_sources(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _current: CurrentUser = Depends(require_knowledge_admin),
    session: Session = Depends(db_session),
) -> list[KnowledgeSourceOut]:
    sources, _total = KnowledgeService(session).list_sources(page=page, page_size=page_size)
    return [_source_out(s) for s in sources]


@knowledge_router.get("/jobs/{job_id}", response_model=IngestionJobOut)
def get_job(
    job_id: uuid.UUID,
    _current: CurrentUser = Depends(require_knowledge_admin),
    session: Session = Depends(db_session),
) -> IngestionJobOut:
    return _job_out(KnowledgeService(session).get_job(job_id))


@knowledge_router.post("/sources/{source_id}/verify", response_model=KnowledgeSourceOut)
def verify_source(
    source_id: uuid.UUID,
    body: SourceVerifyInput,
    request: Request,
    current: CurrentUser = Depends(require_knowledge_admin),
    session: Session = Depends(db_session),
) -> KnowledgeSourceOut:
    source = KnowledgeService(session).verify_source(
        source_id=source_id,
        verification_status=body.verification_status,
        trust_level=body.trust_level,
        actor_user_id=current.id,
        ip=_ip(request),
    )
    return _source_out(source)


@assistant_router.post("/query", response_model=AssistantResponse)
def assistant_query(
    body: AssistantQueryInput,
    request: Request,
    current: CurrentUser = Depends(require_reader),
    session: Session = Depends(db_session),
) -> AssistantResponse:
    result = AssistantService(session).query(
        current=current,
        query=body.query,
        scheme_id=body.scheme_id,
        scheme_version_id=body.scheme_version_id,
        conversation_id=body.conversation_id,
        ip=_ip(request),
    )
    return AssistantResponse(**result)


# --------------------------------- mappers ---------------------------------- #
def _job_out(job) -> IngestionJobOut:
    return IngestionJobOut(
        id=str(job.id),
        status=job.status.value,
        url=job.url,
        knowledge_source_id=str(job.knowledge_source_id) if job.knowledge_source_id else None,
        attempts=job.attempts,
        max_attempts=job.max_attempts,
        error=job.error,
        result=job.result,
        created_at=job.created_at,
    )


def _source_out(s) -> KnowledgeSourceOut:
    return KnowledgeSourceOut(
        id=str(s.id),
        title=s.title,
        url=s.url,
        publisher=s.publisher,
        source_type=s.source_type.value if s.source_type else None,
        trust_level=s.trust_level.value,
        verification_status=s.verification_status.value,
        scheme_id=str(s.scheme_id) if s.scheme_id else None,
        created_at=s.created_at,
    )
