"""Eligibility authorization policies.

- A citizen may only evaluate eligibility for THEMSELVES; identity is derived
  from the authenticated principal, never from a client-supplied citizen_id
  (prompt §16, threat-model.md #2/#6).
- Agents/admins may evaluate on behalf of a citizen per RBAC (agent-assist),
  but in this slice we scope evaluation to the caller's own profile for
  citizens and allow staff roles to target a profile explicitly (kept minimal;
  broader agent-consent flow is a later phase).
"""
from __future__ import annotations

from app.models.enums import UserRole

STAFF_ROLES = (UserRole.AGENT.value, UserRole.SCHEME_ADMIN.value, UserRole.ADMIN.value)
