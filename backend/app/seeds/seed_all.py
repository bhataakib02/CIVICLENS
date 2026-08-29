"""Master seed runner for CivicLens.

Usage:
    python -m app.seeds.seed_all
"""
from __future__ import annotations

from app.db.session import get_sessionmaker
from app.seeds.seed_demo import seed as seed_demo
from app.seeds.seed_documents import seed as seed_documents
from app.seeds.seed_applications import seed as seed_applications
from app.seeds.seed_knowledge import seed as seed_knowledge


def seed_all() -> None:
    session = get_sessionmaker()()
    try:
        print("1/4 Seeding Demo Schemes & Users...")
        res_demo = seed_demo(session)
        print(f"  -> {res_demo}")

        print("2/4 Seeding Demo Documents...")
        res_docs = seed_documents(session)
        print(f"  -> {res_docs}")

        print("3/4 Seeding Demo Applications...")
        res_apps = seed_applications(session)
        print(f"  -> {res_apps}")

        print("4/4 Seeding Demo Knowledge Base...")
        res_know = seed_knowledge(session)
        print(f"  -> {res_know}")

        print("5/5 Seeding Opportunity Discovery Engine Sources & Listings...")
        from app.seeds.seed_opportunities import seed as seed_opportunities
        res_opp = seed_opportunities(session)
        print(f"  -> {res_opp}")

        print("\n=== All Demo Data & Opportunity Engine Seeded Successfully! ===")
    finally:
        session.close()


if __name__ == "__main__":
    seed_all()
