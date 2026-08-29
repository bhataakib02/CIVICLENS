"""Audit logging service.

Writes immutable audit_logs rows for authentication-sensitive and
data-changing operations. Never records passwords, raw JWTs, refresh tokens,
or PII in `diff` (docs/security/audit-logging.md). IPs are hashed.

The service flushes rows into the caller's Session but does NOT commit — it
participates in the caller's transaction so an audit row and the action it
records commit atomically (or roll back together).
"""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.core.security import hash_ip
from app.models.audit_log import AuditLog


class AuditAction:
    REGISTER = "auth.register"
    LOGIN_SUCCESS = "auth.login_success"
    LOGIN_FAILURE = "auth.login_failure"
    TOKEN_REFRESH = "auth.token_refresh"
    TOKEN_REUSE_DETECTED = "auth.token_reuse_detected"
    LOGOUT = "auth.logout"
    OTP_REQUEST = "auth.otp_request"
    OTP_VERIFY_SUCCESS = "auth.otp_verify_success"
    OTP_VERIFY_FAILURE = "auth.otp_verify_failure"
    # Consent management.
    CONSENT_GRANTED = "consent.granted"
    CONSENT_REVOKED = "consent.revoked"
    PROFILE_UPDATE = "citizen.profile_update"
    ADDRESS_CREATE = "citizen.address_create"
    ADDRESS_UPDATE = "citizen.address_update"
    ADDRESS_DELETE = "citizen.address_delete"
    # Schemes / eligibility (Prompt 2).
    SCHEME_CREATE = "scheme.create"
    SCHEME_VERSION_CREATE = "scheme_version.create"
    SCHEME_VERSION_RULES_SET = "scheme_version.rules_set"
    SCHEME_VERSION_PUBLISH = "scheme_version.publish"
    SCHEME_VERSION_SUPERSEDE = "scheme_version.supersede"
    SCHEME_VERSION_ARCHIVE = "scheme_version.archive"
    RULE_VALIDATION_FAILED = "eligibility.rule_validation_failed"
    ELIGIBILITY_CHECK = "eligibility.check"
    # Knowledge / RAG (Prompt 3).
    KNOWLEDGE_SOURCE_INGEST_REQUESTED = "knowledge.source_ingest_requested"
    KNOWLEDGE_SOURCE_VERIFIED = "knowledge.source_verified"
    KNOWLEDGE_SEARCH = "knowledge.search"
    ASSISTANT_QUERY = "assistant.query"
    # Documents (Prompt 4).
    DOCUMENT_UPLOAD_INIT = "document.upload_init"
    DOCUMENT_UPLOADED = "document.uploaded"
    DOCUMENT_VALIDATION_FAILED = "document.validation_failed"
    DOCUMENT_PROCESSING_STARTED = "document.processing_started"
    DOCUMENT_PROCESSING_COMPLETED = "document.processing_completed"
    DOCUMENT_PROCESSING_FAILED = "document.processing_failed"
    DOCUMENT_VIEWED = "document.viewed"
    DOCUMENT_DOWNLOADED = "document.downloaded"
    DOCUMENT_DELETED = "document.deleted"
    DOCUMENT_VERIFIED = "document.verified"
    DOCUMENT_REJECTED = "document.rejected"
    EXTRACTION_CORRECTED = "document.extraction_corrected"
    IDENTITY_MISMATCH_DETECTED = "document.identity_mismatch_detected"
    FACT_CONFLICT_DETECTED = "document.fact_conflict_detected"
    # Applications / case management (Prompt 5).
    APPLICATION_CREATED = "application.created"
    APPLICATION_UPDATED = "application.updated"
    APPLICATION_SUBMITTED = "application.submitted"
    APPLICATION_ASSIGNED = "application.assigned"
    APPLICATION_REASSIGNED = "application.reassigned"
    APPLICATION_UNASSIGNED = "application.unassigned"
    APPLICATION_REVIEWED = "application.reviewed"
    APPLICATION_ACTION_REQUIRED = "application.action_required"
    APPLICATION_ACTION_RESOLVED = "application.action_resolved"
    APPLICATION_APPROVED = "application.approved"
    APPLICATION_REJECTED = "application.rejected"
    APPLICATION_WITHDRAWN = "application.withdrawn"
    APPLICATION_COMPLETED = "application.completed"
    APPLICATION_SUBMISSION_FAILED = "application.submission_failed"
    # Notifications / real-time (Prompt 6).
    NOTIFICATION_CREATED = "notification.created"
    NOTIFICATION_SENT = "notification.sent"
    NOTIFICATION_FAILED = "notification.failed"
    NOTIFICATION_READ = "notification.read"
    NOTIFICATION_PREFERENCES_CHANGED = "notification.preferences_changed"
    REALTIME_CONNECTION_ESTABLISHED = "realtime.connection_established"


# Keys that must never appear in audit metadata even if a caller passes them.
_FORBIDDEN_META_KEYS = frozenset(
    {"password", "password_hash", "access_token", "refresh_token", "token", "jwt"}
)


def _sanitize(meta: dict[str, Any] | None) -> dict[str, Any] | None:
    if not meta:
        return None
    return {k: v for k, v in meta.items() if k.lower() not in _FORBIDDEN_META_KEYS}


class AuditService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def record(
        self,
        *,
        action: str,
        entity_type: str,
        entity_id: uuid.UUID | None = None,
        actor_user_id: uuid.UUID | None = None,
        diff: dict[str, Any] | None = None,
        ip: str | None = None,
    ) -> AuditLog:
        """Append an audit row to the current transaction (flush, no commit)."""
        payload = _sanitize(diff) or {}
        hashed = hash_ip(ip)
        if hashed:
            payload = {**payload, "ip_hash": hashed}
        entry = AuditLog(
            actor_user_id=actor_user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            diff=payload or None,
        )
        self._session.add(entry)
        self._session.flush()
        return entry
