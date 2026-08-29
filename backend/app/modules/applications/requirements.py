"""Document requirements + readiness checklist (prompt §11-§15, §34).

Requirements ORIGINATE from scheme configuration (document_requirements rows for
the pinned scheme_version) — never hardcoded here. The checklist maps each
required/optional document type to a readiness status derived deterministically
from the citizen's attached documents:

    MISSING | UPLOADED | PROCESSING | VERIFICATION_REQUIRED | VERIFIED | REJECTED | EXPIRED

A requirement is satisfied only by a VERIFIED (non-expired) document. PROCESSING
/ VERIFICATION_REQUIRED / REJECTED / EXPIRED do NOT satisfy it.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.application import ApplicationDocument
from app.models.document import Document, DocumentExtractedField
from app.models.document_requirement import DocumentRequirement
from app.models.enums import ChecklistItemStatus, DocumentStatus

# Map a Document lifecycle status -> checklist status.
_DOC_STATUS_TO_CHECKLIST = {
    DocumentStatus.UPLOADING: ChecklistItemStatus.UPLOADED,
    DocumentStatus.UPLOADED: ChecklistItemStatus.UPLOADED,
    DocumentStatus.VALIDATING: ChecklistItemStatus.PROCESSING,
    DocumentStatus.PROCESSING: ChecklistItemStatus.PROCESSING,
    DocumentStatus.EXTRACTED: ChecklistItemStatus.PROCESSING,
    DocumentStatus.VERIFICATION_REQUIRED: ChecklistItemStatus.VERIFICATION_REQUIRED,
    DocumentStatus.VERIFIED: ChecklistItemStatus.VERIFIED,
    DocumentStatus.VALIDATION_FAILED: ChecklistItemStatus.REJECTED,
    DocumentStatus.PROCESSING_FAILED: ChecklistItemStatus.REJECTED,
    DocumentStatus.REJECTED: ChecklistItemStatus.REJECTED,
}

_SATISFYING = {ChecklistItemStatus.VERIFIED}


@dataclass
class ChecklistItem:
    document_type: str
    required: bool
    status: ChecklistItemStatus
    document_id: uuid.UUID | None = None
    notes: str | None = None


@dataclass
class Checklist:
    items: list[ChecklistItem] = field(default_factory=list)

    @property
    def all_required_satisfied(self) -> bool:
        return all(i.status in _SATISFYING for i in self.items if i.required)

    @property
    def has_requirements(self) -> bool:
        return any(i.required for i in self.items)


class RequirementsService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def requirements_for_version(self, scheme_version_id: uuid.UUID) -> list[DocumentRequirement]:
        stmt = select(DocumentRequirement).where(
            DocumentRequirement.scheme_version_id == scheme_version_id
        )
        return list(self._session.scalars(stmt))

    def build_checklist(
        self,
        *,
        scheme_version_id: uuid.UUID,
        citizen_profile_id: uuid.UUID,
        application_id: uuid.UUID | None,
        as_of: date | None = None,
    ) -> Checklist:
        as_of = as_of or date.today()
        reqs = self.requirements_for_version(scheme_version_id)

        # Candidate documents: those attached to the application (if any),
        # else the citizen's documents of the required type (reuse policy §13).
        attached = self._attached_documents(application_id) if application_id else {}

        items: list[ChecklistItem] = []
        for req in reqs:
            dtype = req.document_type.value
            doc = attached.get(dtype) or self._best_citizen_document(citizen_profile_id, dtype)
            if doc is None:
                items.append(ChecklistItem(document_type=dtype, required=req.is_mandatory,
                                           status=ChecklistItemStatus.MISSING, notes=req.notes))
                continue
            status = _DOC_STATUS_TO_CHECKLIST.get(doc.status, ChecklistItemStatus.UPLOADED)
            # Expiry check (§34): a VERIFIED doc past its issue/validity date is EXPIRED.
            if status is ChecklistItemStatus.VERIFIED and self._is_expired(doc, as_of):
                status = ChecklistItemStatus.EXPIRED
            items.append(ChecklistItem(document_type=dtype, required=req.is_mandatory,
                                       status=status, document_id=doc.id, notes=req.notes))
        return Checklist(items=items)

    # ------------------------------------------------------------------ #
    def _attached_documents(self, application_id: uuid.UUID) -> dict[str, Document]:
        stmt = (
            select(Document)
            .join(ApplicationDocument, ApplicationDocument.document_id == Document.id)
            .where(ApplicationDocument.application_id == application_id, Document.deleted_at.is_(None))
        )
        out: dict[str, Document] = {}
        for doc in self._session.scalars(stmt):
            out.setdefault(doc.document_type.value, doc)
        return out

    def _best_citizen_document(self, citizen_profile_id: uuid.UUID, dtype: str) -> Document | None:
        """Most recent non-deleted document of this type for the citizen,
        preferring VERIFIED."""
        stmt = (
            select(Document)
            .where(
                Document.citizen_profile_id == citizen_profile_id,
                Document.document_type == dtype,
                Document.deleted_at.is_(None),
            )
            .order_by(Document.created_at.desc())
        )
        docs = list(self._session.scalars(stmt))
        verified = [d for d in docs if d.status is DocumentStatus.VERIFIED]
        return verified[0] if verified else (docs[0] if docs else None)

    def _is_expired(self, doc: Document, as_of: date) -> bool:
        """A document is EXPIRED if an extracted validity/issue-derived expiry
        date has passed. We look for a normalized 'valid_until' / 'expiry_date'
        extracted field; absent one, it is not considered expired (we never
        invent an expiry)."""
        stmt = (
            select(DocumentExtractedField)
            .where(
                DocumentExtractedField.document_id == doc.id,
                DocumentExtractedField.field_name.in_(["valid_until", "expiry_date"]),
            )
        )
        for f in self._session.scalars(stmt):
            val = f.verified_value or f.normalized_value
            if val:
                try:
                    if date.fromisoformat(val) < as_of:
                        return True
                except ValueError:
                    continue
        return False
