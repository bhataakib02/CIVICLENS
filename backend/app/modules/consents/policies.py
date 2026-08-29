"""Authorization policy for Consent management & Agent access."""
from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import PermissionDeniedError
from app.models.enums import UserRole
from app.modules.auth.dependencies import CurrentUser
from app.modules.consents.repository import ConsentRepository


def verify_agent_consent(
    session: Session, agent_user: CurrentUser, citizen_profile_id: uuid.UUID
) -> None:
    """Verify that an AGENT has an active (non-revoked) consent to access a citizen's profile.

    Admins bypass agent authorization check.
    Citizens acting for themselves bypass this check.
    AGENTS must have active AGENT_ASSISTANCE consent.
    """
    if agent_user.role == UserRole.ADMIN.value:
        return

    if agent_user.role != UserRole.AGENT.value:
        raise PermissionDeniedError("Only authorized AGENT or ADMIN can access citizen resources.")

    repo = ConsentRepository(session)
    consent = repo.get_active_agent_consent(citizen_id=citizen_profile_id, agent_id=agent_user.id)
    if consent is None:
        raise PermissionDeniedError(
            "Agent does not have active citizen consent to perform actions for this citizen."
        )
