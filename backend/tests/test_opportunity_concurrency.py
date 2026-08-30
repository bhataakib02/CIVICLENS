"""Concurrency and distributed locking test for crawler scheduler (prompt §47).

Executes Scheduler A and Scheduler B concurrently against the same due source.
Verifies that distributed lease locking prevents duplicate crawl jobs.
"""
from __future__ import annotations

import concurrent.futures
import pytest
from unittest.mock import patch, MagicMock

from app.models.enums import OpportunityAuthorityLevel
from app.modules.opportunities.repository import OpportunityRepository
from app.modules.opportunities.schemas import OpportunitySourceCreate
from app.modules.opportunities.scheduler.service import OpportunityScheduler


def test_scheduler_concurrency_race_protection(db_session_factory):
    session1 = db_session_factory()
    repo1 = OpportunityRepository(session1)
    source = repo1.create_source(
        OpportunitySourceCreate(
            name="Concurrent Test Government Portal",
            domain="concurrent-govt.gov.in",
            base_url="https://concurrent-govt.gov.in/jobs",
            authority_level=OpportunityAuthorityLevel.OFFICIAL.value,
            crawl_frequency="30_minutes",
            enabled=True,
        )
    )
    session1.commit()

    session2 = db_session_factory()

    try:
        lock_results = []
        import time

        def run_crawl_lock_attempt(sess):
            scheduler = OpportunityScheduler(sess)
            token = scheduler.lock_mgr.acquire_lock(source.id, ttl_seconds=60)
            if token:
                time.sleep(0.3)
                scheduler.lock_mgr.release_lock(source.id, token)
                return "ACQUIRED"
            return "LOCKED"

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future1 = executor.submit(run_crawl_lock_attempt, session1)
            future2 = executor.submit(run_crawl_lock_attempt, session2)

            res1 = future1.result()
            res2 = future2.result()

        results = [res1, res2]
        assert results.count("ACQUIRED") == 1, f"Expected exactly 1 ACQUIRED, got {results}"
        assert results.count("LOCKED") == 1, f"Expected exactly 1 LOCKED, got {results}"

    finally:
        session1.close()
        session2.close()
