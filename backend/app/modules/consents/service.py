"""Consent application service."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.models.consent import ConsentRecord
from app.modules.audit.service import AuditAction, AuditService
from app.modules.citizens.service import CitizensService
from app.modules.consents.repository import ConsentRepository
from app.modules.consents.schemas import GrantConsentInput


class ConsentService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._repo = ConsentRepository(session)
        self._audit = AuditService(session)

    def grant_consent(
        self, citizen_user_id: uuid.UUID, body: GrantConsentInput, *, ip: str | None = None
    ) -> ConsentRecord:
        profile = CitizensService(self._session).get_profile(citizen_user_id)
        profile_uuid = uuid.UUID(profile.id) if isinstance(profile.id, str) else profile.id
        consent = ConsentRecord(
            citizen_id=profile_uuid,
            consent_type=body.consent_type,
            purpose=body.purpose,
            scope=body.scope,
            version=body.version,
            actor_id=citizen_user_id,
            agent_id=body.agent_id,
        )
        self._repo.add_consent(consent)
        self._audit.record(
            action=AuditAction.CONSENT_GRANTED,
            entity_type="consent",
            entity_id=consent.id,
            actor_user_id=citizen_user_id,
            diff={"consent_type": body.consent_type.value, "agent_id": str(body.agent_id) if body.agent_id else None},
            ip=ip,
        )
        self._session.commit()
        self._session.refresh(consent)
        return consent

    def revoke_consent(
        self, citizen_user_id: uuid.UUID, consent_id: uuid.UUID, *, ip: str | None = None
    ) -> ConsentRecord:
        profile = CitizensService(self._session).get_profile(citizen_user_id)
        profile_uuid = uuid.UUID(profile.id) if isinstance(profile.id, str) else profile.id
        consent = self._repo.get_by_id(consent_id)
        if consent is None or consent.citizen_id != profile_uuid:
            raise NotFoundError("Consent record not found.")

        if consent.revoked_at is not None:
            return consent

        consent.revoked_at = datetime.now(timezone.utc)
        self._audit.record(
            action=AuditAction.CONSENT_REVOKED,
            entity_type="consent",
            entity_id=consent.id,
            actor_user_id=citizen_user_id,
            diff={"consent_type": consent.consent_type.value},
            ip=ip,
        )
        self._session.commit()
        self._session.refresh(consent)
        return consent

    def list_consents(self, citizen_user_id: uuid.UUID) -> list[ConsentRecord]:
        profile = CitizensService(self._session).get_profile(citizen_user_id)
        profile_uuid = uuid.UUID(profile.id) if isinstance(profile.id, str) else profile.id
        return self._repo.list_by_citizen(profile_uuid)
