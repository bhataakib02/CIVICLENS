"""Document authorization policies (prompt §2, §10).

Object-level: a document is accessible only to its owning citizen (derived from
the authenticated principal's profile), or to staff (agent/admin) per RBAC.
Ownership is NEVER taken from a client-supplied user_id.
"""
from __future__ import annotations

from app.models.enums import UserRole

STAFF_ROLES = (UserRole.AGENT.value, UserRole.SCHEME_ADMIN.value, UserRole.ADMIN.value)


def can_access_document(*, current_role: str, current_profile_id, document_profile_id) -> bool:
    if current_role in STAFF_ROLES:
        return True
    return current_profile_id is not None and current_profile_id == document_profile_id
