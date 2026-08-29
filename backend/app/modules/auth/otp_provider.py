"""OTP delivery provider abstraction.

Production architecture:
  - OTPProvider: abstract base — never knows about storage.
  - TestOTPProvider: NON-PRODUCTION, returns fixed code '000000', logs clearly.
    Must NOT be used in production (factory enforces this).
  - SMSOTPProvider: stub for real SMS integration. Raises NotImplementedError
    with instructions; replace with a real Twilio/MSG91/etc. client.

The provider is responsible ONLY for delivering the OTP to the user's device.
It never stores, hashes, or validates OTPs — that is OTPService's concern.

SECURITY:
  - The 6-digit OTP code passed to deliver() must NEVER be logged anywhere
    except the TestOTPProvider (which clearly marks it as [TEST-ONLY]).
  - Real providers must use TLS and authenticated API calls.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger("civiclens.otp")


class OTPDeliveryError(Exception):
    """Provider could not deliver the OTP (transient or permanent)."""


class OTPProvider(ABC):
    """Abstract OTP delivery provider."""

    name: str = "abstract"

    @abstractmethod
    def deliver(self, *, phone_number: str, code: str) -> None:
        """Deliver the OTP code to the given phone number.

        The `code` is the plaintext 6-digit code.
        Implementations MUST NOT log the code value (except TestOTPProvider).
        Raises OTPDeliveryError on failure.
        """
        ...  # pragma: no cover


class TestOTPProvider(OTPProvider):
    """NON-PRODUCTION test OTP provider.

    - Always accepts any phone number.
    - Logs the code at DEBUG level — TEST/DEV ONLY.
    - Suitable for automated tests and local development.
    - Will RAISE in production (factory enforces ENVIRONMENT != production).
    - Code is always '000000' for deterministic test runs when
      OTP_TEST_FIXED_CODE=true (default in test environment).
    """

    name = "test"

    def deliver(self, *, phone_number: str, code: str) -> None:
        # [TEST-ONLY] Logging the code is acceptable only in this provider.
        logger.debug(
            "[TEST-ONLY] OTP delivery (non-production): code=%s phone=%s",
            code,
            phone_number[-4:].rjust(len(phone_number), "*"),  # mask all but last 4
        )
        # No network call; no side effects.


class SMSOTPProvider(OTPProvider):
    """Stub for a real SMS OTP provider (e.g. Twilio, MSG91, Exotel).

    Replace this stub with a real implementation before production deployment.
    Configure via:
      SMS_PROVIDER_API_KEY=...
      SMS_PROVIDER_SENDER_ID=...
      SMS_PROVIDER_BASE_URL=...
    """

    name = "sms"

    def __init__(self) -> None:
        raise NotImplementedError(
            "SMSOTPProvider is a stub. "
            "Implement a real SMS provider (Twilio / MSG91 / Exotel) "
            "and configure SMS_PROVIDER_* environment variables before "
            "enabling SMS OTP in production."
        )

    def deliver(self, *, phone_number: str, code: str) -> None:
        raise NotImplementedError("Real SMS delivery not configured.")  # pragma: no cover


def get_otp_provider(settings=None) -> OTPProvider:
    """Return the configured OTP provider. Fails closed in production.

    In test/development, defaults to TestOTPProvider.
    In production, 'test' provider raises immediately (fail closed).
    """
    from app.core.config import get_settings

    s = settings or get_settings()
    provider_name = getattr(s, "otp_provider", "test").lower()

    if provider_name == "test":
        if getattr(s, "is_production", False):
            raise RuntimeError(
                "TestOTPProvider must not be used in production. "
                "Set OTP_PROVIDER to a real SMS provider."
            )
        return TestOTPProvider()

    if provider_name == "sms":
        return SMSOTPProvider()

    raise ValueError(
        f"Unknown OTP_PROVIDER '{provider_name}'. "
        "Supported values: 'test' (non-production), 'sms' (requires configuration)."
    )
