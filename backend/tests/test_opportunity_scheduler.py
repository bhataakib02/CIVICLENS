"""Unit tests for 30-minute opportunity scheduler, locking, and failure backoff policy."""
import pytest
from datetime import datetime, timezone

from app.modules.opportunities.scheduler.policies import CrawlPolicyManager


def test_crawl_policy_parse_interval():
    assert CrawlPolicyManager.parse_interval_minutes("30_minutes") == 30
    assert CrawlPolicyManager.parse_interval_minutes("hourly") == 60
    assert CrawlPolicyManager.parse_interval_minutes("daily") == 1440


def test_crawl_policy_calculate_next_crawl_with_failures():
    now = datetime.now(timezone.utc)
    # Success case
    next_success = CrawlPolicyManager.calculate_next_crawl_time("30_minutes", now=now)
    assert (next_success - now).total_seconds() == 1800  # 30 minutes

    # Failure #1 -> 5 min backoff
    next_fail1 = CrawlPolicyManager.calculate_next_crawl_time("30_minutes", consecutive_failures=1, now=now)
    assert (next_fail1 - now).total_seconds() == 300  # 5 minutes

    # Failure #3 -> 20 min backoff
    next_fail3 = CrawlPolicyManager.calculate_next_crawl_time("30_minutes", consecutive_failures=3, now=now)
    assert (next_fail3 - now).total_seconds() == 1200  # 20 minutes
