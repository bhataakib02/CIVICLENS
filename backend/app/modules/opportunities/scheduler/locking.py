"""Distributed locking and lease management for crawler scheduler (prompt §5, §6).

Uses Redis distributed locks when available; falls back to DB row locking / lease timestamps.
Prevents duplicate simultaneous crawls across multi-worker instances.
"""
from __future__ import annotations

import time
import uuid
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("civiclens.opportunities.scheduler.locking")


class DistributedCrawlLock:
    """Manages distributed leases per source to prevent duplicate concurrent execution."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.settings = get_settings()

    def acquire_lock(self, source_id: uuid.UUID, ttl_seconds: int = 600) -> Optional[str]:
        """Try acquiring a lock for source_id. Returns token string if acquired, None if locked."""
        token = str(uuid.uuid4())
        lock_key = f"lock:crawl_source:{source_id}"

        # 1. Try Redis Lock if Redis available
        if self.settings.redis_url:
            try:
                import redis

                r = redis.Redis.from_url(self.settings.redis_url)
                acquired = r.set(lock_key, token, ex=ttl_seconds, nx=True)
                if acquired:
                    logger.info("redis_lock_acquired", extra={"source_id": str(source_id), "ttl": ttl_seconds})
                    return token
                else:
                    logger.info("redis_lock_busy", extra={"source_id": str(source_id)})
                    return None
            except Exception as exc:
                logger.warning("redis_lock_fallback_to_db", extra={"error": str(exc)})

        # 2. DB Row Lease Fallback
        try:
            # Check DB lock table or source table update
            now_ts = time.time()
            res = self.session.execute(
                text(
                    """
                    UPDATE opportunity_sources
                    SET crawl_policy = jsonb_set(
                        COALESCE(crawl_policy, '{}'::jsonb),
                        '{lease}',
                        (:lease_json)::jsonb
                    )
                    WHERE id = :source_id
                    AND (
                        (crawl_policy->'lease'->>'expires_at') IS NULL
                        OR (crawl_policy->'lease'->>'expires_at')::float < :now_ts
                    )
                    RETURNING id
                    """
                ),
                {
                    "source_id": str(source_id),
                    "lease_json": f'{{"token": "{token}", "expires_at": {now_ts + ttl_seconds}}}',
                    "now_ts": now_ts,
                },
            ).fetchone()

            if res:
                self.session.commit()
                logger.info("db_lease_acquired", extra={"source_id": str(source_id)})
                return token
            else:
                logger.info("db_lease_busy", extra={"source_id": str(source_id)})
                return None
        except Exception as exc:
            self.session.rollback()
            logger.error("lock_acquisition_failed", extra={"error": str(exc)})
            return None

    def release_lock(self, source_id: uuid.UUID, token: str) -> None:
        """Release lock/lease for source_id."""
        lock_key = f"lock:crawl_source:{source_id}"

        # 1. Release Redis
        if self.settings.redis_url:
            try:
                import redis

                r = redis.Redis.from_url(self.settings.redis_url)
                val = r.get(lock_key)
                if val and val.decode("utf-8") == token:
                    r.delete(lock_key)
                    logger.info("redis_lock_released", extra={"source_id": str(source_id)})
            except Exception as exc:
                logger.warning("redis_lock_release_warning", extra={"error": str(exc)})

        # 2. Release DB lease
        try:
            self.session.execute(
                text(
                    """
                    UPDATE opportunity_sources
                    SET crawl_policy = crawl_policy - 'lease'
                    WHERE id = :source_id
                    AND (crawl_policy->'lease'->>'token') = :token
                    """
                ),
                {"source_id": str(source_id), "token": token},
            )
            self.session.commit()
        except Exception as exc:
            self.session.rollback()
            logger.warning("db_lease_release_warning", extra={"error": str(exc)})
