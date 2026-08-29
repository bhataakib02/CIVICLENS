"""Document HTTP routes.

Contract + documented extensions:
    POST   /documents/upload-init
    POST   /documents/{id}/complete
    GET    /documents
    GET    /documents/{id}
    GET    /documents/{id}/download
    DELETE /documents/{id}
    POST   /documents/{id}/confirm            (verify/correct/reject)
    PUT    /documents/_local-object           (local storage signed upload)
    GET    /documents/_local-object           (local storage signed download)

Responses never expose storage_key/internal paths/credentials (prompt §42).
The _local-object endpoint exists only for the LocalStorageProvider dev/test
signed URLs; it validates the HMAC signature + expiry before serving bytes.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Query, Request, Response, UploadFile, status
from fastapi.responses import Response as RawResponse
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.db.session import db_session
from app.models.enums import DocumentType
from app.modules.auth.dependencies import CurrentUser, require_authenticated_user
from app.modules.documents.dependencies import require_owner
from app.modules.documents.repository import DocumentsRepository
from app.modules.documents.schemas import (
    ConfirmInput,
    Document as DocumentSchema,
    DocumentDetail,
    DownloadResponse,
    UploadCompleteInput,
    UploadInitInput,
    UploadInitResponse,
    ExtractedFieldOut,
)
from app.modules.documents.service import DocumentsService
from app.modules.documents.storage import get_storage_provider
from app.modules.documents.storage.local import LocalStorageProvider
from app.modules.documents.storage.provider import ObjectNotFoundError, SignatureError
from app.modules.documents.verification.service import VerificationService
from app.modules.documents.worker import run_job_until_terminal

documents_router = APIRouter(prefix="/documents", tags=["documents"])


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _to_document(doc) -> DocumentSchema:
    return DocumentSchema(
        id=str(doc.id), document_type=doc.document_type, status=doc.status.value,
        filename=doc.filename, mime_type=doc.mime_type, size_bytes=doc.size_bytes,
        uploaded_at=doc.uploaded_at, created_at=doc.created_at,
    )


# ------------------------------- local storage seam ------------------------- #
@documents_router.put("/_local-object")
async def local_object_put(
    request: Request,
    key: str = Query(...),
    action: str = Query(...),
    expires: int = Query(...),
    sig: str = Query(...),
    session: Session = Depends(db_session),
) -> Response:
    """Accept a direct upload for the LocalStorageProvider signed URL (dev/test)."""
    provider = get_storage_provider()
    if not isinstance(provider, LocalStorageProvider) or action != "upload":
        raise NotFoundError("Not found.")
    try:
        provider.verify_signature(key, "upload", expires, sig)
    except SignatureError as exc:
        raise ValidationError(str(exc)) from exc
    body = await request.body()
    if len(body) > get_storage_provider()._s.document_max_size_bytes:  # cheap guard
        raise ValidationError("Uploaded file exceeds maximum size.")
    provider.put_object(key, body)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@documents_router.get("/_local-object")
def local_object_get(
    key: str = Query(...),
    action: str = Query(...),
    expires: int = Query(...),
    sig: str = Query(...),
) -> RawResponse:
    """Serve bytes for a LocalStorageProvider signed download URL (dev/test)."""
    provider = get_storage_provider()
    if not isinstance(provider, LocalStorageProvider) or action != "download":
        raise NotFoundError("Not found.")
    try:
        provider.verify_signature(key, "download", expires, sig)
    except SignatureError as exc:
        raise ValidationError(str(exc)) from exc
    try:
        data = provider.get_object(key)
    except ObjectNotFoundError as exc:
        raise NotFoundError("Object not found.") from exc
    return RawResponse(content=data, media_type="application/octet-stream")


# ------------------------------- documents ---------------------------------- #
@documents_router.post("/upload-init", response_model=UploadInitResponse)
def upload_init(
    body: UploadInitInput,
    request: Request,
    current: CurrentUser = Depends(require_owner),
    session: Session = Depends(db_session),
) -> UploadInitResponse:
    result = DocumentsService(session).upload_init(
        current=current, document_type=body.document_type, filename=body.filename,
        mime_type=body.mime_type, size_bytes=body.size_bytes, ip=_ip(request),
    )
    return UploadInitResponse(**result)


@documents_router.post("/{document_id}/complete", response_model=DocumentSchema, status_code=status.HTTP_202_ACCEPTED)
def complete_upload(
    document_id: uuid.UUID,
    request: Request,
    background: BackgroundTasks,
    body: UploadCompleteInput | None = None,
    current: CurrentUser = Depends(require_owner),
    session: Session = Depends(db_session),
) -> DocumentSchema:
    doc = DocumentsService(session).complete_upload(
        current=current, document_id=document_id, ip=_ip(request)
    )
    # Queue async processing (API does not block on OCR/extraction).
    job = DocumentsRepository(session).get_latest_job(doc.id)
    if job is not None:
        background.add_task(run_job_until_terminal, job.id)
    return _to_document(doc)


@documents_router.get("", response_model=list[DocumentSchema])
@documents_router.get("/", response_model=list[DocumentSchema], include_in_schema=False)
def list_documents(
    current: CurrentUser = Depends(require_owner),
    session: Session = Depends(db_session),
) -> list[DocumentSchema]:
    return [_to_document(d) for d in DocumentsService(session).list_documents(current=current)]


@documents_router.post("", response_model=DocumentSchema, status_code=status.HTTP_202_ACCEPTED)
async def upload_multipart(
    request: Request,
    background: BackgroundTasks,
    file: UploadFile = File(...),
    document_type: str = Form(...),
    current: CurrentUser = Depends(require_owner),
    session: Session = Depends(db_session),
) -> DocumentSchema:
    """Direct multipart upload (contract POST /documents). Prefer upload-init for large files."""
    try:
        dtype = DocumentType(document_type)
    except ValueError as exc:
        raise ValidationError("Unknown document_type.") from exc
    data = await file.read()
    doc = DocumentsService(session).multipart_upload(
        current=current, document_type=dtype, filename=file.filename or "upload",
        mime_type=file.content_type or "application/octet-stream", data=data, ip=_ip(request),
    )
    job = DocumentsRepository(session).get_latest_job(doc.id)
    if job is not None:
        background.add_task(run_job_until_terminal, job.id)
    return _to_document(doc)


@documents_router.get("/{document_id}", response_model=DocumentDetail)
def get_document(
    document_id: uuid.UUID,
    request: Request,
    current: CurrentUser = Depends(require_owner),
    session: Session = Depends(db_session),
) -> DocumentDetail:
    service = DocumentsService(session)
    doc = service.get_document(current=current, document_id=document_id, ip=_ip(request))
    repo = DocumentsRepository(session)
    extraction = repo.latest_extraction(doc.id)
    job = repo.get_latest_job(doc.id)
    fields_out: list[ExtractedFieldOut] = []
    if extraction is not None:
        for f in repo.fields_for_extraction(extraction.id):
            fields_out.append(
                ExtractedFieldOut(
                    field_name=f.field_name, value_type=f.value_type.value,
                    raw_value=f.raw_value, normalized_value=f.normalized_value,
                    verified_value=f.verified_value, confidence=float(f.confidence),
                    confidence_level=f.confidence_level.value, page_number=f.page_number,
                    text_span=f.text_span, bounding_box=f.bounding_box,
                    source=f.source.value, verification_status=f.verification_status.value,
                )
            )
    base = _to_document(doc)
    return DocumentDetail(
        **base.model_dump(),
        extracted_fields=(extraction.extracted_fields if extraction else {}),
        fields=fields_out,
        confidence=float(extraction.confidence) if extraction and extraction.confidence is not None else None,
        verified_by_citizen=extraction.verified_by_citizen if extraction else False,
        classified_type=extraction.classified_type.value if extraction and extraction.classified_type else None,
        identity_match=extraction.identity_match if extraction else None,
        conflicts=(extraction.conflicts or {}).get("items", []) if extraction and extraction.conflicts else [],
        processing_status=job.status.value if job else None,
    )


@documents_router.get("/{document_id}/download", response_model=DownloadResponse)
def download_document(
    document_id: uuid.UUID,
    request: Request,
    current: CurrentUser = Depends(require_owner),
    session: Session = Depends(db_session),
) -> DownloadResponse:
    result = DocumentsService(session).create_download(
        current=current, document_id=document_id, ip=_ip(request)
    )
    return DownloadResponse(**result)


@documents_router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: uuid.UUID,
    request: Request,
    current: CurrentUser = Depends(require_owner),
    session: Session = Depends(db_session),
) -> Response:
    DocumentsService(session).delete_document(current=current, document_id=document_id, ip=_ip(request))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@documents_router.post("/{document_id}/confirm", response_model=DocumentDetail)
def confirm_document(
    document_id: uuid.UUID,
    body: ConfirmInput,
    request: Request,
    current: CurrentUser = Depends(require_owner),
    session: Session = Depends(db_session),
) -> DocumentDetail:
    service = DocumentsService(session)
    doc = service.get_document_for_owner(current=current, document_id=document_id)
    VerificationService(session).verify(
        document=doc, action=body.action, corrected_fields=body.corrected_fields,
        correction_reason=body.correction_reason, actor_user_id=current.id, ip=_ip(request),
    )
    # Return refreshed detail.
    return get_document(document_id, request, current, session)
