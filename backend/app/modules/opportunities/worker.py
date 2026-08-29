"""Background worker for opportunity crawling, link verification, continuous scheduler, and freshness updates (prompt §52, §53)."""
from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.session import get_sessionmaker
from app.models.opportunity import Opportunity, OpportunitySource, OpportunityLink
from app.models.enums import OpportunityDeadlineStatus
from app.modules.opportunities.ingestion.date_extractor import DateClassifier
from app.modules.opportunities.ingestion.link_validator import LinkValidator
from app.modules.opportunities.service import OpportunityService
from app.modules.opportunities.scheduler.service import OpportunityScheduler

logger = get_logger("civiclens.opportunities.worker")


def run_scheduled_crawls(session: Session | None = None) -> dict:
    """Execute continuous 30-minute discovery cycle across all due sources."""
    session = session or get_sessionmaker()()
    try:
        scheduler = OpportunityScheduler(session)
        return scheduler.run_discovery_cycle()
    finally:
        session.close()


def run_link_verifications(session: Session | None = None) -> dict:
    """Verify application links and mark dead links invalid (prompt §24)."""
    session = session or get_sessionmaker()()
    try:
        validator = LinkValidator()
        links = session.query(OpportunityLink).filter(OpportunityLink.is_valid == True).all()
        verified_count = 0
        broken_count = 0

        for link in links:
            res = validator.validate_link(link.url, link.domain)
            link.http_status = res.http_status
            link.is_valid = res.is_valid
            link.verified_at = datetime.now(timezone.utc)
            if not res.is_valid:
                broken_count += 1
            verified_count += 1

        session.commit()
        logger.info("link_verifications_completed", extra={"verified": verified_count, "broken": broken_count})
        return {"verified": verified_count, "broken": broken_count}
    finally:
        session.close()


def run_deadline_status_updates(session: Session | None = None) -> dict:
    """Recalculate deadline statuses for active opportunities (prompt §16)."""
    session = session or get_sessionmaker()()
    try:
        now = datetime.now(timezone.utc)
        opps = session.query(Opportunity).filter(Opportunity.status != OpportunityDeadlineStatus.CLOSED).all()
        updated_count = 0

        for opp in opps:
            new_status = DateClassifier.calculate_status(
                open_date=opp.application_open_date,
                deadline=opp.application_deadline,
                event_date=opp.event_date,
                now=now,
            )
            if opp.status != new_status:
                opp.status = new_status
                updated_count += 1

        session.commit()
        logger.info("deadline_status_updates_completed", extra={"updated": updated_count})
        return {"updated": updated_count}
    finally:
        session.close()


def start_worker_loop(poll_interval_seconds: int = 60) -> None:
    """Continuous worker daemon loop executing periodic discovery cycles and verifications."""
    logger.info("starting_opportunity_worker_loop", extra={"poll_interval": poll_interval_seconds})
    last_link_verify = 0.0

    while True:
        try:
            run_scheduled_crawls()
            run_deadline_status_updates()

            # Run link verifications every 6 hours
            if time.time() - last_link_verify > 21600:
                run_link_verifications()
                last_link_verify = time.time()

        except Exception as exc:
            logger.error("opportunity_worker_loop_error", extra={"error": str(exc)})

        time.sleep(poll_interval_seconds)


if __name__ == "__main__":
    start_worker_loop()
