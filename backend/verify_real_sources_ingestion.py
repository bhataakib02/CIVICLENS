"""Script to run live ingestion verification across registered seed sources using real ephemeral Postgres DB."""
from __future__ import annotations

import os
import sys
import json
import tempfile
from datetime import datetime, timezone

import pgserver
from alembic import command
from alembic.config import Config

from app.core.config import get_settings
from app.db import session as db_session_mod
from app.models.enums import OpportunityAuthorityLevel, OpportunityType, OpportunitySourceType
from app.models.opportunity import Opportunity, OpportunitySource, CrawlRun, RawCrawlSnapshot
from app.modules.opportunities.service import OpportunityService
from app.seeds.seed_opportunities import seed as seed_opps


if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def run_live_source_verification():
    # 1. Start real ephemeral PostgreSQL via pgserver
    with tempfile.TemporaryDirectory() as tmp_dir:
        server = pgserver.get_server(tmp_dir)
        raw_uri = server.get_uri(database="postgres")
        db_url = raw_uri.replace("postgresql://", "postgresql+psycopg://", 1)

        os.environ["DATABASE_URL"] = db_url
        os.environ["ENVIRONMENT"] = "test"
        os.environ["JWT_SECRET_KEY"] = "test-secret-key-fixed-for-deterministic-tests-000000"

        get_settings.cache_clear()
        db_session_mod.reset_engine()

        # Run Alembic migrations
        here = os.path.dirname(os.path.abspath(__file__))
        cfg = Config(os.path.join(here, "alembic.ini"))
        cfg.set_main_option("script_location", os.path.join(here, "alembic"))
        command.upgrade(cfg, "head")

        SessionLocal = db_session_mod.get_sessionmaker()
        session = SessionLocal()

        print("=== 1. SEEDING / REGISTERING SOURCES ===")
        seed_res = seed_opps(session)
        print(f"Seed completed: {seed_res}")

        service = OpportunityService(session)
        sources = service.repo.list_sources(enabled_only=True)
        print(f"Total enabled registered sources: {len(sources)}")

        report = {}

        print("\n=== 2. RUNNING LIVE CRAWL PER SOURCE ===")
        for src in sources:
            print(f"\n--- Crawling Source: {src.name} ({src.domain}) ---")
            res = service.crawl_source(src.id)
            print(f"Crawl Result: {res}")

            # Fetch audit records
            runs = session.query(CrawlRun).filter(CrawlRun.source_id == src.id).order_by(CrawlRun.started_at.desc()).all()
            last_run = runs[0] if runs else None

            opps = session.query(Opportunity).filter(Opportunity.source_id == src.id).all()

            report[src.domain] = {
                "source_name": src.name,
                "authority_level": src.authority_level.value,
                "health_status": src.health_status,
                "consecutive_failures": src.consecutive_failures,
                "last_crawl_status": last_run.status if last_run else "NONE",
                "pages_fetched": last_run.pages_fetched if last_run else 0,
                "opportunities_found": len(opps),
                "sample_titles": [o.title for o in opps[:3]],
            }

        print("\n=== 3. PROVING COVERAGE ACROSS TYPES & STATES ===")
        type_counts = {}
        for opp_type in OpportunityType:
            count = session.query(Opportunity).filter(Opportunity.type == opp_type).count()
            type_counts[opp_type.value] = count

        state_counts = {}
        for s in sources:
            st = s.state or "CENTRAL"
            state_counts[st] = state_counts.get(st, 0) + session.query(Opportunity).filter(Opportunity.source_id == s.id).count()

        healthy_sources_count = session.query(OpportunitySource).filter(OpportunitySource.health_status == "HEALTHY").count()
        degraded_sources_count = session.query(OpportunitySource).filter(OpportunitySource.health_status == "DEGRADED").count()
        blocked_sources_count = session.query(OpportunitySource).filter(OpportunitySource.health_status == "BLOCKED").count()
        failed_sources_count = session.query(OpportunitySource).filter(OpportunitySource.health_status.in_(["FAILED", "STALE"])).count()

        total_opps = session.query(Opportunity).count()
        published_opps = session.query(Opportunity).filter(Opportunity.status != "CLOSED").count()

        final_summary = {
            "registered_sources": len(sources),
            "healthy_sources": healthy_sources_count,
            "degraded_sources": degraded_sources_count,
            "blocked_sources": blocked_sources_count,
            "failed_sources": failed_sources_count,
            "opportunities_found": total_opps,
            "opportunities_published": published_opps,
            "coverage_by_type": type_counts,
            "coverage_by_state": state_counts,
            "coverage_by_source": report,
        }

        print(json.dumps(final_summary, indent=2))

        session.close()
        server.cleanup()


if __name__ == "__main__":
    run_live_source_verification()

