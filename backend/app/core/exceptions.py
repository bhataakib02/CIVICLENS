"""Domain/application exceptions and the stable error contract.

All API errors surface through the envelope defined in
docs/api/error-handling.md and openapi.yaml #/components/schemas/Error:

    {"error": {"code": ..., "message": ..., "request_id": ..., "field_errors"?: [...]}}

Never leak stack traces, SQL, secrets, or internal paths to clients.
"""
from __future__ import annotations


class AppError(Exception):
    """Base class for all application errors that map to an error envelope.

    Attributes:
        status_code: HTTP status to return.
        code: stable machine-readable error code (SCREAMING_SNAKE_CASE).
        message: safe, human-readable message (no internal details).
    """

    status_code: int = 500
    code: str = "INTERNAL_ERROR"
    message: str = "An unexpected error occurred."

    def __init__(self, message: str | None = None, *, code: str | None = None) -> None:
        if message is not None:
            self.message = message
        if code is not None:
            self.code = code
        super().__init__(self.message)


class ValidationError(AppError):
    status_code = 422
    code = "VALIDATION_ERROR"
    message = "Request failed validation."

    def __init__(self, message: str | None = None, *, field_errors: list[dict] | None = None):
        super().__init__(message)
        self.field_errors = field_errors or []


class AuthenticationError(AppError):
    status_code = 401
    code = "INVALID_CREDENTIALS"
    message = "Authentication failed."


class InvalidTokenError(AppError):
    status_code = 401
    code = "INVALID_TOKEN"
    message = "The provided token is invalid or expired."


class AccountSuspendedError(AppError):
    status_code = 403
    code = "ACCOUNT_SUSPENDED"
    message = "This account is suspended."


class PermissionDeniedError(AppError):
    status_code = 403
    code = "PERMISSION_DENIED"
    message = "You do not have permission to access this resource."


class NotFoundError(AppError):
    status_code = 404
    code = "NOT_FOUND"
    message = "The requested resource does not exist."


class ConflictError(AppError):
    status_code = 409
    code = "CONFLICT"
    message = "The request conflicts with existing state."


class AccountExistsError(ConflictError):
    code = "ACCOUNT_EXISTS"
    message = "An account with these details already exists. Please log in instead."
