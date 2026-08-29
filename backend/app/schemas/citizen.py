"""Citizen profile + address schemas — conform to openapi.yaml.

Field names follow the authoritative contract / data-dictionary:
declared_annual_income, family_size, category, occupation, date_of_birth,
gender, disability_status; addresses use type/state/district/pincode/line1.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import AddressType

# ------------------------------ Citizen profile ---------------------------- #


class CitizenProfile(BaseModel):
    """Matches openapi.yaml #/schemas/CitizenProfile."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    date_of_birth: date | None = None
    gender: str | None = None
    category: str | None = None
    occupation: str | None = None
    declared_annual_income: Decimal | None = None
    disability_status: bool | None = None
    family_size: int | None = None
    profile_completeness: float = Field(ge=0.0, le=1.0)
    current_version_no: int


class CitizenProfileUpdate(BaseModel):
    """Editable subset of CitizenProfile (progressive profiling).

    All fields optional; only provided fields are applied. `income >= 0`,
    `family_size >= 1` enforced per the prompt.
    """

    model_config = ConfigDict(extra="forbid")

    date_of_birth: date | None = None
    gender: str | None = None
    category: str | None = None
    occupation: str | None = None
    declared_annual_income: Decimal | None = Field(default=None, ge=0)
    disability_status: bool | None = None
    family_size: int | None = Field(default=None, ge=1)

    @field_validator("date_of_birth")
    @classmethod
    def _dob_not_future(cls, value: date | None) -> date | None:
        if value is not None and value > date.today():
            raise ValueError("date_of_birth cannot be in the future.")
        return value


# --------------------------------- Addresses -------------------------------- #

_PINCODE_LEN = 6


class AddressInput(BaseModel):
    """Matches openapi.yaml #/schemas/AddressInput."""

    model_config = ConfigDict(extra="forbid")

    type: AddressType
    state: str = Field(min_length=1, max_length=64)
    district: str = Field(min_length=1, max_length=64)
    pincode: str
    line1: str = Field(min_length=1)
    is_primary: bool = False

    @field_validator("pincode")
    @classmethod
    def _validate_pincode(cls, value: str) -> str:
        value = value.strip()
        if len(value) != _PINCODE_LEN or not value.isdigit():
            raise ValueError("pincode must be exactly 6 digits.")
        return value


class AddressUpdate(BaseModel):
    """Partial update for an existing address (extension: PUT/PATCH address)."""

    model_config = ConfigDict(extra="forbid")

    type: AddressType | None = None
    state: str | None = Field(default=None, min_length=1, max_length=64)
    district: str | None = Field(default=None, min_length=1, max_length=64)
    pincode: str | None = None
    line1: str | None = Field(default=None, min_length=1)
    is_primary: bool | None = None

    @field_validator("pincode")
    @classmethod
    def _validate_pincode(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if len(value) != _PINCODE_LEN or not value.isdigit():
            raise ValueError("pincode must be exactly 6 digits.")
        return value


class Address(BaseModel):
    """Matches openapi.yaml #/schemas/Address (+ is_primary extension)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    type: AddressType
    state: str
    district: str
    pincode: str
    line1: str
    is_primary: bool
