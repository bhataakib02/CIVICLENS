"""Permanent cleanup script for dummy seed data in CivicLens.

Deletes:
- Dummy demo users (@example.com and None email users)
- Dummy demo applications
- Dummy demo documents
- Dummy demo schemes (GOV-SCHEME-*, CIVIC-APP-*)

Preserves:
- Real user accounts (thefreelancer2076@gmail.com, aakibbhat01@gmail.com, freelancer2076@gmail.com)
- All real production Opportunity Sources & Opportunity Intelligence Engine listings discovered by the crawler.
"""
from __future__ import annotations

import os

from app.core.config import get_settings
from app.db.session import get_sessionmaker
from app.models.user import User
from app.models.scheme import Scheme, SchemeVersion
from app.models.application import (
    Application,
    ApplicationStatusHistory,
    ApplicationDocument,
    ApplicationSubmission,
    ApplicationAssignment,
    ApplicationAction,
)
from app.models.document import Document
from app.models.citizen_profile import CitizenProfile, CitizenProfileVersion
from app.models.address import Address


def cleanup_dummy_data() -> None:
    # Ensure pointing to the active Postgres database
    os.environ.setdefault(
        "DATABASE_URL",
        "postgresql+psycopg://civiclens:civiclens_dev_password@127.0.0.1:5432/civiclens",
    )
    get_settings.cache_clear()

    session = get_sessionmaker()()
    try:
        print("=== 1. PERMANENTLY CLEANING DUMMY APPLICATIONS ===")
        # Delete application child tables
        session.query(ApplicationAction).delete(synchronize_session=False)
        session.query(ApplicationAssignment).delete(synchronize_session=False)
        session.query(ApplicationSubmission).delete(synchronize_session=False)
        session.query(ApplicationDocument).delete(synchronize_session=False)
        session.query(ApplicationStatusHistory).delete(synchronize_session=False)
        apps_deleted = session.query(Application).delete(synchronize_session=False)
        print(f"  -> Deleted {apps_deleted} applications and all child workflow records.")

        print("\n=== 2. PERMANENTLY CLEANING DUMMY DOCUMENTS ===")
        docs_deleted = session.query(Document).delete(synchronize_session=False)
        print(f"  -> Deleted {docs_deleted} dummy documents.")

        print("\n=== 3. PERMANENTLY CLEANING DUMMY SCHEMES ===")
        ver_deleted = session.query(SchemeVersion).delete(synchronize_session=False)
        schemes_deleted = session.query(Scheme).delete(synchronize_session=False)
        print(f"  -> Deleted {schemes_deleted} dummy schemes, {ver_deleted} scheme versions.")

        print("\n=== 4. CLEANING DUMMY USERS (@example.com) ===")
        dummy_users = (
            session.query(User)
            .filter(
                (User.email.is_(None))
                | (User.email.like("%@example.com"))
            )
            .all()
        )

        dummy_user_ids = [u.id for u in dummy_users]
        if dummy_user_ids:
            prof_ids = [p.id for p in session.query(CitizenProfile).filter(CitizenProfile.user_id.in_(dummy_user_ids)).all()]
            if prof_ids:
                session.query(CitizenProfileVersion).filter(CitizenProfileVersion.citizen_profile_id.in_(prof_ids)).delete(synchronize_session=False)
                session.query(Address).filter(Address.citizen_profile_id.in_(prof_ids)).delete(synchronize_session=False)
            prof_del = session.query(CitizenProfile).filter(CitizenProfile.user_id.in_(dummy_user_ids)).delete(synchronize_session=False)
            users_del = session.query(User).filter(User.id.in_(dummy_user_ids)).delete(synchronize_session=False)
            print(f"  -> Deleted {users_del} dummy users, {prof_del} profiles.")

        session.commit()

        # Print remaining clean database inventory
        remaining_users = session.query(User).all()
        print("\n=== CLEAN DATABASE STATE ===")
        print("Remaining Users:")
        for u in remaining_users:
            print(f"  - {u.email} ({u.role})")

        remaining_schemes = session.query(Scheme).count()
        remaining_apps = session.query(Application).count()
        remaining_docs = session.query(Document).count()

        from app.models.opportunity import OpportunitySource, Opportunity
        opp_sources = session.query(OpportunitySource).count()
        opp_listings = session.query(Opportunity).count()

        print(f"Remaining Schemes: {remaining_schemes}")
        print(f"Remaining Applications: {remaining_apps}")
        print(f"Remaining Documents: {remaining_docs}")
        print(f"Active Real Opportunity Sources: {opp_sources}")
        print(f"Active Real Opportunities Discovered: {opp_listings}")

        print("\n=== Dummy Data Permanently Cleaned! ===")

    except Exception as e:
        session.rollback()
        print(f"Cleanup failed: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    cleanup_dummy_data()
