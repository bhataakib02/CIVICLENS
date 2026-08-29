"""Eligibility HTTP routes.

    POST /eligibility/check   — evaluate the current citizen against one scheme
                                (or explicit scheme_version). Identity is
                                derived from the authenticated principal.

Idempotency (prompt §18): an optional `Idempotency-Key` header (consistent
with docs/api/idempotency.md) makes retries return the same persisted result
instead of creating duplicates.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.orm import Session

from app.db.session import db_session
from app.modules.auth.dependencies import CurrentUser, require_authenticated_user
from app.modules.eligibility.service import EligibilityService
from app.schemas.eligibility import EligibilityCheckInput, EligibilityResultOut

eligibility_router = APIRouter(prefix="/eligibility", tags=["eligibility"])


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@eligibility_router.post("/check", response_model=EligibilityResultOut)
def check_eligibility(
    body: EligibilityCheckInput,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    current: CurrentUser = Depends(require_authenticated_user),
    session: Session = Depends(db_session),
) -> EligibilityResultOut:
    result = EligibilityService(session).check(
        current=current,
        scheme_id=body.scheme_id,
        scheme_version_id=body.scheme_version_id,
        facts=body.facts,
        idempotency_key=idempotency_key,
        ip=_ip(request),
    )
    return EligibilityResultOut(**result)
