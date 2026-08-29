"""Documents application service (prompt §7, §10, §13, §34, §35, §36).

Owns the secure upload/download/delete lifecycle and object-level
authorization. File bytes go to object storage (ADR-005); the DB holds only a
non-guessable storage_key + metadata. Ownership is derived from the
authenticated principal's citizen profile, never from client input.

Upload flow: upload-init (create record + presigned PUT) -> client uploads to
storage -> complete (server re-reads bytes, hashes, validates size, dedups,
queues processing). Download: short-lived signed URL after an ownership check.
Delete: soft-delete the row AND delete the storage object (documented strategy).
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.exceptions import ConflictError, NotFoundError, PermissionDeniedError, ValidationError
from app.core.logging import get_logger
from app.models.document import Document, DocumentProcessingJob
from app.models.enums import DocumentStatus, ProcessingJobStatus
from app.modules.audit.service import AuditAction, AuditService
from app.modules.auth.dependencies import CurrentUser
from app.modules.documents.policies import can_access_document
from app.modules.documents.repository import DocumentsRepository
from app.modules.documents.storage import (
    ObjectNotFoundError,
    generate_storage_key,
    get_storage_provider,
)
from app.modules.documents.storage.provider import StorageProvider

logger = get_logger("civiclens.documents.service")

# Extension -> mime for validating the declared upload-init mime.
_ALLOWED_MIME = {"application/pdf": "pdf", "image/jpeg": "jpeg", "image/png": "png"}


class DocumentsService:
    def __init__(self, session: Session, settings: Settings | None = None) -> None:
        self._session = session
        self._s = settings or get_settings()
        self._repo = DocumentsRepository(session)
        self._audit = AuditService(session)
        self._storage: StorageProvider = get_storage_provider(self._s)

    # ------------------------------------------------------------------ #
    def _require_profile(self, current: CurrentUser) -> uuid.UUID:
        from app.models.citizen_profile import CitizenProfile
        from sqlalchemy import select

        profile_id = self._session.scalar(
            select(CitizenProfile.id).where(CitizenProfile.user_id == current.id)
        )
        if profile_id is None:
            raise NotFoundError("Citizen profile not found.")
        return profile_id

    def _authorize(self, current: CurrentUser, document: Document) -> None:
        from sqlalchemy import select

        from app.models.citizen_profile import CitizenProfile

        profile_id = self._session.scalar(
            select(CitizenProfile.id).where(CitizenProfile.user_id == current.id)
        )
        if not can_access_document(
            current_role=current.role,
            current_profile_id=profile_id,
            document_profile_id=document.citizen_profile_id,
        ):
            # Do not disclose existence of another citizen's document.
            raise NotFoundError("Document not found.")

    # ------------------------------------------------------------------ #
    def upload_init(
        self, *, current: CurrentUser, document_type, filename: str, mime_type: str,
        size_bytes: int, ip: str | None = None,
    ) -> dict:
        mime = mime_type.split(";")[0].strip().lower()
        if mime not in _ALLOWED_MIME:
            raise ValidationError(
                "Unsupported file type.",
                field_errors=[{"field": "mime_type", "message": "Allowed: PDF, JPEG, PNG."}],
            )
        if size_bytes > self._s.document_max_size_bytes:
            raise ValidationError(
                "File exceeds maximum size.",
                field_errors=[{"field": "size_bytes", "message": f"Max {self._s.document_max_size_mb} MB."}],
            )
        profile_id = self._require_profile(current)
        document_id = uuid.uuid4()
        storage_key = generate_storage_key(
            citizen_profile_id=profile_id, document_id=document_id, ext=_ALLOWED_MIME[mime]
        )
        document = Document(
            id=document_id,
            citizen_profile_id=profile_id,
            uploaded_by=current.id,
            document_type=document_type,
            status=DocumentStatus.UPLOADING,
            storage_key=storage_key,
            filename=filename[:255],
            mime_type=mime,
            size_bytes=size_bytes,
        )
        self._repo.add(document)
        signed = self._storage.create_upload_url(storage_key, mime)
        self._audit.record(
            action=AuditAction.DOCUMENT_UPLOAD_INIT,
            entity_type="document",
            entity_id=document.id,
            actor_user_id=current.id,
            diff={"document_type": document_type.value, "mime": mime},
            ip=ip,
        )
        self._session.commit()
        return {
            "document_id": str(document.id),
            "upload_url": signed.url,
            "method": signed.method,
            "headers": signed.headers,
            "expires_at": signed.expires_at,
        }

    def complete_upload(self, *, current: CurrentUser, document_id: uuid.UUID, ip: str | None = None) -> Document:
        document = self._repo.get(document_id)
        if document is None:
            raise NotFoundError("Document not found.")
        self._authorize(current, document)
        if document.status not in (DocumentStatus.UPLOADING, DocumentStatus.UPLOADED):
            raise ConflictError("Document is not awaiting upload completion.", code="INVALID_STATE")

        # Server re-reads the stored bytes: verifies presence, size, hash.
        try:
            data = self._storage.get_object(document.storage_key)
        except ObjectNotFoundError:
            raise ValidationError("No uploaded object found for this document.")
        if len(data) > self._s.document_max_size_bytes:
            document.status = DocumentStatus.VALIDATION_FAILED
            self._session.commit()
            raise ValidationError("Uploaded file exceeds maximum size.")

        sha256 = hashlib.sha256(data).hexdigest()
        # Duplicate detection (policy: flag, do NOT auto-delete the new upload).
        duplicate = self._repo.find_duplicate(document.citizen_profile_id, sha256)
        document.sha256 = sha256
        document.size_bytes = len(data)
        document.status = DocumentStatus.UPLOADED
        document.uploaded_at = datetime.now(timezone.utc)

        job = DocumentProcessingJob(document_id=document.id, status=ProcessingJobStatus.PENDING)
        self._repo.add_job(job)

        self._audit.record(
            action=AuditAction.DOCUMENT_UPLOADED,
            entity_type="document",
            entity_id=document.id,
            actor_user_id=current.id,
            diff={"duplicate_of": str(duplicate.id) if duplicate else None, "size_bytes": len(data)},
            ip=ip,
        )
        self._session.commit()
        self._session.refresh(document)
        return document

    def list_documents(self, *, current: CurrentUser) -> list[Document]:
        profile_id = self._require_profile(current)
        return self._repo.list_for_profile(profile_id)

    def get_document(self, *, current: CurrentUser, document_id: uuid.UUID, ip: str | None = None) -> Document:
        document = self._repo.get(document_id)
        if document is None:
            raise NotFoundError("Document not found.")
        self._authorize(current, document)
        self._audit.record(
            action=AuditAction.DOCUMENT_VIEWED, entity_type="document",
            entity_id=document.id, actor_user_id=current.id, ip=ip,
        )
        self._session.commit()
        return document

    def create_download(self, *, current: CurrentUser, document_id: uuid.UUID, ip: str | None = None) -> dict:
        document = self._repo.get(document_id)
        if document is None:
            raise NotFoundError("Document not found.")
        self._authorize(current, document)
        if not self._storage.object_exists(document.storage_key):
            raise NotFoundError("Document object not found.")
        signed = self._storage.create_download_url(document.storage_key)
        self._audit.record(
            action=AuditAction.DOCUMENT_DOWNLOADED, entity_type="document",
            entity_id=document.id, actor_user_id=current.id, ip=ip,
        )
        self._session.commit()
        return {"download_url": signed.url, "expires_at": signed.expires_at}

    def delete_document(self, *, current: CurrentUser, document_id: uuid.UUID, ip: str | None = None) -> None:
        document = self._repo.get(document_id)
        if document is None:
            raise NotFoundError("Document not found.")
        self._authorize(current, document)
        # Strategy: soft-delete the row (audit/retention) AND delete the private
        # object so bytes are not retained after deletion (prompt §35).
        self._storage.delete_object(document.storage_key)
        document.deleted_at = datetime.now(timezone.utc)
        document.status = DocumentStatus.REJECTED
        self._audit.record(
            action=AuditAction.DOCUMENT_DELETED, entity_type="document",
            entity_id=document.id, actor_user_id=current.id, ip=ip,
        )
        self._session.commit()

    def get_document_for_owner(self, *, current: CurrentUser, document_id: uuid.UUID) -> Document:
        document = self._repo.get(document_id)
        if document is None:
            raise NotFoundError("Document not found.")
        self._authorize(current, document)
        return document

    def multipart_upload(
        self, *, current: CurrentUser, document_type, filename: str, mime_type: str, data: bytes,
        ip: str | None = None,
    ) -> "Document":
        """Direct multipart upload convenience path (contract POST /documents).

        Validates size, stores bytes, hashes, queues processing in one call.
        Larger uploads should prefer the presigned upload-init/complete flow.
        """
        mime = (mime_type or "").split(";")[0].strip().lower()
        if mime not in _ALLOWED_MIME:
            raise ValidationError(
                "Unsupported file type.",
                field_errors=[{"field": "file", "message": "Allowed: PDF, JPEG, PNG."}],
            )
        if len(data) > self._s.document_max_size_bytes:
            raise ValidationError("File exceeds maximum size.")
        profile_id = self._require_profile(current)
        document_id = uuid.uuid4()
        storage_key = generate_storage_key(
            citizen_profile_id=profile_id, document_id=document_id, ext=_ALLOWED_MIME[mime]
        )
        self._storage.put_object(storage_key, data, mime)
        sha256 = hashlib.sha256(data).hexdigest()
        document = Document(
            id=document_id, citizen_profile_id=profile_id, uploaded_by=current.id,
            document_type=document_type, status=DocumentStatus.UPLOADED, storage_key=storage_key,
            filename=filename[:255] if filename else None, mime_type=mime, size_bytes=len(data),
            sha256=sha256, uploaded_at=datetime.now(timezone.utc),
        )
        self._repo.add(document)
        job = DocumentProcessingJob(document_id=document.id, status=ProcessingJobStatus.PENDING)
        self._repo.add_job(job)
        self._audit.record(
            action=AuditAction.DOCUMENT_UPLOADED, entity_type="document",
            entity_id=document.id, actor_user_id=current.id,
            diff={"via": "multipart", "size_bytes": len(data)}, ip=ip,
        )
        self._session.commit()
        self._session.refresh(document)
        return document
