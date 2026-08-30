"""Notification policies (prompt §15, §38).

Maps a domain event -> the channels it may use, its notification category, and
priority. This is server-side authoritative: a citizen can never cause an
arbitrary channel/recipient combination — the policy decides. Events not mapped
here produce NO notification (avoids spam, prompt §15).

`mandatory_channels` are delivered even if the recipient opted the category out
(reserved for security alerts, prompt §16). None here yet, but the mechanism is
present so security-critical events cannot be silenced.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.models.enums import (
    DomainEventType,
    NotificationCategory,
    NotificationChannel,
    NotificationPriority,
)

Ch = NotificationChannel
Cat = NotificationCategory
Pri = NotificationPriority


@dataclass(frozen=True)
class NotificationPolicy:
    channels: tuple[NotificationChannel, ...]
    category: NotificationCategory
    priority: NotificationPriority = Pri.NORMAL
    # Channels that ignore category opt-out (security-mandatory).
    mandatory_channels: tuple[NotificationChannel, ...] = field(default_factory=tuple)


# IN_APP is always included where a citizen-facing notification is warranted.
_POLICIES: dict[DomainEventType, NotificationPolicy] = {
    DomainEventType.APPLICATION_SUBMITTED: NotificationPolicy(
        (Ch.IN_APP, Ch.EMAIL), Cat.STATUS_CHANGE, Pri.NORMAL),
    DomainEventType.APPLICATION_STATUS_CHANGED: NotificationPolicy(
        (Ch.IN_APP,), Cat.STATUS_CHANGE, Pri.NORMAL),
    DomainEventType.APPLICATION_ACTION_REQUIRED: NotificationPolicy(
        (Ch.IN_APP, Ch.EMAIL, Ch.SMS), Cat.STATUS_CHANGE, Pri.HIGH),
    DomainEventType.APPLICATION_APPROVED: NotificationPolicy(
        (Ch.IN_APP, Ch.EMAIL), Cat.STATUS_CHANGE, Pri.HIGH),
    DomainEventType.APPLICATION_REJECTED: NotificationPolicy(
        (Ch.IN_APP, Ch.EMAIL), Cat.STATUS_CHANGE, Pri.HIGH),
    DomainEventType.APPLICATION_COMPLETED: NotificationPolicy(
        (Ch.IN_APP, Ch.EMAIL), Cat.STATUS_CHANGE, Pri.NORMAL),
    DomainEventType.APPLICATION_WITHDRAWN: NotificationPolicy(
        (Ch.IN_APP,), Cat.STATUS_CHANGE, Pri.LOW),
    DomainEventType.DOCUMENT_VERIFICATION_REQUIRED: NotificationPolicy(
        (Ch.IN_APP,), Cat.DOC_REVERIFICATION, Pri.NORMAL),
    DomainEventType.DOCUMENT_PROCESSING_COMPLETED: NotificationPolicy(
        (Ch.IN_APP,), Cat.DOC_REVERIFICATION, Pri.LOW),
    DomainEventType.DOCUMENT_VERIFIED: NotificationPolicy(
        (Ch.IN_APP,), Cat.DOC_REVERIFICATION, Pri.LOW),
    DomainEventType.ELIGIBILITY_CHECK_COMPLETED: NotificationPolicy(
        (Ch.IN_APP,), Cat.SCHEME_MATCH, Pri.LOW),
    DomainEventType.OPPORTUNITY_PUBLISHED: NotificationPolicy(
        (Ch.IN_APP,), Cat.SCHEME_MATCH, Pri.NORMAL),
    DomainEventType.OPPORTUNITY_UPDATED: NotificationPolicy(
        (Ch.IN_APP,), Cat.SCHEME_MATCH, Pri.LOW),
}

# Which preference category flag governs each notification category.
_CATEGORY_PREF_FLAG = {
    Cat.STATUS_CHANGE: "application_updates",
    Cat.DOC_REVERIFICATION: "document_updates",
    Cat.SCHEME_MATCH: "scheme_updates",
    Cat.DEADLINE_REMINDER: "application_updates",
}


def policy_for(event_type: DomainEventType) -> NotificationPolicy | None:
    return _POLICIES.get(event_type)


def preference_flag_for_category(category: NotificationCategory) -> str:
    return _CATEGORY_PREF_FLAG.get(category, "application_updates")
