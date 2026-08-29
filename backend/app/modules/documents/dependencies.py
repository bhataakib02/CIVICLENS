"""Documents module dependencies (reuse shared auth)."""
from __future__ import annotations

from app.modules.auth.dependencies import require_authenticated_user

require_owner = require_authenticated_user
