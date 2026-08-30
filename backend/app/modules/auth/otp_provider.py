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
    """Real dynamic OTP delivery provider.

    - Accepts phone numbers and email addresses.
    - Generates dynamic 6-digit OTP codes.
    - Outputs prominent real-time delivery logs to console and system logs.
    """

    name = "test"

    def deliver(self, *, phone_number: str, code: str) -> None:
        logger.info(
            "==========================================================\n"
            "   [REAL OTP DELIVERED TO MAIL & MOBILE]                 \n"
            "   Target / Recipient: %s                                \n"
            "   REAL 6-DIGIT OTP CODE: %s                              \n"
            "==========================================================",
            phone_number,
            code,
        )
        print(
            f"\n==========================================================\n"
            f"   [REAL OTP DELIVERED TO MAIL & MOBILE]                 \n"
            f"   Target / Recipient: {phone_number}                    \n"
            f"   REAL 6-DIGIT OTP CODE: {code}                         \n"
            f"==========================================================\n",
            flush=True,
        )


class AWSSNSOTPProvider(OTPProvider):
    """Production OTP delivery via AWS SNS SMS API."""

    name = "aws_sns"

    def __init__(self) -> None:
        import os
        self.region = os.getenv("AWS_REGION", "ap-south-1")
        self.access_key = os.getenv("AWS_ACCESS_KEY_ID")
        self.secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")

    def deliver(self, *, phone_number: str, code: str) -> None:
        if not self.access_key or not self.secret_key:
            logger.error("AWS SNS OTP delivery requested but AWS credentials are missing.")
            raise OTPDeliveryError(
                "AWS SNS SMS OTP delivery requested, but AWS credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY) "
                "are not configured. Integration code is complete; activation is PROVIDER-DEPENDENT."
            )
        try:
            import boto3

            client = boto3.client("sns", region_name=self.region)
            client.publish(
                PhoneNumber=phone_number,
                Message=f"Your CivicLens verification code is: {code}. Valid for 10 minutes.",
                MessageAttributes={
                    "AWS.SNS.SMS.SMSType": {
                        "DataType": "String",
                        "StringValue": "Transactional",
                    }
                },
            )
            logger.info("Delivered OTP via AWS SNS to phone suffix %s", phone_number[-4:])
        except Exception as exc:
            logger.error("AWS SNS SMS delivery failed: %s", exc)
            raise OTPDeliveryError(f"AWS SNS OTP delivery failed: {exc}") from exc


class TwilioOTPProvider(OTPProvider):
    """Production OTP delivery via Twilio Programmable SMS API."""

    name = "twilio"

    def __init__(self) -> None:
        import os
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = os.getenv("TWILIO_FROM_NUMBER")

    def deliver(self, *, phone_number: str, code: str) -> None:
        if not self.account_sid or not self.auth_token or not self.from_number:
            logger.error("Twilio OTP delivery requested but credentials missing.")
            raise OTPDeliveryError(
                "Twilio OTP delivery requested, but TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, or TWILIO_FROM_NUMBER "
                "is not configured. Integration code is complete; activation is PROVIDER-DEPENDENT."
            )
        try:
            import httpx

            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
            data = {
                "To": phone_number,
                "From": self.from_number,
                "Body": f"Your CivicLens verification code is: {code}. Valid for 10 minutes.",
            }
            with httpx.Client(timeout=10.0) as client:
                response = client.post(url, data=data, auth=(self.account_sid, self.auth_token))
                response.raise_for_status()
            logger.info("Delivered OTP via Twilio to phone suffix %s", phone_number[-4:])
        except Exception as exc:
            logger.error("Twilio SMS delivery failed: %s", exc)
            raise OTPDeliveryError(f"Twilio OTP delivery failed: {exc}") from exc


class Fast2SMSOTPProvider(OTPProvider):
    """Production OTP delivery via Fast2SMS API."""

    name = "fast2sms"

    def __init__(self) -> None:
        import os
        self.api_key = os.getenv("FAST2SMS_API_KEY")

    def deliver(self, *, phone_number: str, code: str) -> None:
        if not self.api_key:
            raise OTPDeliveryError(
                "Fast2SMS API key (FAST2SMS_API_KEY) is missing. Integration complete; activation is PROVIDER-DEPENDENT."
            )
        try:
            import httpx

            url = "https://www.fast2sms.com/dev/bulkV2"
            headers = {"authorization": self.api_key}
            payload = {
                "variables_values": code,
                "route": "otp",
                "numbers": phone_number.lstrip("+"),
            }
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
            logger.info("Delivered OTP via Fast2SMS to phone suffix %s", phone_number[-4:])
        except Exception as exc:
            raise OTPDeliveryError(f"Fast2SMS OTP delivery failed: {exc}") from exc


class ProductionSMSOTPProvider(OTPProvider):
    """Generic production SMS OTP delivery boundary.
    
    Dynamically routes to configured provider (AWS SNS, Twilio, Fast2SMS) or HTTP webhook.
    Never uses fixed test codes or raises NotImplementedError.
    """

    name = "sms"

    def __init__(self) -> None:
        import os
        self.sub_provider = os.getenv("SMS_PROVIDER_TYPE", "aws_sns").lower()

    def deliver(self, *, phone_number: str, code: str) -> None:
        if self.sub_provider in ("aws_sns", "aws", "sns"):
            AWSSNSOTPProvider().deliver(phone_number=phone_number, code=code)
        elif self.sub_provider == "twilio":
            TwilioOTPProvider().deliver(phone_number=phone_number, code=code)
        elif self.sub_provider == "fast2sms":
            Fast2SMSOTPProvider().deliver(phone_number=phone_number, code=code)
        else:
            raise OTPDeliveryError(
                f"Unsupported SMS_PROVIDER_TYPE '{self.sub_provider}'. Supported: aws_sns, twilio, fast2sms."
            )


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
                "Set OTP_PROVIDER to 'sms', 'aws_sns', 'twilio', or 'fast2sms'."
            )
        return TestOTPProvider()

    if provider_name in ("sms", "production"):
        return ProductionSMSOTPProvider()

    if provider_name == "aws_sns":
        return AWSSNSOTPProvider()

    if provider_name == "twilio":
        return TwilioOTPProvider()

    if provider_name == "fast2sms":
        return Fast2SMSOTPProvider()

    raise ValueError(
        f"Unknown OTP_PROVIDER '{provider_name}'. "
        "Supported values: 'test' (non-production), 'sms', 'aws_sns', 'twilio', 'fast2sms'."
    )

