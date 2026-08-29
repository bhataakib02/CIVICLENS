"""Document evidence -> eligibility integration (prompt §29, §32, §52).

Collects VERIFIED/CONFIRMED document-extracted fields for a citizen and maps
them to canonical eligibility field_keys, so they can be passed to the existing
ContextBuilder as `extra_facts`. The rule engine remains the sole decider
(PASS/FAIL/UNKNOWN); this module only supplies evidence.

Only fields that are verified (auto-accepted at HIGH confidence, or
citizen-confirmed/corrected) contribute — unverified low-confidence extractions
never silently drive eligibility (FR-DOCS-3). Verified corrections take
precedence over the raw extracted value.

The facts are returned with an intended source of DOCUMENT_EXTRACTED; when fed
to ContextBuilder they are labeled distinctly from profile facts, so the
engine's existing conflict detection flags profile-vs-document disagreement
rather than silently overriding the profile.
"""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document, DocumentExtractedField
from app.models.enums import DocumentStatus, FieldVerificationStatus

# Extracted field_name -> canonical eligibility field_key.
_FIELD_MAP = {
    "annual_income": "declared_annual_income",
    "state": "state",
    "district": "district",
    "postal_code": "pincode",
    "date_of_birth": "date_of_birth",
}

_VERIFIED_STATUSES = {
    FieldVerificationStatus.AUTO_ACCEPTED,
    FieldVerificationStatus.CONFIRMED,
    FieldVerificationStatus.CORRECTED,
}


class DocumentFactsProvider:
    """Reads verified document facts for a citizen profile."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def verified_facts(self, citizen_profile_id: uuid.UUID) -> dict:
        """Return {canonical_field_key: value} from VERIFIED documents only.

        Value precedence: a citizen-corrected verified_value overrides the
        normalized extracted value. States are already normalized (e.g.
        WEST_BENGAL); we map them back to a comparable form for the engine by
        using the normalized value as-is (the engine compares against the
        profile's address state via the same normalizer downstream).
        """
        stmt = (
            select(DocumentExtractedField)
            .join(Document, DocumentExtractedField.document_id == Document.id)
            .where(
                Document.citizen_profile_id == citizen_profile_id,
                Document.status == DocumentStatus.VERIFIED,
                Document.deleted_at.is_(None),
                DocumentExtractedField.verification_status.in_(list(_VERIFIED_STATUSES)),
                DocumentExtractedField.field_name.in_(list(_FIELD_MAP.keys())),
            )
            .order_by(DocumentExtractedField.updated_at.desc())
        )
        facts: dict = {}
        for f in self._session.scalars(stmt):
            key = _FIELD_MAP.get(f.field_name)
            if key is None or key in facts:
                continue
            value = f.verified_value if f.verified_value is not None else f.normalized_value
            if value is None:
                continue
            facts[key] = _coerce(key, value)
        return facts


def _coerce(field_key: str, value: str):
    if field_key == "declared_annual_income":
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
    return value
