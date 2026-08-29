"""Outbox event worker entrypoint (prompt §8, §50).

Run as a separate process:  python -m app.modules.notifications.worker

Polls the transactional outbox in bounded batches (backpressure — prompt §50)
and drains due events into notifications. Multiple instances are safe because
claiming uses FOR UPDATE SKIP LOCKED. In-process one-shot dispatch (used by the
API/tests) calls OutboxDispatcher.dispatch_pending directly.
"""
from __future__ import annotations

import time

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.modules.notifications.service import OutboxDispatcher

logger = get_logger("civiclens.notifications.worker")


def run_forever(poll_interval_seconds: float = 1.0) -> None:  # pragma: no cover - long-running
    configure_logging()
    settings = get_settings()
    logger.info("outbox_worker_started",
                extra={"batch_size": settings.outbox_worker_batch_size})
    while True:
        try:
            n = OutboxDispatcher(settings=settings).dispatch_pending()
            if n == 0:
                time.sleep(poll_interval_seconds)
        except Exception:
            logger.error("outbox_worker_iteration_failed", exc_info=True)
            time.sleep(poll_interval_seconds)


if __name__ == "__main__":  # pragma: no cover
    run_forever()
