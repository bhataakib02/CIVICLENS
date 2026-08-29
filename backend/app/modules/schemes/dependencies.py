"""Schemes module dependencies (reuse the shared auth dependencies)."""
from __future__ import annotations

from app.modules.auth.dependencies import require_authenticated_user, require_role
from app.modules.schemes.policies import SCHEME_ADMIN_ROLES

# Admin gate for scheme/version/rule mutation.
require_scheme_admin = require_role(*SCHEME_ADMIN_ROLES)

# Any authenticated user may read the catalog.
require_reader = require_authenticated_user
