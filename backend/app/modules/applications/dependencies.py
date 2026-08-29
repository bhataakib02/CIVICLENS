"""Applications module dependencies (reuse shared auth)."""
from __future__ import annotations

from app.modules.applications.policies import ADMIN_ROLE, CASE_WORKER_ROLE
from app.modules.auth.dependencies import require_authenticated_user, require_role

require_user = require_authenticated_user
require_reviewer = require_role(CASE_WORKER_ROLE, ADMIN_ROLE)
require_admin = require_role(ADMIN_ROLE)
