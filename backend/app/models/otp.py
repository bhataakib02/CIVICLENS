"""OTP (One-Time Password) request model for phone-based citizen auth.

Stores a hashed OTP code (never the plaintext) with short expiry, single-use
semantics, and attempt counting. The phone number is stored as-is (PII) in
this table; access is by phone_number lookup only during the brief OTP window.

Security properties enforced by OTPService:
  - Short expiry: 5 minutes (configurable via OTP_EXPIRY_SECONDS)
  - Single use: used_at set on first successful verify
  - Attempt limits: OTP_MAX_ATTEMPTS (default 5); exhausted OTPs are invalid
  - Rate limiting: per phone_number in the service layer
  - Audit events written on every request and verify attempt
  - OTP plaintext NEVER stored, NEVER logged
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, uuid_pk


class OTPRequest(Base):
    __tablename__ = "otp_requests"

    id: Mapped[uuid.UUID] = uuid_pk()

    # PII: stored for lookup during the brief OTP window.
    # phone_number is NOT indexed globally — queries always use phone_number + expires_at.
    phone_number: Mapped[str] = mapped_column(String(320), nullable=False, index=True)

    # Argon2id hash of the OTP plaintext (never stored raw).
    code_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    # Single-use: set when the OTP is successfully verified.
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Attempt counting: service increments on every failed verify; blocks at max.
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Audit / rate-limit context (IP stored for rate limiting; not logged beyond this table).
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:  # pragma: no cover - debug only, no PII
        return f"<OTPRequest id={self.id} expires_at={self.expires_at}>"
