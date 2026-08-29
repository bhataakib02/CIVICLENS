"""Opportunity Discovery Continuous 30-Minute Scheduler (prompt §1-§10).

Executes automated continuous discovery cycles every 30 minutes without user interaction.
Supports distributed locking, per-source schedules, failure backoffs, and health tracking.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.session import get_sessionmaker
from app.models.enums import OpportunityAuthorityLevel
from app.models.opportunity import OpportunitySource, CrawlRun
from app.modules.opportunities.repository import OpportunityRepository
from app.modules.opportunities.service import OpportunityService
from app.modules.opportunities.scheduler.locking import DistributedCrawlLock
from app.modules.opportunities.scheduler.policies import CrawlPolicyManager

logger = get_logger("civiclens.opportunities.scheduler")


class OpportunityScheduler:
    """Persistent background scheduler executing 30-minute discovery cycles."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.repo = OpportunityRepository(session)
        self.service = OpportunityService(session)
        self.lock_mgr = DistributedCrawlLock(session)

    def run_discovery_cycle(self) -> Dict[str, Any]:
        """Execute a discovery cycle for all due sources."""
        now = datetime.now(timezone.utc)
        enabled_sources = self.repo.list_sources(enabled_only=True)
        processed = 0
        skipped = 0
        locked = 0
        details = []

        for source in enabled_sources:
            # Check if source is due
            crawl_policy = source.crawl_policy or {}
            next_crawl_str = crawl_policy.get("next_crawl_at")
            consecutive_failures = crawl_policy.get("consecutive_failures", 0)

            is_due = True
            if next_crawl_str:
                try:
                    next_crawl = datetime.fromisoformat(next_crawl_str)
                    if next_crawl > now:
                        is_due = False
                except Exception:
                    is_due = True

            if not is_due:
                skipped += 1
                continue

            # Acquire lock to prevent duplicate runs
            lock_token = self.lock_mgr.acquire_lock(source.id, ttl_seconds=600)
            if not lock_token:
                locked += 1
                continue

            try:
                logger.info("starting_scheduled_crawl", extra={"source_id": str(source.id), "source_name": source.name})
                crawl_res = self.service.crawl_source(source.id)

                # Update crawl metrics & next schedule
                if crawl_res.get("status") == "COMPLETED":
                    consecutive_failures = 0
                    source.last_crawled_at = now
                    source.last_successful_crawl_at = now
                    source.last_error = None
                else:
                    consecutive_failures += 1
                    source.last_error_at = now
                    source.last_error = crawl_res.get("error", "Crawl failed")

                next_crawl = CrawlPolicyManager.calculate_next_crawl_time(
                    frequency_str=source.crawl_frequency,
                    last_success=source.last_successful_crawl_at,
                    consecutive_failures=consecutive_failures,
                    now=now,
                )

                source.crawl_policy = {
                    **(source.crawl_policy or {}),
                    "next_crawl_at": next_crawl.isoformat(),
                    "consecutive_failures": consecutive_failures,
                    "last_status": crawl_res.get("status"),
                }

                self.session.commit()
                processed += 1
                details.append(crawl_res)
            except Exception as exc:
                self.session.rollback()
                logger.error("scheduled_crawl_error", extra={"source_id": str(source.id), "error": str(exc)})
            finally:
                self.lock_mgr.release_lock(source.id, lock_token)

        summary = {
            "timestamp": now.isoformat(),
            "processed": processed,
            "skipped": skipped,
            "locked_or_busy": locked,
            "details": details,
        }
        logger.info("discovery_cycle_completed", extra=summary)
        return summary


def trigger_scheduler_task() -> Dict[str, Any]:
    """Helper entry point for celery worker / background thread."""
    session = get_sessionmaker()()
    try:
        scheduler = OpportunityScheduler(session)
        return scheduler.run_discovery_cycle()
    finally:
        session.close()
