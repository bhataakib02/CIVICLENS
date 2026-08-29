"""Knowledge authorization policies (prompt §29, §34).

Ingestion/verification/re-ingestion: scheme_admin/admin only (citizens must
never ingest arbitrary sources — SSRF/RAG-poisoning surface). Search/assistant:
any authenticated user, but only authoritative (verified official/secondary)
sources are surfaced as evidence to non-staff.
"""
from __future__ import annotations

from app.models.enums import UserRole

KNOWLEDGE_ADMIN_ROLES = (UserRole.SCHEME_ADMIN.value, UserRole.ADMIN.value)
STAFF_ROLES = (UserRole.AGENT.value, UserRole.SCHEME_ADMIN.value, UserRole.ADMIN.value)
