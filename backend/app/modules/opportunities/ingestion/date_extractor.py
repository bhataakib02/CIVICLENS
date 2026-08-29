"""Date extraction, classification, and status determination (prompt §15, §16).

Distinguishes: Published Date, Application Open Date, Application Deadline, Exam Date, Interview Date, Event Date.
Calculates deadline status: UPCOMING, OPEN, CLOSING_SOON, CLOSED, DATE_UNKNOWN.
Never infers deadlines without evidence.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Tuple

from app.models.enums import OpportunityDeadlineStatus


class DateClassifier:
    """Classifies dates and computes opportunity status."""

    @staticmethod
    def parse_datetime(date_str: Optional[str]) -> Optional[datetime]:
        if not date_str:
            return None
        try:
            from dateutil import parser as date_parser
            dt = date_parser.parse(date_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            pass

        # Stdlib fallbacks
        clean_str = date_str.strip()
        formats = [
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%d %b %Y",
            "%d %B %Y",
            "%d/%m/%Y",
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(clean_str, fmt)
                return dt.replace(tzinfo=timezone.utc)
            except Exception:
                continue
        return None

    @classmethod
    def calculate_status(
        cls,
        open_date: Optional[datetime],
        deadline: Optional[datetime],
        event_date: Optional[datetime] = None,
        now: Optional[datetime] = None,
    ) -> OpportunityDeadlineStatus:
        now = now or datetime.now(timezone.utc)

        if deadline is None:
            if event_date and event_date < now:
                return OpportunityDeadlineStatus.CLOSED
            return OpportunityDeadlineStatus.DATE_UNKNOWN

        if deadline < now:
            return OpportunityDeadlineStatus.CLOSED

        seconds_left = (deadline - now).total_seconds()
        days_left = seconds_left / 86400.0

        if open_date and open_date > now:
            return OpportunityDeadlineStatus.UPCOMING

        if days_left <= 5.0:
            return OpportunityDeadlineStatus.CLOSING_SOON

        return OpportunityDeadlineStatus.OPEN
