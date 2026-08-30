"""Master seed runner for CivicLens (Real Production Data Only).

Usage:
    python -m app.seeds.seed_all
"""
from __future__ import annotations

from app.db.session import get_sessionmaker
from app.seeds.seed_requested_users import seed as seed_requested_users
from app.seeds.seed_knowledge import seed as seed_knowledge
from app.seeds.seed_opportunities import seed as seed_opportunities


def seed_all() -> None:
    session = get_sessionmaker()()
    try:
        print("1/3 Seeding Real User Accounts...")
        res_users = seed_requested_users(session)
        print(f"  -> {res_users}")

        print("2/3 Seeding Production Knowledge Base...")
        res_know = seed_knowledge(session)
        print(f"  -> {res_know}")

        print("3/3 Seeding Real Opportunity Discovery Engine Sources...")
        res_opp = seed_opportunities(session)
        print(f"  -> {res_opp}")

        session.commit()
        print("\n=== Real Production Seeds Applied Successfully (No Dummy Data)! ===")
    except Exception as e:
        session.rollback()
        print(f"Seeding failed: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed_all()
