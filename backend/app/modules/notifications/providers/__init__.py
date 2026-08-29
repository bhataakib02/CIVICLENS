"""Provider registry/factory (prompt §12, §13).

Selects a provider per channel from settings. Dev providers are NON_PRODUCTION
and the factory FAILS CLOSED if one is selected while ENVIRONMENT=production —
CivicLens never claims real delivery it cannot perform.
"""
from __future__ import annotations

from app.core.config import Settings, get_settings
from app.models.enums import NotificationChannel
from app.modules.notifications.providers.base import (
    DeliveryProvider,
    DeliveryResult,
    OutboundMessage,
)
from app.modules.notifications.providers.email import ConsoleEmailProvider
from app.modules.notifications.providers.in_app import InAppProvider
from app.modules.notifications.providers.push import FakePushProvider
from app.modules.notifications.providers.sms import FakeSMSProvider


class ProviderUnavailableError(Exception):
    pass


# channel -> {provider_name: constructor}
_DEV_PROVIDERS = {
    NotificationChannel.EMAIL: {"test": ConsoleEmailProvider, "console": ConsoleEmailProvider},
    NotificationChannel.SMS: {"test": FakeSMSProvider, "fake": FakeSMSProvider},
    NotificationChannel.PUSH: {"test": FakePushProvider, "fake": FakePushProvider},
}


def get_provider(channel: NotificationChannel, settings: Settings | None = None) -> DeliveryProvider:
    settings = settings or get_settings()

    # In-app is always real and always available.
    if channel is NotificationChannel.IN_APP:
        return InAppProvider()

    provider_name = {
        NotificationChannel.EMAIL: settings.email_provider,
        NotificationChannel.SMS: settings.sms_provider,
        NotificationChannel.PUSH: settings.push_provider,
    }.get(channel, "")
    name = (provider_name or "").lower()

    dev = _DEV_PROVIDERS.get(channel, {})
    if name in dev:
        if settings.is_production:
            raise ProviderUnavailableError(
                f"NON_PRODUCTION {channel.value} provider '{name}' must not be used in production; "
                f"configure a real provider."
            )
        return dev[name]()

    # A real provider (e.g. 'ses', 'twilio', 'fcm') would be constructed here.
    raise ProviderUnavailableError(
        f"Unknown/unconfigured provider '{provider_name}' for channel {channel.value}."
    )


__all__ = [
    "DeliveryProvider",
    "DeliveryResult",
    "OutboundMessage",
    "ProviderUnavailableError",
    "get_provider",
]
