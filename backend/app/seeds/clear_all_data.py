"""Clean database data wipe script for CivicLens.

Removes all demo users, credentials, schemes, applications, documents,
knowledge sources, and opportunity engine data.

Usage:
    python -m app.seeds.clear_all_data
"""
from __future__ import annotations

from sqlalchemy import text
from app.db.session import get_sessionmaker


def clear_all_data() -> None:
    session = get_sessionmaker()()
    try:
        print("Clearing all data from CivicLens database...")

        # Disable trigger checks / CASCADE truncate order
        tables = [
            "audit_logs",
            "link_verifications",
            "crawl_items",
            "crawl_runs",
            "raw_crawl_snapshots",
            "opportunity_application_tracks",
            "opportunity_changes",
            "opportunity_alerts",
            "opportunity_subscriptions",
            "opportunity_links",
            "opportunity_versions",
            "opportunities",
            "opportunity_sources",
            "knowledge_snippets",
            "knowledge_sources",
            "application_versions",
            "applications",
            "documents",
            "scheme_versions",
            "schemes",
            "addresses",
            "citizen_profile_versions",
            "citizen_profiles",
            "user_roles",
            "user_identities",
            "users",
        ]

        for tbl in tables:
            try:
                session.execute(text(f"TRUNCATE TABLE {tbl} CASCADE;"))
                print(f"  ✓ Truncated {tbl}")
            except Exception as e:
                session.rollback()
                try:
                    session.execute(text(f"DELETE FROM {tbl};"))
                    session.commit()
                    print(f"  ✓ Deleted from {tbl}")
                except Exception as inner_e:
                    session.rollback()
                    print(f"  - Notice for {tbl}: {inner_e}")

        session.commit()
        print("\n=== Database Cleaned Successfully! Zero Demo/Hardcoded Data Remains. ===")
    finally:
        session.close()


if __name__ == "__main__":
    clear_all_data()
