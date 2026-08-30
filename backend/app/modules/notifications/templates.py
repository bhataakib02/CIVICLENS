"""Versioned, localized notification templates (prompt §24, §25, §26, §48).

- Templates are keyed by (event_type, version) and hold per-language title/body.
- Rendering uses str.format_map with a defaultdict so a missing variable becomes
  an empty placeholder rather than raising or leaking internals — and NEVER
  concatenates raw HTML/user input into trusted markup (plain-text bodies).
- Localization: the requested language is used if present, else falls back to
  English (prompt §26). Unavailable translations are NOT machine-generated.
- The version used is recorded on the notification so historical notifications
  never change when a template is later edited (prompt §25).
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from app.models.enums import DomainEventType

DEFAULT_LANGUAGE = "en"


@dataclass(frozen=True)
class RenderedTemplate:
    template_key: str
    version: int
    language: str
    title: str
    body: str


@dataclass(frozen=True)
class _TemplateDef:
    version: int
    # language -> (title, body). 'en' is mandatory (fallback).
    by_language: dict[str, tuple[str, str]]


# key -> current template definition. Versioned: to change copy, add a new
# _TemplateDef with a higher version (old notifications keep their version).
_TEMPLATES: dict[str, _TemplateDef] = {
    DomainEventType.APPLICATION_SUBMITTED.value: _TemplateDef(
        version=1,
        by_language={
            "en": ("Application submitted",
                   "Your application {application_number} has been submitted successfully."),
            "bn": ("আবেদন জমা দেওয়া হয়েছে",
                   "আপনার আবেদন {application_number} সফলভাবে জমা দেওয়া হয়েছে।"),
            "hi": ("आवेदन जमा किया गया",
                   "आपका आवेदन {application_number} सफलतापूर्वक जमा कर दिया गया है।"),
        },
    ),
    DomainEventType.APPLICATION_STATUS_CHANGED.value: _TemplateDef(
        version=1,
        by_language={
            "en": ("Application status updated",
                   "Your application {application_number} status is now {status}."),
            "hi": ("आवेदन की स्थिति अपडेट हुई",
                   "आपके आवेदन {application_number} की स्थिति अब {status} है।"),
        },
    ),
    DomainEventType.APPLICATION_ACTION_REQUIRED.value: _TemplateDef(
        version=1,
        by_language={
            "en": ("Action required",
                   "Action is required on your application {application_number}."),
            "bn": ("পদক্ষেপ প্রয়োজন",
                   "আপনার আবেদন {application_number}-এ পদক্ষেপ প্রয়োজন।"),
        },
    ),
    DomainEventType.APPLICATION_APPROVED.value: _TemplateDef(
        version=1,
        by_language={
            "en": ("Application approved",
                   "Good news — your application {application_number} was approved."),
        },
    ),
    DomainEventType.APPLICATION_REJECTED.value: _TemplateDef(
        version=1,
        by_language={
            "en": ("Application rejected",
                   "Your application {application_number} was not approved."),
        },
    ),
    DomainEventType.APPLICATION_COMPLETED.value: _TemplateDef(
        version=1,
        by_language={
            "en": ("Application complete",
                   "Your application {application_number} is now complete."),
        },
    ),
    DomainEventType.DOCUMENT_VERIFICATION_REQUIRED.value: _TemplateDef(
        version=1,
        by_language={
            "en": ("Document verification required",
                   "A document you submitted needs verification."),
        },
    ),
    DomainEventType.DOCUMENT_PROCESSING_COMPLETED.value: _TemplateDef(
        version=1,
        by_language={
            "en": ("Document processed",
                   "Your document has been processed."),
        },
    ),
    DomainEventType.DOCUMENT_VERIFIED.value: _TemplateDef(
        version=1,
        by_language={
            "en": ("Document verified", "Your document has been verified."),
        },
    ),
    DomainEventType.ELIGIBILITY_CHECK_COMPLETED.value: _TemplateDef(
        version=1,
        by_language={
            "en": ("Eligibility check complete",
                   "An eligibility check has completed: {decision}."),
        },
    ),
    DomainEventType.OPPORTUNITY_PUBLISHED.value: _TemplateDef(
        version=1,
        by_language={
            "en": ("New Opportunity Published",
                   "A new opportunity '{title}' from {organization} has been published."),
            "bn": ("নতুন সুযোগ প্রকাশিত হয়েছে",
                   "{organization} থেকে নতুন সুযোগ '{title}' প্রকাশিত হয়েছে।"),
            "hi": ("नया अवसर प्रकाशित हुआ",
                   "{organization} से नया अवसर '{title}' प्रकाशित किया गया है।"),
        },
    ),
    DomainEventType.OPPORTUNITY_UPDATED.value: _TemplateDef(
        version=1,
        by_language={
            "en": ("Opportunity Details Updated",
                   "Details for opportunity '{title}' from {organization} have been updated."),
            "hi": ("अवसर विवरण अपडेट हुआ",
                   "{organization} से अवसर '{title}' के विवरण अपडेट किए गए हैं।"),
        },
    ),
}


def has_template(event_type: str) -> bool:
    return event_type in _TEMPLATES


def render(event_type: str, *, language: str, variables: dict) -> RenderedTemplate:
    """Render the current template for the event in the requested language,
    falling back to English (prompt §26). Safe variable substitution only."""
    definition = _TEMPLATES.get(event_type)
    if definition is None:
        # Generic, safe default so an unmapped event still yields a valid record.
        safe_vars = defaultdict(str, variables or {})
        return RenderedTemplate(
            template_key=event_type, version=1, language=DEFAULT_LANGUAGE,
            title="Notification", body="You have a new notification.",
        )

    lang = language if language in definition.by_language else DEFAULT_LANGUAGE
    title_tpl, body_tpl = definition.by_language[lang]
    safe_vars = defaultdict(str, {k: ("" if v is None else str(v)) for k, v in (variables or {}).items()})
    return RenderedTemplate(
        template_key=event_type,
        version=definition.version,
        language=lang,
        title=title_tpl.format_map(safe_vars),
        body=body_tpl.format_map(safe_vars),
    )
