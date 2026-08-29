"""Delivery retry policy: backoff + error classification (prompt §31, §46).

Transient errors retry with exponential backoff + jitter up to a bounded number
of attempts; permanent errors do not retry. After the attempt budget is
exhausted the event is dead-lettered (handled in service.py).
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

from app.core.config import Settings, get_settings
from app.models.enums import DeliveryErrorCode

RETRYABLE = {
    DeliveryErrorCode.TRANSIENT_PROVIDER_ERROR,
    DeliveryErrorCode.TIMEOUT,
    DeliveryErrorCode.RATE_LIMITED,
}

PERMANENT = {
    DeliveryErrorCode.INVALID_EMAIL,
    DeliveryErrorCode.INVALID_PHONE,
    DeliveryErrorCode.UNSUPPORTED_CHANNEL,
    DeliveryErrorCode.RECIPIENT_OPTED_OUT,
    DeliveryErrorCode.PROVIDER_UNAVAILABLE,
}


def is_retryable(error_code: DeliveryErrorCode | None) -> bool:
    if error_code is None:
        return True  # unknown transient failure -> retry (bounded)
    return error_code in RETRYABLE


def next_attempt_at(attempt_count: int, settings: Settings | None = None,
                    now: datetime | None = None) -> datetime:
    """Exponential backoff with jitter, capped at the configured max.

    attempt_count is the number of attempts already made (>=1 when scheduling
    the next retry)."""
    s = settings or get_settings()
    now = now or datetime.now(timezone.utc)
    base = s.notification_backoff_base_seconds
    delay = base * (2 ** max(0, attempt_count - 1))
    delay = min(delay, s.notification_backoff_max_seconds)
    if s.notification_backoff_jitter_seconds > 0:
        delay += random.uniform(0, s.notification_backoff_jitter_seconds)
    return now + timedelta(seconds=delay)


def attempts_exhausted(attempt_count: int, settings: Settings | None = None) -> bool:
    s = settings or get_settings()
    return attempt_count >= s.notification_max_attempts
