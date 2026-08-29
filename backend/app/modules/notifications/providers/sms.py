"""SMS provider abstraction + NON_PRODUCTION fake provider (prompt §13, §29).

Never logs phone numbers (prompt §29, §37). Preference/verification gating is
enforced upstream in the orchestrator; here we only validate shape and return a
structured result.
"""
from __future__ import annotations

import re
import uuid

from app.core.logging import get_logger
from app.models.enums import DeliveryErrorCode, NotificationChannel
from app.modules.notifications.providers.base import (
    DeliveryProvider,
    DeliveryResult,
    OutboundMessage,
)

logger = get_logger("civiclens.notifications.sms")
_PHONE_RE = re.compile(r"^\+?[0-9]{7,15}$")


class FakeSMSProvider(DeliveryProvider):
    """NON_PRODUCTION: records nothing sensitive; does not send real SMS."""

    channel = NotificationChannel.SMS
    name = "fake"
    non_production = True

    def send(self, message: OutboundMessage) -> DeliveryResult:
        if not message.recipient or not _PHONE_RE.match(message.recipient):
            return DeliveryResult(
                success=False, channel=self.channel, provider=self.name,
                non_production=True, error_code=DeliveryErrorCode.INVALID_PHONE,
            )
        # PII-safe: never log the phone number or body.
        logger.info("sms_fake_sent", extra={"len": len(message.body or "")})
        return DeliveryResult(
            success=True, channel=self.channel, provider=self.name, non_production=True,
            provider_message_id=f"fakesms-{uuid.uuid4().hex[:16]}",
            detail="NON_PRODUCTION fake SMS; not delivered by a real provider.",
        )


class AWSSNSNotificationProvider(DeliveryProvider):
    """Production SMS delivery via AWS SNS."""

    channel = NotificationChannel.SMS
    name = "aws_sns"
    non_production = False

    def send(self, message: OutboundMessage) -> DeliveryResult:
        import os

        if not message.recipient or not _PHONE_RE.match(message.recipient):
            return DeliveryResult(
                success=False, channel=self.channel, provider=self.name,
                non_production=False, error_code=DeliveryErrorCode.INVALID_PHONE,
            )

        region = os.getenv("AWS_REGION", "ap-south-1")
        access_key = os.getenv("AWS_ACCESS_KEY_ID")

        if not access_key:
            return DeliveryResult(
                success=False, channel=self.channel, provider=self.name, non_production=False,
                detail="AWS SNS credentials missing. Activation is PROVIDER-DEPENDENT.",
            )

        try:
            import boto3

            client = boto3.client("sns", region_name=region)
            resp = client.publish(PhoneNumber=message.recipient, Message=f"{message.title}\n\n{message.body}")
            msg_id = resp.get("MessageId", f"sns-{uuid.uuid4().hex[:16]}")
            return DeliveryResult(
                success=True, channel=self.channel, provider=self.name,
                non_production=False, provider_message_id=msg_id, detail="AWS SNS SMS sent",
            )
        except Exception as exc:
            logger.error("AWS SNS SMS delivery failed: %s", exc)
            return DeliveryResult(
                success=False, channel=self.channel, provider=self.name,
                non_production=False, error_code=DeliveryErrorCode.TRANSIENT_NETWORK_FAILURE, detail=str(exc),
            )


class TwilioSMSNotificationProvider(DeliveryProvider):
    """Production SMS delivery via Twilio."""

    channel = NotificationChannel.SMS
    name = "twilio"
    non_production = False

    def send(self, message: OutboundMessage) -> DeliveryResult:
        import os

        if not message.recipient or not _PHONE_RE.match(message.recipient):
            return DeliveryResult(
                success=False, channel=self.channel, provider=self.name,
                non_production=False, error_code=DeliveryErrorCode.INVALID_PHONE,
            )

        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        from_number = os.getenv("TWILIO_FROM_NUMBER")

        if not account_sid or not auth_token or not from_number:
            return DeliveryResult(
                success=False, channel=self.channel, provider=self.name, non_production=False,
                detail="Twilio credentials missing. Activation is PROVIDER-DEPENDENT.",
            )

        try:
            import httpx

            url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
            data = {"To": message.recipient, "From": from_number, "Body": f"{message.title}: {message.body}"}
            with httpx.Client(timeout=10.0) as client:
                res = client.post(url, data=data, auth=(account_sid, auth_token))
                res.raise_for_status()

            return DeliveryResult(
                success=True, channel=self.channel, provider=self.name,
                non_production=False, provider_message_id=f"tw-{uuid.uuid4().hex[:16]}", detail="Twilio SMS sent",
            )
        except Exception as exc:
            logger.error("Twilio SMS delivery failed: %s", exc)
            return DeliveryResult(
                success=False, channel=self.channel, provider=self.name,
                non_production=False, error_code=DeliveryErrorCode.TRANSIENT_NETWORK_FAILURE, detail=str(exc),
            )

