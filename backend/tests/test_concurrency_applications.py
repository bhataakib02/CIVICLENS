"""Concurrency test: simultaneous submit produces exactly one submission
(prompt §50). Uses threads against the real DB, exercising the row lock +
partial-unique-index guard in the workflow."""
from __future__ import annotations

import threading
import uuid
from datetime import date

import pytest
from sqlalchemy import func, select

pytestmark = pytest.mark.integration

STRONG_PW = "CorrectHorse9Battery!"


def _register(client, email):
    return client.post("/api/v1/auth/register", json={"email": email, "password": STRONG_PW}).json()["access_token"]


def _h(t):
    return {"Authorization": f"Bearer {t}"}


def _ready_app(client, db_session_factory):
    from app.models.citizen_profile import CitizenProfile
    from app.models.document import Document
    from app.models.document_requirement import DocumentRequirement
    from app.models.eligibility import EligibilityRule
    from app.models.enums import DocumentStatus, DocumentType
    from app.models.scheme import Scheme, SchemeVersion
    from app.models.user import User

    with db_session_factory() as s:
        scheme = Scheme(canonical_name="Conc", category="employment", scope="central")
        s.add(scheme); s.flush()
        v = SchemeVersion(scheme_id=scheme.id, version_no=1, status="published",
                          benefits_summary="b", effective_from=date(2025, 1, 1))
        s.add(v); s.flush()
        s.add(EligibilityRule(scheme_version_id=v.id, rule_code="INCOME", field_key="declared_annual_income",
                              operator="lte", value=250000, mandatory=True, sort_order=0, explanation_text="x"))
        s.add(DocumentRequirement(scheme_version_id=v.id, document_type=DocumentType.INCOME_CERTIFICATE, is_mandatory=True))
        s.commit()
        version_id = str(v.id)

    token = _register(client, "conc@example.com")
    client.patch("/api/v1/me", headers=_h(token), json={"declared_annual_income": "100000"})
    with db_session_factory() as s:
        user = s.scalar(select(User).where(User.email == "conc@example.com"))
        profile = s.scalar(select(CitizenProfile).where(CitizenProfile.user_id == user.id))
        s.add(Document(citizen_profile_id=profile.id, document_type=DocumentType.INCOME_CERTIFICATE,
                       status=DocumentStatus.VERIFIED, storage_key=f"k/{uuid.uuid4()}"))
        s.commit()
    app_id = client.post("/api/v1/applications", headers=_h(token), json={"scheme_version_id": version_id}).json()["id"]
    return token, app_id


def test_concurrent_submit_exactly_one_submission(client, db_session_factory):
    token, app_id = _ready_app(client, db_session_factory)

    results: list[int] = []
    barrier = threading.Barrier(2)

    def _submit():
        barrier.wait()  # maximize overlap
        r = client.post(f"/api/v1/applications/{app_id}/submit", headers=_h(token))
        results.append(r.status_code)

    threads = [threading.Thread(target=_submit) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Exactly one success (200); the other is a conflict (409) — never two submissions.
    assert sorted(results) == [200, 409], results

    from app.models.application import Application, ApplicationSubmission

    with db_session_factory() as s:
        n_sub = s.scalar(select(func.count()).select_from(ApplicationSubmission).where(
            ApplicationSubmission.application_id == uuid.UUID(app_id)))
        app = s.get(Application, uuid.UUID(app_id))
    assert n_sub == 1
    assert app.status.value == "submitted"
