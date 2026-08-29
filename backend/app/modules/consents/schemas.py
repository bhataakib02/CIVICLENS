"""Consent schemas."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.consent import ConsentType


class GrantConsentInput(BaseModel):
    consent_type: ConsentType
    purpose: str = Field(min_length=1)
    scope: dict | None = None
    agent_id: uuid.UUID | None = None
    version: str = "1.0"


class ConsentOut(BaseModel):
    id: uuid.UUID
    citizen_id: uuid.UUID
    consent_type: ConsentType
    purpose: str
    scope: dict | None
    version: str
    actor_id: uuid.UUID | None
    agent_id: uuid.UUID | None
    granted_at: datetime
    revoked_at: datetime | None = None

    class Config:
        from_attributes = True
