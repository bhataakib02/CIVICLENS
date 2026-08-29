"""Consent HTTP endpoints."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.db.session import db_session
from app.modules.auth.dependencies import CurrentUser, require_authenticated_user
from app.modules.consents.schemas import ConsentOut, GrantConsentInput
from app.modules.consents.service import ConsentService

consents_router = APIRouter(prefix="/me/consents", tags=["consents"])


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@consents_router.get("", response_model=list[ConsentOut])
def list_consents(
    current: CurrentUser = Depends(require_authenticated_user),
    session: Session = Depends(db_session),
) -> list[ConsentOut]:
    return [ConsentOut.model_validate(c) for c in ConsentService(session).list_consents(current.id)]


@consents_router.post("", response_model=ConsentOut, status_code=status.HTTP_201_CREATED)
def grant_consent(
    body: GrantConsentInput,
    request: Request,
    current: CurrentUser = Depends(require_authenticated_user),
    session: Session = Depends(db_session),
) -> ConsentOut:
    consent = ConsentService(session).grant_consent(current.id, body, ip=_ip(request))
    return ConsentOut.model_validate(consent)


@consents_router.post("/{consent_id}/revoke", response_model=ConsentOut)
def revoke_consent(
    consent_id: uuid.UUID,
    request: Request,
    current: CurrentUser = Depends(require_authenticated_user),
    session: Session = Depends(db_session),
) -> ConsentOut:
    consent = ConsentService(session).revoke_consent(current.id, consent_id, ip=_ip(request))
    return ConsentOut.model_validate(consent)
