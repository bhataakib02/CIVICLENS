"""Consent repository layer."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.consent import ConsentRecord, ConsentType


class ConsentRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add_consent(self, consent: ConsentRecord) -> ConsentRecord:
        self._session.add(consent)
        self._session.flush()
        return consent

    def get_by_id(self, consent_id: uuid.UUID) -> ConsentRecord | None:
        return self._session.get(ConsentRecord, consent_id)

    def list_by_citizen(self, citizen_id: uuid.UUID) -> list[ConsentRecord]:
        stmt = (
            select(ConsentRecord)
            .where(ConsentRecord.citizen_id == citizen_id)
            .order_by(ConsentRecord.granted_at.desc())
        )
        return list(self._session.scalars(stmt))

    def get_active_agent_consent(
        self, citizen_id: uuid.UUID, agent_id: uuid.UUID
    ) -> ConsentRecord | None:
        stmt = select(ConsentRecord).where(
            ConsentRecord.citizen_id == citizen_id,
            ConsentRecord.agent_id == agent_id,
            ConsentRecord.consent_type == ConsentType.AGENT_ASSISTANCE,
            ConsentRecord.revoked_at.is_(None),
        )
        return self._session.scalar(stmt)
