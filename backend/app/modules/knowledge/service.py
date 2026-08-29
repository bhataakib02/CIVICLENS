"""Knowledge application service.

Responsibilities:
- create_ingestion_job: persist a PENDING job and return it (the router
  schedules the worker as a background task -> 202 Accepted). Async: the API
  never blocks on fetch/parse/embed.
- get_job: job status polling.
- verify_source: admin marks a source verified/rejected + sets trust level.
- search: hybrid retrieval + rerank, returning authorized evidence only.

Owns its transaction for the job-create + verify writes.
"""
from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models.enums import IngestionJobStatus, SourceTrustLevel, VerificationStatus
from app.models.knowledge import IngestionJob
from app.modules.audit.service import AuditAction, AuditService
from app.modules.knowledge.embeddings.provider import get_embedding_provider
from app.modules.knowledge.repository import KnowledgeRepository
from app.modules.knowledge.retrieval.hybrid import HybridRetriever
from app.modules.knowledge.retrieval.reranker import get_reranker
from app.modules.knowledge.retrieval.semantic import RetrievedChunk

logger = get_logger("civiclens.knowledge.service")


class KnowledgeService:
    def __init__(self, session: Session, settings: Settings | None = None) -> None:
        self._session = session
        self._s = settings or get_settings()
        self._repo = KnowledgeRepository(session)
        self._audit = AuditService(session)

    # ------------------------------ ingestion ---------------------------- #
    def create_ingestion_job(
        self,
        *,
        title: str,
        url: str,
        publisher: str,
        scheme_id: uuid.UUID | None,
        scheme_version_id: uuid.UUID | None,
        actor_user_id: uuid.UUID,
        ip: str | None = None,
    ) -> IngestionJob:
        job = IngestionJob(
            url=url,
            scheme_id=scheme_id,
            scheme_version_id=scheme_version_id,
            status=IngestionJobStatus.PENDING,
            created_by=actor_user_id,
            result={"_input": {"title": title, "publisher": publisher}},
        )
        self._repo.add_job(job)
        self._audit.record(
            action=AuditAction.KNOWLEDGE_SOURCE_INGEST_REQUESTED,
            entity_type="ingestion_job",
            entity_id=job.id,
            actor_user_id=actor_user_id,
            diff={"url_host": _host(url)},
            ip=ip,
        )
        self._session.commit()
        self._session.refresh(job)
        return job

    def get_job(self, job_id: uuid.UUID) -> IngestionJob:
        job = self._repo.get_job(job_id)
        if job is None:
            raise NotFoundError("Ingestion job not found.")
        return job

    def verify_source(
        self,
        *,
        source_id: uuid.UUID,
        verification_status: str,
        trust_level: str | None,
        actor_user_id: uuid.UUID,
        ip: str | None = None,
    ):
        source = self._repo.get_source(source_id)
        if source is None:
            raise NotFoundError("Knowledge source not found.")
        try:
            source.verification_status = VerificationStatus(verification_status)
            if trust_level is not None:
                source.trust_level = SourceTrustLevel(trust_level)
        except ValueError as exc:
            raise ValidationError("Invalid verification_status or trust_level.") from exc
        self._audit.record(
            action=AuditAction.KNOWLEDGE_SOURCE_VERIFIED,
            entity_type="knowledge_source",
            entity_id=source.id,
            actor_user_id=actor_user_id,
            diff={"verification_status": source.verification_status.value, "trust_level": source.trust_level.value},
            ip=ip,
        )
        self._session.commit()
        self._session.refresh(source)
        return source

    def list_sources(self, *, page: int, page_size: int):
        offset = (page - 1) * page_size
        return self._repo.list_sources(limit=page_size, offset=offset), self._repo.count_sources()

    # ------------------------------ search ------------------------------- #
    def search(
        self,
        *,
        query: str,
        scheme_id: uuid.UUID | None,
        scheme_version_id: uuid.UUID | None,
        limit: int,
        authoritative_only: bool = True,
        actor_user_id: uuid.UUID | None = None,
        ip: str | None = None,
    ) -> list[RetrievedChunk]:
        embedder = get_embedding_provider(self._s)
        retriever = HybridRetriever(self._session, embedder, self._s)
        candidates = retriever.retrieve(
            query=query,
            scheme_id=scheme_id,
            scheme_version_id=scheme_version_id,
            authoritative_only=authoritative_only,
        )
        reranked = get_reranker().rerank(query, candidates, top_k=limit)
        if actor_user_id is not None:
            self._audit.record(
                action=AuditAction.KNOWLEDGE_SEARCH,
                entity_type="knowledge_search",
                actor_user_id=actor_user_id,
                diff={"result_count": len(reranked)},
                ip=ip,
            )
            self._session.commit()
        logger.info("knowledge_search", extra={"result_count": len(reranked)})
        return reranked


def _host(url: str) -> str:
    from urllib.parse import urlparse

    return urlparse(url).hostname or ""
