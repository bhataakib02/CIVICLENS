"""Notification orchestrator (prompt §14).

Given a domain event (envelope), it:
  1. looks up the notification policy (channels/category/priority),
  2. resolves the recipient user + preferred language,
  3. filters channels by user preferences (security-mandatory channels bypass),
  4. renders the versioned, localized template,
  5. creates a Notification row per channel (idempotent via the DB unique
     constraint — prompt §33),
  6. dispatches delivery via the provider (structured result),
  7. best-effort publishes a real-time event for in-app notifications.

All work happens inside the worker's session/transaction. Delivery failures are
recorded on the notification (status FAILED + error_code) and returned so the
worker can decide whether to retry the whole event (prompt §31).

Notifications are NEVER created directly by routers/models — only here.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.core.metrics import metrics
from app.models.citizen_profile import CitizenProfile
from app.models.enums import (
    DeliveryErrorCode,
    DomainEventType,
    NotificationChannel,
    NotificationStatus,
)
from app.models.notification import Notification
from app.models.user import User
from app.modules.notifications import policies, preferences, templates
from app.modules.notifications.events import parse_event_type
from app.modules.notifications.providers import (
    OutboundMessage,
    ProviderUnavailableError,
    get_provider,
)
from app.modules.notifications.realtime import events as realtime_events

logger = get_logger("civiclens.notifications.orchestrator")


@dataclass
class Recipient:
    user_id: uuid.UUID
    citizen_profile_id: uuid.UUID | None
    language: str
    email: str | None
    phone: str | None


@dataclass
class OrchestrationResult:
    created: int = 0
    delivered: int = 0
    failed: int = 0
    retryable_failure: bool = False


class NotificationOrchestrator:
    def __init__(self, session: Session, settings: Settings | None = None) -> None:
        self._session = session
        self._s = settings or get_settings()

    # ------------------------------------------------------------------ #
    def handle_event(
        self,
        *,
        event_id: uuid.UUID | None,
        event_type_str: str,
        aggregate_type: str,
        aggregate_id: uuid.UUID,
        payload: dict,
        schema_version: int = 1,
    ) -> OrchestrationResult:
        result = OrchestrationResult()
        try:
            event_type = parse_event_type(event_type_str)
        except ValueError:
            logger.info("orchestrator_unknown_event", extra={"event_type": event_type_str})
            return result

        policy = policies.policy_for(event_type)
        if policy is None:
            return result  # not a citizen-notifiable event (avoid spam, §15)

        recipient = self._resolve_recipient(payload)
        if recipient is None:
            return result

        pref = preferences.get_or_create(self._session, recipient.user_id)
        pref_flag = policies.preference_flag_for_category(policy.category)
        category_on = preferences.category_enabled(pref, pref_flag)

        rendered = templates.render(
            event_type.value, language=recipient.language, variables=payload
        )

        for channel in policy.channels:
            mandatory = channel in policy.mandatory_channels
            # Category opt-out: skip unless mandatory.
            if not category_on and not mandatory:
                continue
            # Channel opt-in (in_app + mandatory bypass the channel toggle).
            if channel is not NotificationChannel.IN_APP and not mandatory:
                if not preferences.channel_enabled(pref, channel):
                    continue

            self._deliver_channel(
                event_id=event_id, event_type=event_type, policy=policy,
                recipient=recipient, rendered=rendered, channel=channel,
                aggregate_type=aggregate_type, aggregate_id=aggregate_id, result=result,
            )
        return result

    # ------------------------------------------------------------------ #
    def _deliver_channel(self, *, event_id, event_type: DomainEventType, policy,
                         recipient: Recipient, rendered, channel: NotificationChannel,
                         aggregate_type, aggregate_id, result: OrchestrationResult) -> None:
        # Idempotent create: the DB unique (event_id, channel, recipient) guards
        # against duplicate event processing (prompt §33, §44).
        existing = None
        if event_id is not None:
            existing = self._session.scalar(
                select(Notification).where(
                    Notification.event_id == event_id,
                    Notification.channel == channel,
                    Notification.recipient_user_id == recipient.user_id,
                )
            )
        if existing is not None:
            return  # already processed this (event, channel, recipient)

        notification = Notification(
            citizen_profile_id=recipient.citizen_profile_id,
            recipient_user_id=recipient.user_id,
            event_id=event_id,
            type=event_type.value,
            channel=channel,
            category=policy.category,
            priority=policy.priority,
            status=NotificationStatus.PROCESSING,
            subject=rendered.title,
            title=rendered.title,
            body=rendered.body,
            template_key=rendered.template_key,
            template_version=rendered.version,
            language=rendered.language,
            entity_type=aggregate_type,
            entity_id=aggregate_id,
        )
        self._session.add(notification)
        try:
            self._session.flush()
        except IntegrityError:
            # A concurrent worker created it first — dedup at DB level (§33, §45).
            self._session.rollback()
            return
        metrics.incr("notifications_created")
        result.created += 1

        self._dispatch(notification, recipient, result)

    def _dispatch(self, notification: Notification, recipient: Recipient,
                  result: OrchestrationResult) -> None:
        channel = notification.channel
        address = {
            NotificationChannel.EMAIL: recipient.email,
            NotificationChannel.SMS: recipient.phone,
            NotificationChannel.PUSH: str(recipient.user_id),
            NotificationChannel.IN_APP: str(recipient.user_id),
        }.get(channel)

        notification.attempt_count += 1
        try:
            provider = get_provider(channel, self._s)
        except ProviderUnavailableError:
            self._mark_failed(notification, DeliveryErrorCode.PROVIDER_UNAVAILABLE, result)
            return

        delivery = provider.send(OutboundMessage(
            recipient=address or "", title=notification.title or "",
            body=notification.body or "", channel=channel, language=notification.language or "en",
        ))
        notification.provider = delivery.provider
        if delivery.success:
            # SENT (provider accepted). DELIVERED is only set when a real provider
            # confirms receipt — dev providers never claim it (prompt §54).
            notification.status = NotificationStatus.SENT
            notification.sent_at = datetime.now(timezone.utc)
            notification.provider_message_id = delivery.provider_message_id
            metrics.incr("notifications_sent")
            result.delivered += 1
            # Best-effort real-time fan-out for the in-app channel (§20).
            if channel is NotificationChannel.IN_APP:
                self._publish_realtime(notification, recipient)
        else:
            self._mark_failed(notification, delivery.error_code, result)

    def _mark_failed(self, notification: Notification,
                     error_code: DeliveryErrorCode | None, result: OrchestrationResult) -> None:
        from app.modules.notifications.delivery import is_retryable

        notification.status = NotificationStatus.FAILED
        notification.failed_at = datetime.now(timezone.utc)
        notification.error_code = error_code.value if error_code else None
        metrics.incr("notifications_failed")
        result.failed += 1
        # A retryable channel failure signals the worker to retry the event.
        if is_retryable(error_code):
            result.retryable_failure = True

    def _publish_realtime(self, notification: Notification, recipient: Recipient) -> None:
        message = realtime_events.build_message(
            notification_id=notification.id, event_type=notification.type,
            title=notification.title, category=notification.category.value,
            priority=notification.priority.value, entity_type=notification.entity_type,
            entity_id=notification.entity_id,
        )
        realtime_events.publish_sync(recipient.user_id, message)

    # ------------------------------------------------------------------ #
    def _resolve_recipient(self, payload: dict) -> Recipient | None:
        """Resolve recipient from the event payload. Supports citizen_profile_id
        (application/document/eligibility events) and recipient_user_id."""
        profile_id = payload.get("citizen_profile_id")
        user_id = payload.get("recipient_user_id")

        profile: CitizenProfile | None = None
        if profile_id:
            profile = self._session.get(CitizenProfile, uuid.UUID(str(profile_id)))
        if profile is not None:
            user = self._session.get(User, profile.user_id)
            return Recipient(
                user_id=profile.user_id, citizen_profile_id=profile.id,
                language=(profile.preferred_language or self._s.notification_default_language),
                email=(user.email if user else None),
                phone=(user.phone_number if user else None),
            )
        if user_id:
            uid = uuid.UUID(str(user_id))
            user = self._session.get(User, uid)
            if user is None:
                return None
            prof = self._session.scalar(select(CitizenProfile).where(CitizenProfile.user_id == uid))
            return Recipient(
                user_id=uid, citizen_profile_id=(prof.id if prof else None),
                language=(prof.preferred_language if prof else self._s.notification_default_language),
                email=user.email, phone=user.phone_number,
            )
        return None
