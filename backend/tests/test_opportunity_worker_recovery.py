"""Worker crash and lease expiration recovery test (prompt §48).

Simulates:
1. Worker A acquires distributed crawl lease for a source.
2. Worker A crashes unexpectedly without releasing the lock.
3. Lease expires (TTL timeout).
4. Worker B acquires expired lease and completes the crawl job.
"""
from __future__ import annotations

import time
import pytest
from unittest.mock import patch, MagicMock

from app.models.enums import OpportunityAuthorityLevel
from app.modules.opportunities.repository import OpportunityRepository
from app.modules.opportunities.schemas import OpportunitySourceCreate
from app.modules.opportunities.scheduler.locking import DistributedCrawlLock
from app.modules.opportunities.scheduler.service import OpportunityScheduler


def test_worker_crash_and_lease_recovery(db_session_factory):
    session_a = db_session_factory()
    session_b = db_session_factory()

    try:
        repo_a = OpportunityRepository(session_a)
        source = repo_a.create_source(
            OpportunitySourceCreate(
                name="Worker Crash Recovery Test Source",
                domain="worker-crash-test.gov.in",
                base_url="https://worker-crash-test.gov.in/notices",
                authority_level=OpportunityAuthorityLevel.OFFICIAL.value,
                crawl_frequency="30_minutes",
                enabled=True,
            )
        )
        session_a.commit()
        source_id = source.id

        lock_mgr_a = DistributedCrawlLock(session_a)
        lock_mgr_b = DistributedCrawlLock(session_b)

        # 1. Worker A acquires lease with short TTL (1 second)
        token_a = lock_mgr_a.acquire_lock(source_id, ttl_seconds=1)
        assert token_a is not None, "Worker A failed to acquire initial lock"

        # 2. Worker B attempts acquisition while Worker A's lock is active -> must fail (None)
        token_b_immediate = lock_mgr_b.acquire_lock(source_id, ttl_seconds=10)
        assert token_b_immediate is None, "Worker B acquired lock while Worker A lease was active!"

        # 3. Simulate Worker A CRASH (Worker A crashes without calling release_lock)
        # Wait for Worker A's lease to expire (TTL = 1s)
        time.sleep(1.2)

        # 4. Worker B attempts acquisition after lease expiration -> must succeed
        token_b_recovered = lock_mgr_b.acquire_lock(source_id, ttl_seconds=60)
        assert token_b_recovered is not None, "Worker B failed to acquire lock after Worker A lease expiration!"

        # 5. Worker B executes crawl to completion
        mock_doc = MagicMock()
        mock_doc.url = "https://worker-crash-test.gov.in/notices/job-01"
        mock_doc.content = "<html><body><h1>Recovered Worker Job 2026</h1></body></html>"
        mock_doc.content_type = "text/html"
        mock_doc.source_identifier = "RECOV-01"

        scheduler_b = OpportunityScheduler(session_b)
        with patch("app.modules.opportunities.service.HTMLConnector.fetch_items", return_value=[mock_doc]):
            crawl_res = scheduler_b.service.crawl_source(source_id)
            assert crawl_res["status"] == "COMPLETED"
            assert crawl_res["discovered"] == 1

        lock_mgr_b.release_lock(source_id, token_b_recovered)

    finally:
        session_a.close()
        session_b.close()
