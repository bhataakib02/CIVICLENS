"""Knowledge module dependencies (reuse shared auth dependencies)."""
from __future__ import annotations

from app.modules.auth.dependencies import require_authenticated_user, require_role
from app.modules.knowledge.policies import KNOWLEDGE_ADMIN_ROLES

require_knowledge_admin = require_role(*KNOWLEDGE_ADMIN_ROLES)
require_reader = require_authenticated_user
