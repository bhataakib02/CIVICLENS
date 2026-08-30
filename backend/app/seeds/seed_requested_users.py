"""Seed requested user accounts for CivicLens.

Creates:
1. Admin: email=thefreelancer2076@gmail.com, password=Blackbird@12., role=scheme_admin
2. User:  email=aakibbhat01@gmail.com, password=Blackbird@12., role=citizen

Usage:
    python -m app.seeds.seed_requested_users
"""
from __future__ import annotations

from sqlalchemy import select
from app.core.security import hash_password
from app.db.session import get_sessionmaker
from app.models.citizen_profile import CitizenProfile
from app.models.enums import UserRole, UserStatus
from app.models.user import User


def seed_requested_users(session=None) -> dict:
    close_at_end = False
    if session is None:
        session = get_sessionmaker()()
        close_at_end = True

    try:
        print("Seeding requested user accounts...")

        # 1. Admin account
        admin_email = "thefreelancer2076@gmail.com"
        admin_pass = "Blackbird@12."

        user_admin = session.scalar(select(User).where(User.email == admin_email))
        if user_admin is None:
            user_admin = User(
                email=admin_email,
                password_hash=hash_password(admin_pass),
                role=UserRole.SCHEME_ADMIN,
                status=UserStatus.ACTIVE,
            )
            user_admin.profile = CitizenProfile(current_version_no=1)
            session.add(user_admin)
            print(f"  ✓ Created Admin: {admin_email}")
        else:
            user_admin.password_hash = hash_password(admin_pass)
            user_admin.role = UserRole.SCHEME_ADMIN
            user_admin.status = UserStatus.ACTIVE
            print(f"  ✓ Updated Admin: {admin_email}")

        # 2. Citizen User account
        citizen_email = "aakibbhat01@gmail.com"
        citizen_pass = "Blackbird@12."

        user_citizen = session.scalar(select(User).where(User.email == citizen_email))
        if user_citizen is None:
            user_citizen = User(
                email=citizen_email,
                password_hash=hash_password(citizen_pass),
                role=UserRole.CITIZEN,
                status=UserStatus.ACTIVE,
            )
            user_citizen.profile = CitizenProfile(current_version_no=1)
            session.add(user_citizen)
            print(f"  ✓ Created User: {citizen_email}")
        else:
            user_citizen.password_hash = hash_password(citizen_pass)
            user_citizen.role = UserRole.CITIZEN
            user_citizen.status = UserStatus.ACTIVE
            print(f"  ✓ Updated User: {citizen_email}")

        session.commit()
        print("\n=== User Accounts Created Successfully! ===")
        return {"users_seeded": 2}
    finally:
        if close_at_end:
            session.close()


seed = seed_requested_users


if __name__ == "__main__":
    seed_requested_users()
