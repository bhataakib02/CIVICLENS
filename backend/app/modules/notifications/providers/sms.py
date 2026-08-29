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
