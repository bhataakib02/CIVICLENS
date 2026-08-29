"""Shared response schemas — error envelope matches openapi.yaml #/schemas/Error."""
from __future__ import annotations

from pydantic import BaseModel


class FieldError(BaseModel):
    field: str
    message: str


class ErrorBody(BaseModel):
    code: str
    message: str
    request_id: str
    field_errors: list[FieldError] | None = None


class ErrorResponse(BaseModel):
    """Stable error envelope: {"error": {...}}."""

    error: ErrorBody
