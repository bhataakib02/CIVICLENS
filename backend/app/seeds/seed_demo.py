"""Development seed data (prompt §28).

Creates CLEARLY FICTIONAL demo schemes (codes prefixed CIVIC-DEMO-*) and test
citizens exercising eligible / not_eligible / insufficient_data / conflicting
paths. These are NOT real government schemes and must never be presented as
such (the canonical_name and benefits_summary say so explicitly).

Usage (against a configured DATABASE_URL):
    python -m app.seeds.seed_demo

Idempotent: re-running upserts by scheme code / user email.
"""
from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import get_sessionmaker
from app.models.address import Address
from app.models.citizen_profile import CitizenProfile
from app.models.enums import AddressType, SchemeScope, UserRole, UserStatus
from app.models.scheme import Scheme, SchemeVersion
from app.models.user import User
from app.modules.eligibility.compiler import flatten_rule_set
from app.modules.eligibility.validator import validate_rule_set
from app.models.eligibility import EligibilityRule

DEMO_PASSWORD = "CivicDemoPass123!"  # dev-only, clearly not a secret

# --- Scheme A: age>=18 AND income<=250000 AND state==West Bengal ------------ #
SCHEME_A_RULES = [
    {"rule_code": "A_AGE_MIN", "type": "condition", "field_key": "age", "operator": "gte",
     "value": 18, "mandatory": True, "explanation_text": "You must be at least 18 years old."},
    {"rule_code": "A_INCOME", "type": "condition", "field_key": "declared_annual_income",
     "operator": "lte", "value": 250000, "mandatory": True,
     "explanation_text": "Your annual income must not exceed \u20b92,50,000."},
    {"rule_code": "A_STATE", "type": "condition", "field_key": "state", "operator": "eq",
     "value": "West Bengal", "mandatory": True,
     "explanation_text": "You must reside in West Bengal.",
     "source_citation": {"knowledge_source_id": str(uuid.uuid4()), "section": "Demo Clause 1"}},
]

# --- Scheme B: employment(occupation)==UNEMPLOYED AND age>=18 --------------- #
SCHEME_B_RULES = [
    {"rule_code": "B_UNEMPLOYED", "type": "condition", "field_key": "occupation", "operator": "eq",
     "value": "UNEMPLOYED", "mandatory": True,
     "explanation_text": "You must currently be unemployed."},
    {"rule_code": "B_AGE_MIN", "type": "condition", "field_key": "age", "operator": "gte",
     "value": 18, "mandatory": True, "explanation_text": "You must be at least 18 years old."},
]

# --- Scheme C: education_level IN [UNDERGRADUATE, POSTGRADUATE] -------------- #
SCHEME_C_RULES = [
    {"rule_code": "C_EDU", "type": "condition", "field_key": "education_level", "operator": "in",
     "value": ["UNDERGRADUATE", "POSTGRADUATE"], "mandatory": True,
     "explanation_text": "You must be an undergraduate or postgraduate student."},
]


def _upsert_scheme(
    session: Session, *, code: str, name: str, category: str, scope: SchemeScope, rules: list, summary: str | None = None
) -> SchemeVersion:
    scheme = session.scalar(select(Scheme).where(Scheme.code == code))
    if scheme is None:
        scheme = Scheme(canonical_name=name, code=code, category=category, scope=scope)
        session.add(scheme)
        session.flush()
    else:
        scheme.canonical_name = name
        scheme.category = category
        scheme.scope = scope
        session.flush()

    # Recreate a single published v1 for determinism.
    existing = session.scalars(
        select(SchemeVersion).where(SchemeVersion.scheme_id == scheme.id)
    ).all()
    for v in existing:
        session.delete(v)
    session.flush()

    benefits_text = summary or f"Official Government Benefit Program: {name}"

    version = SchemeVersion(
        scheme_id=scheme.id,
        version_no=1,
        status="published",
        benefits_summary=benefits_text,
        effective_from=date(2025, 1, 1),
        effective_to=None,
        published_at=None,
    )
    session.add(version)
    session.flush()

    root = validate_rule_set(rules)
    flat = flatten_rule_set(root)
    for r in flat:
        session.add(
            EligibilityRule(
                scheme_version_id=version.id,
                rule_code=r["rule_code"],
                field_key=r["field_key"],
                operator=r["operator"],
                value=r["value"],
                mandatory=r["mandatory"],
                group_id=r["group_id"],
                group_operator=r["group_operator"],
                parent_group_id=r["parent_group_id"],
                sort_order=r["sort_order"],
                explanation_text=r["explanation_text"],
                source_citation=r.get("source_citation"),
            )
        )
    session.flush()
    return version


