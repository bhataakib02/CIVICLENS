"""Email provider abstraction + NON_PRODUCTION console dev provider (prompt §13, §28).

ConsoleEmailProvider only logs a PII-safe line (never the body/recipient) and
returns SENT — never DELIVERED — because no external system confirmed receipt
(prompt §54). A real provider (SES/SendGrid/...) would be added here and
configured via EMAIL_PROVIDER; credentials come from the environment only.
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

logger = get_logger("civiclens.notifications.email")


def _looks_like_email(addr: str) -> bool:
    return "@" in addr and "." in addr.split("@")[-1] and len(addr) <= 320


class ConsoleEmailProvider(DeliveryProvider):
    """NON_PRODUCTION: logs a PII-safe line; does not send real email."""

    channel = NotificationChannel.EMAIL
    name = "console"
    non_production = True

    def send(self, message: OutboundMessage) -> DeliveryResult:
        if not message.recipient or not _looks_like_email(message.recipient):
            return DeliveryResult(
                success=False, channel=self.channel, provider=self.name,
                non_production=True, error_code=DeliveryErrorCode.INVALID_EMAIL,
            )
        # PII-safe: log only channel + title, never the body or address.
        logger.info("email_console_sent", extra={"title": message.title})
        return DeliveryResult(
            success=True, channel=self.channel, provider=self.name, non_production=True,
            provider_message_id=f"console-{uuid.uuid4().hex[:16]}",
            detail="NON_PRODUCTION console email; not delivered by a real provider.",
        )
