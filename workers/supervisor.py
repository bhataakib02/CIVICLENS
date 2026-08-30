"""Multi-worker process supervisor (CivicLens Background Daemon).

Runs both background worker loops concurrently within a single container process:
1. Notification Outbox Worker (app.modules.notifications.worker)
2. Opportunity Crawler Scheduler Daemon (app.modules.opportunities.worker)

Handles SIGTERM / SIGINT signals gracefully for clean worker shutdown.
"""
from __future__ import annotations

import signal
import sys
import threading
import time

from app.core.logging import configure_logging, get_logger
from app.modules.notifications.worker import run_forever as run_notification_worker
from app.modules.opportunities.worker import start_worker_loop as run_opportunity_worker

logger = get_logger("civiclens.worker.supervisor")
_shutdown_event = threading.Event()


def _run_notifications_thread() -> None:
    logger.info("starting_notifications_worker_thread")
    try:
        run_notification_worker()
    except Exception as exc:
        logger.error("notifications_worker_thread_crashed", exc_info=True)


def _run_opportunities_thread() -> None:
    logger.info("starting_opportunities_worker_thread")
    try:
        run_opportunity_worker(poll_interval_seconds=30)
    except Exception as exc:
        logger.error("opportunities_worker_thread_crashed", exc_info=True)


def main() -> None:
    configure_logging()
    logger.info("civiclens_worker_supervisor_starting")

    t_notif = threading.Thread(target=_run_notifications_thread, name="NotificationWorker", daemon=True)
    t_opps = threading.Thread(target=_run_opportunities_thread, name="OpportunityWorker", daemon=True)

    t_notif.start()
    t_opps.start()

    def handle_signal(signum, frame):
        logger.info("signal_received_shutting_down", extra={"signal": signum})
        _shutdown_event.set()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    logger.info("all_worker_threads_running")

    while not _shutdown_event.is_set():
        if not t_notif.is_alive():
            logger.warning("notification_worker_thread_dead_restarting")
            t_notif = threading.Thread(target=_run_notifications_thread, name="NotificationWorker", daemon=True)
            t_notif.start()

        if not t_opps.is_alive():
            logger.warning("opportunity_worker_thread_dead_restarting")
            t_opps = threading.Thread(target=_run_opportunities_thread, name="OpportunityWorker", daemon=True)
            t_opps.start()

        time.sleep(5.0)


if __name__ == "__main__":
    main()
