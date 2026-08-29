"""Citizens application service — profile + address business logic.

Object-level authorization: every read/write is scoped to the authenticated
user's own citizen_profile. Ownership is derived from the principal, never
from a client-supplied id (docs/security/authorization-model.md,
threat-model.md #2). A cross-citizen address access yields NOT_FOUND (we do
not confirm existence of another citizen's resource).

Profile edits are versioned (FR-PROFILE-5): each successful update writes an
immutable snapshot and advances current_version_no.
"""
from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.address import Address
from app.models.citizen_profile import CitizenProfile, CitizenProfileVersion
from app.modules.audit.service import AuditAction, AuditService
from app.modules.citizens.repository import CitizensRepository
from app.schemas.citizen import (
    Address as AddressSchema,
    AddressInput,
    AddressUpdate,
    CitizenProfile as CitizenProfileSchema,
    CitizenProfileUpdate,
)

# Fields that count toward profile completeness (progressive profiling).
_COMPLETENESS_FIELDS = (
    "date_of_birth",
    "gender",
    "category",
    "occupation",
    "declared_annual_income",
    "disability_status",
    "family_size",
)


def _completeness(profile: CitizenProfile) -> float:
    filled = sum(1 for f in _COMPLETENESS_FIELDS if getattr(profile, f) not in (None, ""))
    return round(filled / len(_COMPLETENESS_FIELDS), 4)


def _to_profile_schema(profile: CitizenProfile) -> CitizenProfileSchema:
    return CitizenProfileSchema(
        id=str(profile.id),
        date_of_birth=profile.date_of_birth,
        gender=profile.gender,
        category=profile.category,
        occupation=profile.occupation,
        declared_annual_income=profile.declared_annual_income,
        disability_status=profile.disability_status,
        family_size=profile.family_size,
        profile_completeness=_completeness(profile),
        current_version_no=profile.current_version_no,
    )


def _snapshot(profile: CitizenProfile) -> dict:
    def enc(value: object) -> object:
        if isinstance(value, Decimal):
            return str(value)
        if isinstance(value, date):
            return value.isoformat()
        return value

    return {f: enc(getattr(profile, f)) for f in _COMPLETENESS_FIELDS}


def _to_address_schema(address: Address) -> AddressSchema:
    return AddressSchema(
        id=str(address.id),
        type=address.type,
        state=address.state,
        district=address.district,
        pincode=address.pincode,
        line1=address.line1,
        is_primary=address.is_primary,
    )


class CitizensService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._repo = CitizensRepository(session)
        self._audit = AuditService(session)

    # ------------------------------------------------------------------ #
    # Ownership helpers
    # ------------------------------------------------------------------ #
    def _own_profile(self, user_id: uuid.UUID) -> CitizenProfile:
        profile = self._repo.get_profile_by_user_id(user_id)
        if profile is None:
            raise NotFoundError("Citizen profile not found.")
        return profile

    def _own_address(self, user_id: uuid.UUID, address_id: uuid.UUID) -> tuple[CitizenProfile, Address]:
        profile = self._own_profile(user_id)
        address = self._repo.get_address(address_id)
        # Object-level check: address must belong to the caller's profile.
        # Otherwise NOT_FOUND — never confirm another citizen's resource exists.
        if address is None or address.citizen_profile_id != profile.id:
            raise NotFoundError("Address not found.")
        return profile, address

    # ------------------------------------------------------------------ #
    # Profile
    # ------------------------------------------------------------------ #
    def get_profile(self, user_id: uuid.UUID) -> CitizenProfileSchema:
        return _to_profile_schema(self._own_profile(user_id))

    def update_profile(
        self, user_id: uuid.UUID, payload: CitizenProfileUpdate, *, ip: str | None = None
    ) -> CitizenProfileSchema:
        profile = self._own_profile(user_id)
        changes = payload.model_dump(exclude_unset=True)

        for field, value in changes.items():
            setattr(profile, field, value)

        # Version the edit (immutable snapshot) and advance the pointer.
        profile.current_version_no += 1
        self._repo.add_profile_version(
            CitizenProfileVersion(
                citizen_profile_id=profile.id,
                version_no=profile.current_version_no,
                snapshot=_snapshot(profile),
            )
        )
        self._audit.record(
            action=AuditAction.PROFILE_UPDATE,
            entity_type="citizen_profile",
            entity_id=profile.id,
            actor_user_id=user_id,
            diff={"fields": sorted(changes.keys()), "version_no": profile.current_version_no},
            ip=ip,
        )
        self._session.commit()
        self._session.refresh(profile)
        return _to_profile_schema(profile)

    # ------------------------------------------------------------------ #
    # Addresses
    # ------------------------------------------------------------------ #
    def list_addresses(self, user_id: uuid.UUID) -> list[AddressSchema]:
        profile = self._own_profile(user_id)
        return [_to_address_schema(a) for a in self._repo.list_addresses(profile.id)]

    def create_address(
        self, user_id: uuid.UUID, payload: AddressInput, *, ip: str | None = None
    ) -> AddressSchema:
        profile = self._own_profile(user_id)
        existing = self._repo.list_addresses(profile.id)
        make_primary = payload.is_primary or len(existing) == 0  # first address is primary

        if make_primary:
            self._repo.clear_primary_flags(profile.id)

        address = Address(
            citizen_profile_id=profile.id,
            type=payload.type,
            state=payload.state,
            district=payload.district,
            pincode=payload.pincode,
            line1=payload.line1,
            is_primary=make_primary,
        )
        self._repo.add_address(address)
        self._audit.record(
            action=AuditAction.ADDRESS_CREATE,
            entity_type="address",
            entity_id=address.id,
            actor_user_id=user_id,
            diff={"type": address.type.value, "is_primary": address.is_primary},
            ip=ip,
        )
        self._session.commit()
        self._session.refresh(address)
        return _to_address_schema(address)

    def update_address(
        self,
        user_id: uuid.UUID,
        address_id: uuid.UUID,
        payload: AddressUpdate,
        *,
        ip: str | None = None,
    ) -> AddressSchema:
        profile, address = self._own_address(user_id, address_id)
        changes = payload.model_dump(exclude_unset=True)

        make_primary = changes.pop("is_primary", None)
        for field, value in changes.items():
            setattr(address, field, value)

        if make_primary is True and not address.is_primary:
            self._repo.clear_primary_flags(profile.id, except_id=address.id)
            address.is_primary = True
        elif make_primary is False:
            # Explicitly demoting the current primary is allowed (leaves none).
            address.is_primary = False

        self._audit.record(
            action=AuditAction.ADDRESS_UPDATE,
            entity_type="address",
            entity_id=address.id,
            actor_user_id=user_id,
            diff={"fields": sorted(list(changes.keys()) + (["is_primary"] if make_primary is not None else []))},
            ip=ip,
        )
        self._session.commit()
        self._session.refresh(address)
        return _to_address_schema(address)

    def delete_address(
        self, user_id: uuid.UUID, address_id: uuid.UUID, *, ip: str | None = None
    ) -> None:
        _profile, address = self._own_address(user_id, address_id)
        address_uuid = address.id
        self._repo.delete_address(address)
        self._audit.record(
            action=AuditAction.ADDRESS_DELETE,
            entity_type="address",
            entity_id=address_uuid,
            actor_user_id=user_id,
            ip=ip,
        )
        self._session.commit()
