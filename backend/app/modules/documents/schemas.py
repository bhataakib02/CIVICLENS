"""Document API schemas (Pydantic v2).

Conform to openapi.yaml Document/DocumentDetail (extended deliberately). NEVER
expose storage_key, internal paths, or credentials.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import DocumentType


class UploadInitInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_type: DocumentType
    filename: str = Field(min_length=1, max_length=255)
    mime_type: str = Field(min_length=1, max_length=128)
    size_bytes: int = Field(ge=1)


class UploadInitResponse(BaseModel):
    document_id: str
    upload_url: str
    method: str
    headers: dict[str, str]
    expires_at: int


class UploadCompleteInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # sha256 optional client-provided integrity hint; server recomputes.
    sha256: str | None = Field(default=None, max_length=64)


class Document(BaseModel):
    """Matches openapi #/schemas/Document (extended fields, no storage_key)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    document_type: DocumentType
    status: str
    filename: str | None = None
    mime_type: str | None = None
    size_bytes: int | None = None
    uploaded_at: datetime | None = None
    created_at: datetime


class ExtractedFieldOut(BaseModel):
    field_name: str
    value_type: str
    raw_value: str | None = None
    normalized_value: str | None = None
    verified_value: str | None = None
    confidence: float
    confidence_level: str
    page_number: int | None = None
    text_span: str | None = None
    bounding_box: dict | None = None
    source: str
    verification_status: str


class DocumentDetail(Document):
    extracted_fields: dict[str, Any] = Field(default_factory=dict)
    fields: list[ExtractedFieldOut] = Field(default_factory=list)
    confidence: float | None = None
    verified_by_citizen: bool = False
    classified_type: str | None = None
    identity_match: bool | None = None
    conflicts: list[dict] = Field(default_factory=list)
    processing_status: str | None = None


class DownloadResponse(BaseModel):
    download_url: str
    expires_at: int


class ConfirmInput(BaseModel):
    """POST /documents/{id}/confirm — confirm or correct extracted fields."""

    model_config = ConfigDict(extra="forbid")

    action: str = Field(default="confirm")  # confirm | correct | reject
    corrected_fields: dict[str, Any] = Field(default_factory=dict)
    correction_reason: str | None = None
