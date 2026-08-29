"""In-app delivery provider (prompt §11).

In-app is the always-available channel: "delivery" means the notification row is
persisted and (best-effort) pushed over real-time. There is no external vendor,
so success is a genuine SENT (the row exists); real-time fan-out is separate and
its failure does not fail the notification.
"""
from __future__ import annotations

from app.models.enums import NotificationChannel
from app.modules.notifications.providers.base import (
    DeliveryProvider,
    DeliveryResult,
    OutboundMessage,
)


class InAppProvider(DeliveryProvider):
    channel = NotificationChannel.IN_APP
    name = "in_app"
    non_production = False  # in-app is real: the DB row IS the delivery.

    def send(self, message: OutboundMessage) -> DeliveryResult:
        return DeliveryResult(
            success=True, channel=self.channel, provider=self.name,
            provider_message_id=None, detail="in_app_persisted",
        )
