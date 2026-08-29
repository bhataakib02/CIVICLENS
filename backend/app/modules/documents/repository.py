"""Documents persistence layer."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import (
    Document,
    DocumentExtractedField,
    DocumentExtraction,
    DocumentProcessingJob,
)
from app.models.enums import DocumentStatus


class DocumentsRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, document: Document) -> Document:
        self._session.add(document)
        self._session.flush()
        return document

    def get(self, document_id: uuid.UUID) -> Document | None:
        doc = self._session.get(Document, document_id)
        if doc is not None and doc.deleted_at is not None:
            return None  # soft-deleted rows are not returned
        return doc

    def get_including_deleted(self, document_id: uuid.UUID) -> Document | None:
        return self._session.get(Document, document_id)

    def list_for_profile(self, profile_id: uuid.UUID) -> list[Document]:
        stmt = (
            select(Document)
            .where(Document.citizen_profile_id == profile_id, Document.deleted_at.is_(None))
            .order_by(Document.created_at.desc())
        )
        return list(self._session.scalars(stmt))

    def find_duplicate(self, profile_id: uuid.UUID, sha256: str) -> Document | None:
        stmt = select(Document).where(
            Document.citizen_profile_id == profile_id,
            Document.sha256 == sha256,
            Document.deleted_at.is_(None),
        )
        return self._session.scalars(stmt).first()

    def add_job(self, job: DocumentProcessingJob) -> DocumentProcessingJob:
        self._session.add(job)
        self._session.flush()
        return job

    def get_latest_job(self, document_id: uuid.UUID) -> DocumentProcessingJob | None:
        stmt = (
            select(DocumentProcessingJob)
            .where(DocumentProcessingJob.document_id == document_id)
            .order_by(DocumentProcessingJob.created_at.desc())
        )
        return self._session.scalars(stmt).first()

    def get_job(self, job_id: uuid.UUID) -> DocumentProcessingJob | None:
        return self._session.get(DocumentProcessingJob, job_id)

    def latest_extraction(self, document_id: uuid.UUID) -> DocumentExtraction | None:
        stmt = (
            select(DocumentExtraction)
            .where(DocumentExtraction.document_id == document_id)
            .order_by(DocumentExtraction.extracted_at.desc())
        )
        return self._session.scalars(stmt).first()

    def fields_for_extraction(self, extraction_id: uuid.UUID) -> list[DocumentExtractedField]:
        stmt = (
            select(DocumentExtractedField)
            .where(DocumentExtractedField.extraction_id == extraction_id)
            .order_by(DocumentExtractedField.field_name)
        )
        return list(self._session.scalars(stmt))
