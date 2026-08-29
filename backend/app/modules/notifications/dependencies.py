"""Notification module dependencies."""
from __future__ import annotations

from app.modules.auth.dependencies import CurrentUser, require_authenticated_user

__all__ = ["CurrentUser", "require_authenticated_user"]
