"""Application authorization policies (prompt §22, §30, §31).

- Citizen: own applications only (by citizen_profile_id).
- Case worker (role 'agent'): ASSIGNED applications only — not every citizen's.
- Admin: applications permitted by administrative policy (all, but through the
  same object-level check function, never a raw "return all rows" shortcut).

`agent` is CivicLens's case-worker role (data-dictionary user_role enum).
Object-level checks are enforced in the service before any read/write.
"""
from __future__ import annotations

import uuid

from app.models.enums import UserRole

CASE_WORKER_ROLE = UserRole.AGENT.value
ADMIN_ROLE = UserRole.ADMIN.value
REVIEWER_ROLES = {CASE_WORKER_ROLE, ADMIN_ROLE}


def can_view_application(
    *,
    role: str,
    current_user_id: uuid.UUID,
    current_profile_id: uuid.UUID | None,
    owner_profile_id: uuid.UUID,
    assigned_case_worker_id: uuid.UUID | None,
) -> bool:
    if role == ADMIN_ROLE:
        return True
    if role == CASE_WORKER_ROLE:
        return assigned_case_worker_id is not None and assigned_case_worker_id == current_user_id
    # citizen
    return current_profile_id is not None and current_profile_id == owner_profile_id


def can_review_application(
    *, role: str, current_user_id: uuid.UUID, assigned_case_worker_id: uuid.UUID | None
) -> bool:
    if role == ADMIN_ROLE:
        return True
    if role == CASE_WORKER_ROLE:
        return assigned_case_worker_id is not None and assigned_case_worker_id == current_user_id
    return False


def can_assign(role: str) -> bool:
    # Only admins manage assignment in this phase (explicit, no auto-allocation).
    return role == ADMIN_ROLE
