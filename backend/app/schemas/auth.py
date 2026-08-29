"""Auth schemas.

TokenPair matches openapi.yaml #/schemas/TokenPair exactly.
RegisterInput / LoginInput back the email+password endpoints added to the
contract as a documented extension (FR-AUTH-1 allows email+password).
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=1)  # policy enforced in the service layer


class LoginInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=1)


class OTPRequestInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phone_number: str = Field(min_length=7, max_length=20)


class OTPVerifyInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phone_number: str = Field(min_length=7, max_length=20)
    code: str = Field(min_length=1, max_length=10)


class RefreshInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    refresh_token: str = Field(min_length=1)


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class MeResponse(BaseModel):
    """Authenticated principal summary for GET /me (contract returns CitizenProfile
    for the citizen persona; this exposes the account-level view used by the
    extension /me identity needs). Contains no secrets."""

    id: str
    email: str | None = None
    phone_number: str | None = None
    role: str
    status: str