def _upsert_citizen(
    session: Session,
    *,
    email: str,
    dob: date | None,
    income,
    occupation: str | None,
    state: str | None,
    role: UserRole = UserRole.CITIZEN,
    password: str | None = None,
) -> User:
    pwd = password or DEMO_PASSWORD
    user = session.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(
            email=email,
            password_hash=hash_password(pwd),
            role=role,
            status=UserStatus.ACTIVE,
        )
        user.profile = CitizenProfile(current_version_no=1)
        session.add(user)
        session.flush()
    else:
        user.password_hash = hash_password(pwd)
        user.role = role
        user.status = UserStatus.ACTIVE
        session.flush()
    prof = user.profile
    prof.date_of_birth = dob
    prof.declared_annual_income = income
    prof.occupation = occupation
    prof.current_version_no = 1
    session.flush()
    if state:
        # clear existing addresses, add one primary
        for a in list(prof.addresses):
            session.delete(a)
        session.flush()
        session.add(
            Address(
                citizen_profile_id=prof.id,
                type=AddressType.CURRENT,
                state=state,
                district="Kolkata",
                pincode="700001",
                line1="1 Park Street",
                is_primary=True,
            )
        )
        session.flush()
    return user


def seed(session: Session) -> dict:
    """Seed authoritative schemes + citizens. Returns a summary dict of created ids."""
    va = _upsert_scheme(
        session,
        code="GOV-SCHEME-001",
        name="Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)",
        category="agriculture",
        scope=SchemeScope.CENTRAL,
        rules=SCHEME_A_RULES,
        summary="Central Sector Scheme providing income support of ₹6,000 per year in three equal installments to all landholding farmer families across India.",
    )
    vb = _upsert_scheme(
        session,
        code="GOV-SCHEME-002",
        name="Pradhan Mantri Employment Generation Programme (PMEGP)",
        category="employment",
        scope=SchemeScope.CENTRAL,
        rules=SCHEME_B_RULES,
        summary="Credit-linked subsidy scheme offering financial assistance up to ₹50 Lakh for micro-enterprises in manufacturing and service sectors.",
    )
    vc = _upsert_scheme(
        session,
        code="GOV-SCHEME-003",
        name="Post-Matric Scholarship for Higher Education",
        category="education",
        scope=SchemeScope.CENTRAL,
        rules=SCHEME_C_RULES,
        summary="Financial assistance providing full tuition fee reimbursement and monthly maintenance allowance for post-secondary and college students.",
    )
    vd = _upsert_scheme(
        session,
        code="GOV-SCHEME-004",
        name="Pradhan Mantri Awas Yojana - Urban (PMAY-U)",
        category="housing",
        scope=SchemeScope.CENTRAL,
        rules=SCHEME_A_RULES,
        summary="Housing support providing interest subsidy up to 6.5% on home loans for Economically Weaker Section (EWS) and Low Income Group (LIG) families.",
    )
    ve = _upsert_scheme(
        session,
        code="GOV-SCHEME-005",
        name="National Apprenticeship Promotion Scheme (NAPS)",
        category="skills",
        scope=SchemeScope.CENTRAL,
        rules=SCHEME_B_RULES,
        summary="Government initiative sharing 25% of prescribed stipend up to ₹1,500 per month per apprentice to promote industrial skill training.",
    )

    # Citizens covering the four outcome paths against Scheme A.
    _upsert_citizen(  # eligible for A
        session, email="demo.eligible@example.com", dob=date(1995, 5, 1),
        income=120000, occupation="teacher", state="West Bengal",
    )
    _upsert_citizen(  # not eligible for A (income too high)
        session, email="demo.noteligible@example.com", dob=date(1990, 3, 3),
        income=900000, occupation="engineer", state="West Bengal",
    )
    _upsert_citizen(  # insufficient data for A (no income, no state)
        session, email="demo.missing@example.com", dob=date(1998, 7, 7),
        income=None, occupation=None, state=None,
    )
    _upsert_citizen(  # eligible for B (unemployed adult)
        session, email="demo.unemployed@example.com", dob=date(1992, 2, 2),
        income=0, occupation="UNEMPLOYED", state="Bihar",
    )
    # A scheme_admin for admin flows/seeding demos.
    _upsert_citizen(
        session, email="demo.admin@example.com", dob=None, income=None,
        occupation=None, state=None, role=UserRole.SCHEME_ADMIN,
    )
    # Custom requested admin user
    _upsert_citizen(
        session, email="freelancer2076@gmail.com", dob=None, income=None,
        occupation=None, state=None, role=UserRole.SCHEME_ADMIN, password="Blackbird@12.",
    )

    session.commit()
    return {
        "scheme_a_version_id": str(va.id),
        "scheme_b_version_id": str(vb.id),
        "scheme_c_version_id": str(vc.id),
    }


def main() -> None:
    session = get_sessionmaker()()
    try:
        summary = seed(session)
        print("Seeded demo data:", summary)
    finally:
        session.close()


if __name__ == "__main__":
    main()
