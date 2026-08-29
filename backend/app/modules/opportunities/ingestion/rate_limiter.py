"""Per-domain rate limiting for opportunity crawling (prompt §9)."""
from __future__ import annotations

import time
from typing import Dict

from app.core.logging import get_logger

logger = get_logger("civiclens.opportunities.rate_limiter")


class DomainRateLimiter:
    """In-memory sliding window rate limiter per domain."""

    def __init__(self, requests_per_minute: int = 30) -> None:
        self.requests_per_minute = requests_per_minute
        self._domain_requests: Dict[str, list[float]] = {}

    def acquire(self, domain: str) -> None:
        """Enforce rate limits per domain by sleeping if necessary."""
        now = time.time()
        window_start = now - 60.0

        if domain not in self._domain_requests:
            self._domain_requests[domain] = []

        timestamps = [t for t in self._domain_requests[domain] if t > window_start]
        self._domain_requests[domain] = timestamps

        if len(timestamps) >= self.requests_per_minute:
            sleep_needed = timestamps[0] + 60.0 - now
            if sleep_needed > 0:
                logger.info("rate_limit_wait", extra={"domain": domain, "seconds": round(sleep_needed, 2)})
                time.sleep(min(sleep_needed, 5.0))

        self._domain_requests[domain].append(time.time())
