"""Unit tests for the notification subsystem pure logic (prompt §42, no DB):
templates (versioning + localization + safe substitution), policies, delivery
retry classification/backoff, preferences update rules."""
from __future__ import annotations

import pytest

from app.models.enums import (
    DeliveryErrorCode,
    DomainEventType,
    NotificationChannel,
)
from app.modules.notifications import delivery, policies, templates

pytestmark = pytest.mark.unit


# ------------------------------ templates ----------------------------------- #
def test_template_renders_english_with_variables():
    r = templates.render(DomainEventType.APPLICATION_SUBMITTED.value, language="en",
                         variables={"application_number": "CL-2026-00000001"})
    assert r.language == "en"
    assert r.version == 1
    assert "CL-2026-00000001" in r.body
    assert r.title == "Application submitted"


def test_template_localization_bn_used_when_available():
    r = templates.render(DomainEventType.APPLICATION_SUBMITTED.value, language="bn",
                         variables={"application_number": "CL-1"})
    assert r.language == "bn"
    assert "CL-1" in r.body


def test_template_falls_back_to_english_when_language_missing():
    # APPLICATION_APPROVED only defines 'en'; requesting 'bn' falls back.
    r = templates.render(DomainEventType.APPLICATION_APPROVED.value, language="bn",
                         variables={"application_number": "CL-2"})
    assert r.language == "en"


def test_template_missing_variable_is_safe_not_error():
    # No application_number supplied -> empty placeholder, no exception/leak.
    r = templates.render(DomainEventType.APPLICATION_SUBMITTED.value, language="en", variables={})
    assert "{" not in r.body  # placeholder substituted, not left raw


def test_template_versioning_recorded():
    r = templates.render(DomainEventType.APPLICATION_ACTION_REQUIRED.value, language="en",
                         variables={"application_number": "X"})
    assert r.template_key == DomainEventType.APPLICATION_ACTION_REQUIRED.value
    assert isinstance(r.version, int)


# ------------------------------ policies ------------------------------------ #
def test_policy_action_required_uses_multiple_channels():
    p = policies.policy_for(DomainEventType.APPLICATION_ACTION_REQUIRED)
    assert NotificationChannel.IN_APP in p.channels
    assert NotificationChannel.EMAIL in p.channels
    assert NotificationChannel.SMS in p.channels


def test_policy_status_changed_is_in_app_only():
    p = policies.policy_for(DomainEventType.APPLICATION_STATUS_CHANGED)
    assert p.channels == (NotificationChannel.IN_APP,)


def test_unmapped_event_has_no_policy():
    # SCHEME_VERSION_ACTIVATED is intentionally not citizen-notified.
    assert policies.policy_for(DomainEventType.SCHEME_VERSION_ACTIVATED) is None
    assert policies.policy_for(DomainEventType.DOCUMENT_UPLOADED) is None


# ------------------------------ delivery ------------------------------------ #
def test_retryable_classification():
    assert delivery.is_retryable(DeliveryErrorCode.TIMEOUT)
    assert delivery.is_retryable(DeliveryErrorCode.RATE_LIMITED)
    assert delivery.is_retryable(DeliveryErrorCode.TRANSIENT_PROVIDER_ERROR)
    assert not delivery.is_retryable(DeliveryErrorCode.INVALID_EMAIL)
    assert not delivery.is_retryable(DeliveryErrorCode.INVALID_PHONE)
    assert not delivery.is_retryable(DeliveryErrorCode.UNSUPPORTED_CHANNEL)


def test_backoff_is_monotonic_and_capped():
    from app.core.config import get_settings

    s = get_settings()
    from datetime import datetime, timezone

    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    d1 = (delivery.next_attempt_at(1, s, now) - now).total_seconds()
    d2 = (delivery.next_attempt_at(2, s, now) - now).total_seconds()
    d3 = (delivery.next_attempt_at(3, s, now) - now).total_seconds()
    assert d1 < d2 < d3  # exponential growth
    dbig = (delivery.next_attempt_at(50, s, now) - now).total_seconds()
    assert dbig <= s.notification_backoff_max_seconds + s.notification_backoff_jitter_seconds


def test_attempts_exhausted():
    from app.core.config import get_settings

    s = get_settings()
    assert not delivery.attempts_exhausted(1, s)
    assert delivery.attempts_exhausted(s.notification_max_attempts, s)
