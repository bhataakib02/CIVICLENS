"""Crawl scheduling policies and exponential backoff calculations (prompt §3, §7, §8)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional


class CrawlPolicyManager:
    """Calculates next crawl times and failure backoffs."""

    # Default interval mappings in minutes
    INTERVAL_MAP = {
        "30_minutes": 30,
        "hourly": 60,
        "1_hour": 60,
        "3_hours": 180,
        "6_hours": 360,
        "12_hours": 720,
        "daily": 1440,
        "24_hours": 1440,
    }

    @classmethod
    def parse_interval_minutes(cls, frequency_str: str, default: int = 30) -> int:
        freq_norm = (frequency_str or "").lower().strip()
        if freq_norm in cls.INTERVAL_MAP:
            return cls.INTERVAL_MAP[freq_norm]
        try:
            val = int(freq_norm)
            return max(val, 15)  # min 15 minutes safety floor
        except ValueError:
            return default

    @classmethod
    def calculate_next_crawl_time(
        cls,
        frequency_str: str,
        last_success: Optional[datetime] = None,
        consecutive_failures: int = 0,
        now: Optional[datetime] = None,
    ) -> datetime:
        now = now or datetime.now(timezone.utc)

        base_minutes = cls.parse_interval_minutes(frequency_str)

        if consecutive_failures > 0:
            # Bounded exponential backoff: 5m, 10m, 20m, 30m, 60m max
            backoff_sequence = [5, 10, 20, 30, 60]
            idx = min(consecutive_failures - 1, len(backoff_sequence) - 1)
            additional_delay = backoff_sequence[idx]
            return now + timedelta(minutes=additional_delay)

        return now + timedelta(minutes=base_minutes)
