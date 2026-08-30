"""User account model — matches data-dictionary.md `users` (+ documented extensions)."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, uuid_pk
from app.models.enums import UserRole, UserStatus

if TYPE_CHECKING:
    from app.models.citizen_profile import CitizenProfile
    from app.models.refresh_token import RefreshToken


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = uuid_pk()

    # phone_number: data-dictionary has it unique + PII. Nullable here because
    # this slice supports email+password accounts (FR-AUTH-1: "or email+password").
    phone_number: Mapped[str | None] = mapped_column(
        String(320), unique=True, nullable=True, index=True
    )
    email: Mapped[str | None] = mapped_column(String(320), unique=True, nullable=True, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)

    role: Mapped[UserRole] = mapped_column(
        Enum(
            UserRole,
            name="user_role",
            native_enum=True,
            validate_strings=True,
            values_callable=lambda enum: [m.value for m in enum],
        ),
        default=UserRole.CITIZEN,
        nullable=False,
    )
    # DOCUMENTED EXTENSION (see enums.UserStatus).
    status: Mapped[UserStatus] = mapped_column(
        Enum(
            UserStatus,
            name="user_status",
            native_enum=True,
            validate_strings=True,
            values_callable=lambda enum: [m.value for m in enum],
        ),
        default=UserStatus.ACTIVE,
        nullable=False,
    )

    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    profile: Mapped["CitizenProfile | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover - debug only, no PII
        return f"<User id={self.id} role={self.role.value} status={self.status.value}>"
