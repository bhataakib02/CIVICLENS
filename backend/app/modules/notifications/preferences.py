"""Notification preferences: defaults, persistence, channel resolution
(prompt §16, §17).

Safe public-service defaults: application/document/scheme updates ON, security
alerts ON and NON-DISABLEABLE. No marketing opt-in. in_app is always on.
"""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import NotificationChannel
from app.models.notification import NotificationPreference

Ch = NotificationChannel


def get_or_create(session: Session, user_id: uuid.UUID) -> NotificationPreference:
    pref = session.scalar(
        select(NotificationPreference).where(NotificationPreference.user_id == user_id)
    )
    if pref is None:
        pref = NotificationPreference(user_id=user_id)  # model defaults = safe defaults
        session.add(pref)
        session.flush()
    return pref


# Fields a client may update. security_alerts is intentionally excluded — it is
# mandatory and cannot be disabled (prompt §16).
UPDATABLE_FIELDS = (
    "email_enabled", "sms_enabled", "push_enabled", "in_app_enabled",
    "application_updates", "document_updates", "scheme_updates",
)


def apply_update(pref: NotificationPreference, data: dict) -> NotificationPreference:
    for field_name in UPDATABLE_FIELDS:
        if field_name in data and data[field_name] is not None:
            setattr(pref, field_name, bool(data[field_name]))
    # security_alerts stays True regardless of input.
    pref.security_alerts = True
    return pref


def channel_enabled(pref: NotificationPreference, channel: NotificationChannel) -> bool:
    return {
        Ch.IN_APP: pref.in_app_enabled,
        Ch.EMAIL: pref.email_enabled,
        Ch.SMS: pref.sms_enabled,
        Ch.PUSH: pref.push_enabled,
    }.get(channel, False)


def category_enabled(pref: NotificationPreference, pref_flag: str) -> bool:
    return bool(getattr(pref, pref_flag, True))


def as_dict(pref: NotificationPreference) -> dict:
    return {
        "email_enabled": pref.email_enabled,
        "sms_enabled": pref.sms_enabled,
        "push_enabled": pref.push_enabled,
        "in_app_enabled": pref.in_app_enabled,
        "application_updates": pref.application_updates,
        "document_updates": pref.document_updates,
        "scheme_updates": pref.scheme_updates,
        "security_alerts": pref.security_alerts,
    }
