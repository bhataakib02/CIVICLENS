"""Human verification workflow (prompt §30, §31).

confirm / correct / reject a document's extracted fields. A correction NEVER
overwrites raw_value/normalized_value — it sets verified_value + marks the field
CORRECTED, preserving the original extraction and full provenance. All outcomes
are audited; a DocumentVerification row records reviewer + outcome + reason.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models.document import Document, DocumentVerification
from app.models.enums import DocumentStatus, FieldVerificationStatus
from app.modules.audit.service import AuditAction, AuditService
from app.modules.documents.repository import DocumentsRepository

logger = get_logger("civiclens.documents.verification")

_VALID_ACTIONS = {"confirm", "correct", "reject"}


class VerificationService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._repo = DocumentsRepository(session)
        self._audit = AuditService(session)

    def verify(
        self,
        *,
        document: Document,
        action: str,
        corrected_fields: dict,
        correction_reason: str | None,
        actor_user_id: uuid.UUID,
        ip: str | None = None,
    ) -> Document:
        if action not in _VALID_ACTIONS:
            raise ValidationError(f"Invalid verification action '{action}'.")

        extraction = self._repo.latest_extraction(document.id)
        if extraction is None:
            raise NotFoundError("No extraction to verify for this document.")

        now = datetime.now(timezone.utc)
        outcome = FieldVerificationStatus.CONFIRMED

        if action == "reject":
            document.status = DocumentStatus.REJECTED
            outcome = FieldVerificationStatus.REJECTED
            audit_action = AuditAction.DOCUMENT_REJECTED
        else:
            fields = {f.field_name: f for f in self._repo.fields_for_extraction(extraction.id)}
            if action == "correct":
                outcome = FieldVerificationStatus.CORRECTED
                for name, new_value in (corrected_fields or {}).items():
                    field = fields.get(name)
                    if field is None:
                        continue
                    # Preserve original extraction; record the correction only.
                    field.verified_value = str(new_value)
                    field.verification_status = FieldVerificationStatus.CORRECTED
                    field.updated_at = now
            else:  # confirm
                for field in fields.values():
                    field.verification_status = FieldVerificationStatus.CONFIRMED
                    field.updated_at = now
            document.status = DocumentStatus.VERIFIED
            document.verified_at = now
            extraction.verified_by_citizen = True
            audit_action = AuditAction.DOCUMENT_VERIFIED

        self._session.add(
            DocumentVerification(
                document_id=document.id,
                verified_by=actor_user_id,
                outcome=outcome,
                correction_reason=(correction_reason or None),
                corrected_fields=(corrected_fields or None) if action == "correct" else None,
            )
        )
        self._session.flush()

        # Audit (no raw document content in metadata — only field names).
        self._audit.record(
            action=audit_action,
            entity_type="document",
            entity_id=document.id,
            actor_user_id=actor_user_id,
            diff={"action": action, "fields": sorted((corrected_fields or {}).keys())},
            ip=ip,
        )
        if action == "correct":
            self._audit.record(
                action=AuditAction.EXTRACTION_CORRECTED,
                entity_type="document_extraction",
                entity_id=extraction.id,
                actor_user_id=actor_user_id,
                diff={"fields": sorted((corrected_fields or {}).keys())},
                ip=ip,
            )
        self._session.commit()
        self._session.refresh(document)
        logger.info(
            "document_verified" if action != "reject" else "document_rejected",
            extra={"document_id": str(document.id), "action": action},
        )
        return document
