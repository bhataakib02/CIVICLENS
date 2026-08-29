"""Notification delivery provider abstractions (prompt §12, §13, §54).

Providers return a structured DeliveryResult. Success carries a
provider_message_id; failure carries a typed DeliveryErrorCode that the delivery
layer uses to decide whether to retry (prompt §31). Bundled dev providers are
clearly NON_PRODUCTION and report SENT (never DELIVERED) — they do not confirm
receipt (prompt §54). The factory fails closed when a dev provider is selected
in production.

Credentials are never passed to callers and never logged (prompt §37).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.models.enums import DeliveryErrorCode, NotificationChannel


@dataclass(frozen=True)
class OutboundMessage:
    recipient: str          # opaque address/handle (email/phone/device/user-id)
    title: str
    body: str
    channel: NotificationChannel
    language: str = "en"


@dataclass(frozen=True)
class DeliveryResult:
    success: bool
    channel: NotificationChannel
    provider: str
    non_production: bool = False
    provider_message_id: str | None = None
    error_code: DeliveryErrorCode | None = None
    detail: str | None = None


class DeliveryProvider(ABC):
    channel: NotificationChannel
    name = "abstract"
    non_production = False

    @abstractmethod
    def send(self, message: OutboundMessage) -> DeliveryResult:  # pragma: no cover
        ...
