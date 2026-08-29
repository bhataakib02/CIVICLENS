"""Citizens persistence layer (profiles, profile versions, addresses)."""
from __future__ import annotations

import uuid

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.address import Address
from app.models.citizen_profile import CitizenProfile, CitizenProfileVersion


class CitizensRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    # --- profile ---
    def get_profile_by_user_id(self, user_id: uuid.UUID) -> CitizenProfile | None:
        stmt = select(CitizenProfile).where(CitizenProfile.user_id == user_id)
        return self._session.scalar(stmt)

    def add_profile_version(self, version: CitizenProfileVersion) -> None:
        self._session.add(version)
        self._session.flush()

    # --- addresses ---
    def get_address(self, address_id: uuid.UUID) -> Address | None:
        return self._session.get(Address, address_id)

    def list_addresses(self, profile_id: uuid.UUID) -> list[Address]:
        stmt = (
            select(Address)
            .where(Address.citizen_profile_id == profile_id)
            .order_by(Address.is_primary.desc(), Address.id)
        )
        return list(self._session.scalars(stmt))

    def add_address(self, address: Address) -> Address:
        self._session.add(address)
        self._session.flush()
        return address

    def delete_address(self, address: Address) -> None:
        self._session.delete(address)
        self._session.flush()

    def clear_primary_flags(
        self, profile_id: uuid.UUID, *, except_id: uuid.UUID | None = None
    ) -> None:
        """Unset is_primary for a profile's addresses (optionally excluding one).

        Done before setting a new primary so the partial unique index
        (one primary per citizen) is never violated within the transaction.
        """
        stmt = (
            update(Address)
            .where(Address.citizen_profile_id == profile_id, Address.is_primary.is_(True))
            .values(is_primary=False)
        )
        if except_id is not None:
            stmt = stmt.where(Address.id != except_id)
        self._session.execute(stmt)
        self._session.flush()
