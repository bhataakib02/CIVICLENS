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


def test_scheduler_race_condition_locks_out_second_instance(db_session_factory):
    """Section 9: Run two scheduler lock attempts against the same due source concurrently.

    Expected: exactly 1 token acquired, second instance locked out (0 duplicate runs).
    """
    from app.modules.opportunities.repository import OpportunityRepository
    from app.modules.opportunities.schemas import OpportunitySourceCreate
    from app.modules.opportunities.scheduler.locking import DistributedCrawlLock

    session = db_session_factory()
    try:
        repo = OpportunityRepository(session)
        source = repo.create_source(
            OpportunitySourceCreate(
                name="Race Test Source",
                domain="race.gov.in",
                base_url="https://race.gov.in",
                authority_level="OFFICIAL",
            )
        )
        lock_mgr = DistributedCrawlLock(session)

        # First instance acquires lock
        token1 = lock_mgr.acquire_lock(source.id, ttl_seconds=60)
        assert token1 is not None

        # Second instance races to acquire lock on same source.id
        token2 = lock_mgr.acquire_lock(source.id, ttl_seconds=60)
        assert token2 is None  # Second instance MUST be locked out

        # Clean up lock
        lock_mgr.release_lock(source.id, token1)
    finally:
        session.close()


def test_worker_crash_lease_recovery(db_session_factory):
    """Section 10: Worker A acquires lock/lease, crashes (lease expires), Worker B recovers lease.

    Expected: Worker B successfully acquires lease after TTL expiration and completes job.
    """
    import time
    from app.modules.opportunities.repository import OpportunityRepository
    from app.modules.opportunities.schemas import OpportunitySourceCreate
    from app.modules.opportunities.scheduler.locking import DistributedCrawlLock

    session = db_session_factory()
    try:
        repo = OpportunityRepository(session)
        source = repo.create_source(
            OpportunitySourceCreate(
                name="Crash Test Source",
                domain="crash.gov.in",
                base_url="https://crash.gov.in",
                authority_level="OFFICIAL",
            )
        )
        lock_mgr = DistributedCrawlLock(session)

        # Worker A acquires short 1-second lease and crashes
        token_a = lock_mgr.acquire_lock(source.id, ttl_seconds=1)
        assert token_a is not None

        # Worker A crashes (does not call release_lock). Wait 1.1s for lease to expire
        time.sleep(1.1)

        # Worker B picks up expired job
        token_b = lock_mgr.acquire_lock(source.id, ttl_seconds=60)
        assert token_b is not None  # Worker B successfully recovers lease
        assert token_b != token_a

        # Worker B completes job and releases lease
        lock_mgr.release_lock(source.id, token_b)
    finally:
        session.close()



