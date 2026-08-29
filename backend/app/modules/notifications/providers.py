"""Notification delivery provider abstractions (prompt §38).

The application depends on these interfaces, never on a vendor SDK. Bundled
Test* providers are for dev/tests ONLY (they record a delivery in-memory and
never send anything). Production must configure real providers; the factory
fails closed when a test provider is selected in production.

CivicLens does NOT claim real email/SMS delivery unless a real provider is
configured.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.core.config import Settings, get_settings
from app.models.enums import NotificationChannel


class NotificationProviderError(Exception):
    pass


class ProviderUnavailableError(NotificationProviderError):
    pass


@dataclass
class DeliveryResult:
    delivered: bool
    provider: str
    channel: NotificationChannel
    detail: str | None = None


class NotificationProvider(ABC):
    channel: NotificationChannel
    name = "abstract"

    @abstractmethod
    def send(self, *, recipient: str, subject: str, body: str) -> DeliveryResult:  # pragma: no cover
        ...


class _TestProvider(NotificationProvider):
    """Records deliveries in-memory. NOT real delivery."""

    name = "test"
    sent: list = field(default_factory=list)  # type: ignore

    def __init__(self) -> None:
        self.sent = []

    def send(self, *, recipient: str, subject: str, body: str) -> DeliveryResult:
        # PII-safe: record only the channel + subject, never the body/recipient.
        self.sent.append({"channel": self.channel.value, "subject": subject})
        return DeliveryResult(delivered=True, provider=self.name, channel=self.channel)


class TestEmailProvider(_TestProvider):
    channel = NotificationChannel.EMAIL


class TestSMSProvider(_TestProvider):
    channel = NotificationChannel.SMS


class TestPushProvider(_TestProvider):
    channel = NotificationChannel.IN_APP


def get_provider(channel: NotificationChannel, settings: Settings | None = None) -> NotificationProvider:
    settings = settings or get_settings()
    mapping = {
        NotificationChannel.EMAIL: (settings.email_provider, TestEmailProvider),
        NotificationChannel.SMS: (settings.sms_provider, TestSMSProvider),
        NotificationChannel.IN_APP: (settings.push_provider, TestPushProvider),
    }
    provider_name, test_cls = mapping[channel]
    if provider_name.lower() == "test":
        if settings.is_production:
            raise ProviderUnavailableError(
                f"The test {channel.value} provider must not be used in production."
            )
        return test_cls()
    raise ProviderUnavailableError(
        f"Unknown or unconfigured provider '{provider_name}' for channel {channel.value}."
    )
