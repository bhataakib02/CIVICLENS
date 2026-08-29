"""Verification policies.

A citizen may confirm/correct/reject their OWN document's extraction. Staff
(agent/admin) may verify per RBAC. Ownership is enforced in the service via the
shared object-level check before this is reached.
"""
from __future__ import annotations

from app.models.enums import UserRole

STAFF_ROLES = (UserRole.AGENT.value, UserRole.SCHEME_ADMIN.value, UserRole.ADMIN.value)
