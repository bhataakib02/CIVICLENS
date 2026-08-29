"""Address model — matches data-dictionary.md `addresses` (+ is_primary extension).

DOCUMENTED EXTENSION: `is_primary` boolean is not in the data-dictionary.
It is required by the prompt ("There must not be multiple primary addresses
for the same citizen"), enforced by a PostgreSQL partial unique index
(see the Alembic migration). Recorded in the implementation report.
"""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, uuid_pk
from app.models.enums import AddressType

if TYPE_CHECKING:
    from app.models.citizen_profile import CitizenProfile


class Address(Base):
    __tablename__ = "addresses"

    id: Mapped[uuid.UUID] = uuid_pk()
    citizen_profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("citizen_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[AddressType] = mapped_column(
        Enum(
            AddressType,
            name="address_type",
            native_enum=True,
            validate_strings=True,
            values_callable=lambda enum: [m.value for m in enum],
        ),
        nullable=False,
    )
    state: Mapped[str] = mapped_column(String(64), nullable=False)
    district: Mapped[str] = mapped_column(String(64), nullable=False)
    pincode: Mapped[str] = mapped_column(String(6), nullable=False)
    line1: Mapped[str] = mapped_column(Text, nullable=False)  # PII

    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    profile: Mapped["CitizenProfile"] = relationship(back_populates="addresses")
