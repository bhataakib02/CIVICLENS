"""Schemes authorization policies (RBAC).

Scheme/version/rule mutation is restricted to scheme_admin/admin (FR-ADMIN-1).
Catalog reads are available to any authenticated user (citizens browse the
catalog). Object-level checks are not needed for the global catalog, but the
role gate is enforced here, server-side (docs/security/authorization-model.md).
"""
from __future__ import annotations

from app.models.enums import UserRole

# Roles permitted to author/administer schemes, versions, and rules.
SCHEME_ADMIN_ROLES = (UserRole.SCHEME_ADMIN.value, UserRole.ADMIN.value)
