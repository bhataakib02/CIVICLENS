"""Push provider abstraction + NON_PRODUCTION test provider (prompt §13, §30).

There is no real mobile client yet, so only the interface + a test
implementation exist. It never claims real delivery.
"""
from __future__ import annotations

import uuid

from app.core.logging import get_logger
from app.models.enums import DeliveryErrorCode, NotificationChannel
from app.modules.notifications.providers.base import (
    DeliveryProvider,
    DeliveryResult,
    OutboundMessage,
)

logger = get_logger("civiclens.notifications.push")


class FakePushProvider(DeliveryProvider):
    """NON_PRODUCTION: no real push infrastructure exists."""

    channel = NotificationChannel.PUSH
    name = "fake"
    non_production = True

    def send(self, message: OutboundMessage) -> DeliveryResult:
        if not message.recipient:
            return DeliveryResult(
                success=False, channel=self.channel, provider=self.name,
                non_production=True, error_code=DeliveryErrorCode.UNSUPPORTED_CHANNEL,
            )
        logger.info("push_fake_sent", extra={"title": message.title})
        return DeliveryResult(
            success=True, channel=self.channel, provider=self.name, non_production=True,
            provider_message_id=f"fakepush-{uuid.uuid4().hex[:16]}",
            detail="NON_PRODUCTION fake push; no real mobile client.",
        )
