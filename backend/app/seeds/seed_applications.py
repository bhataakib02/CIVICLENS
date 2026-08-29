"""Development seed for the application workflow (prompt §56).

Creates clearly FICTIONAL development data: schemes + versions +
document_requirements, several citizens, and applications in various statuses
(draft, submitted, under_review, approved), plus a case-worker assignment.
Reuses the Prompt-2/3 demo schemes when present. NOT real citizen data.

Usage: python -m app.seeds.seed_applications
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import get_sessionmaker
from app.models.application import Application, ApplicationStatusHistory
from app.models.citizen_profile import CitizenProfile
from app.models.document_requirement import DocumentRequirement
from app.models.enums import (
    ApplicationStatus,
    DocumentType,
    SchemeScope,
    SchemeVersionStatus,
    UserRole,
    UserStatus,
)
from app.models.scheme import Scheme, SchemeVersion
from app.models.user import User
from app.modules.applications.submission import generate_application_number

PW = "CivicDemoPass123!"


def _user(session: Session, email: str, role: UserRole = UserRole.CITIZEN) -> User:
    u = session.scalar(select(User).where(User.email == email))
    if u is None:
        u = User(email=email, password_hash=hash_password(PW), role=role, status=UserStatus.ACTIVE)
        if role is UserRole.CITIZEN:
            u.profile = CitizenProfile(current_version_no=1, declared_annual_income=120000)
        session.add(u)
        session.flush()
    return u


def _scheme_with_version(session: Session, *, code: str, name: str, category: str) -> SchemeVersion:
    scheme = session.scalar(select(Scheme).where(Scheme.code == code))
    if scheme is None:
        scheme = Scheme(canonical_name=name, code=code, category=category, scope=SchemeScope.STATE)
        session.add(scheme)
        session.flush()
    version = session.scalars(
        select(SchemeVersion).where(SchemeVersion.scheme_id == scheme.id)
    ).first()
    if version is None:
        version = SchemeVersion(
            scheme_id=scheme.id, version_no=1, status=SchemeVersionStatus.PUBLISHED,
            benefits_summary=f"[DEVELOPMENT DATA] {name}", effective_from=date(2025, 1, 1),
        )
        session.add(version)
        session.flush()
    # Document requirements (from scheme config).
    if not session.scalars(
        select(DocumentRequirement).where(DocumentRequirement.scheme_version_id == version.id)
    ).first():
        session.add_all([
            DocumentRequirement(scheme_version_id=version.id, document_type=DocumentType.INCOME_CERTIFICATE, is_mandatory=True),
            DocumentRequirement(scheme_version_id=version.id, document_type=DocumentType.RESIDENCE_PROOF, is_mandatory=True),
        ])
        session.flush()
    return version


def _application(session: Session, *, profile_id, version_id, status: ApplicationStatus) -> Application:
    app = Application(
        application_number=generate_application_number(),
        citizen_profile_id=profile_id, scheme_version_id=version_id,
        status=status,
        eligibility_snapshot={"decision": "eligible", "engine_version": "1.0.0",
                              "scheme_version_id": str(version_id),
                              "evaluated_at": datetime.now(timezone.utc).isoformat()},
        submitted_at=datetime.now(timezone.utc) if status in (
            ApplicationStatus.SUBMITTED, ApplicationStatus.UNDER_REVIEW, ApplicationStatus.APPROVED) else None,
    )
    session.add(app)
    session.flush()
    session.add(ApplicationStatusHistory(
        application_id=app.id, from_status=None, to_status=status.value,
        note="[DEVELOPMENT DATA] seeded status.",
    ))
    session.flush()
    return app


def seed(session: Session) -> dict:
    v1 = _scheme_with_version(session, code="CIVIC-APP-001", name="Demo Employment Assistance", category="employment")
    v2 = _scheme_with_version(session, code="CIVIC-APP-002", name="Demo Housing Support", category="housing")
    v3 = _scheme_with_version(session, code="CIVIC-APP-003", name="Demo Student Grant", category="education")

    case_worker = _user(session, "demo.caseworker@example.com", UserRole.AGENT)
    citizens = [_user(session, f"demo.applicant{i}@example.com") for i in range(1, 6)]

    statuses = [
        ApplicationStatus.DRAFT, ApplicationStatus.SUBMITTED, ApplicationStatus.UNDER_REVIEW,
        ApplicationStatus.APPROVED, ApplicationStatus.DRAFT,
    ]
    app_ids = []
    for citizen, status in zip(citizens, statuses):
        app = _application(session, profile_id=citizen.profile.id, version_id=v1.id, status=status)
        if status in (ApplicationStatus.UNDER_REVIEW, ApplicationStatus.APPROVED):
            app.assigned_case_worker_id = case_worker.id
        app_ids.append(str(app.id))
    session.flush()
    session.commit()
    return {
        "scheme_version_ids": [str(v1.id), str(v2.id), str(v3.id)],
        "case_worker_email": "demo.caseworker@example.com",
        "application_ids": app_ids,
    }


def main() -> None:
    session = get_sessionmaker()()
    try:
        print("Seeded applications:", seed(session))
    finally:
        session.close()


if __name__ == "__main__":
    main()
