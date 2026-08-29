"""Integration tests: application workflow + case management against real
PostgreSQL (prompt §45-§53)."""
from __future__ import annotations

import uuid
from datetime import date

import pytest
from sqlalchemy import func, select

pytestmark = pytest.mark.integration

STRONG_PW = "CorrectHorse9Battery!"


# ------------------------------ helpers ------------------------------------- #
def _register(client, email):
    return client.post("/api/v1/auth/register", json={"email": email, "password": STRONG_PW}).json()["access_token"]


def _promote(db_session_factory, email, role):
    from app.models.enums import UserRole
    from app.models.user import User

    with db_session_factory() as s:
        u = s.scalar(select(User).where(User.email == email))
        u.role = UserRole(role)
        s.commit()


def _login(client, email):
    return client.post("/api/v1/auth/login", json={"email": email, "password": STRONG_PW}).json()["access_token"]


def _h(t):
    return {"Authorization": f"Bearer {t}"}


def _make_scheme_version(db_session_factory, *, income_limit=250000, requires_docs=("income_certificate",)):
    """Create a published scheme version with an income rule + doc requirements."""
    from app.models.document_requirement import DocumentRequirement
    from app.models.eligibility import EligibilityRule
    from app.models.enums import DocumentType
    from app.models.scheme import Scheme, SchemeVersion

    with db_session_factory() as s:
        scheme = Scheme(canonical_name="Emp Assist", category="employment", scope="central")
        s.add(scheme); s.flush()
        v = SchemeVersion(scheme_id=scheme.id, version_no=1, status="published",
                          benefits_summary="b", effective_from=date(2025, 1, 1))
        s.add(v); s.flush()
        s.add(EligibilityRule(
            scheme_version_id=v.id, rule_code="INCOME", field_key="declared_annual_income",
            operator="lte", value=income_limit, mandatory=True, sort_order=0,
            explanation_text="Income within limit.",
        ))
        for dt in requires_docs:
            s.add(DocumentRequirement(scheme_version_id=v.id, document_type=DocumentType(dt), is_mandatory=True))
        s.commit()
        return str(scheme.id), str(v.id)


def _set_income(client, token, income):
    client.patch("/api/v1/me", headers=_h(token), json={"declared_annual_income": str(income)})


def _add_verified_document(db_session_factory, token_email, dtype="income_certificate"):
    """Create a VERIFIED document for the citizen directly (pipeline covered elsewhere)."""
    from app.models.citizen_profile import CitizenProfile
    from app.models.document import Document
    from app.models.enums import DocumentStatus, DocumentType
    from app.models.user import User

    with db_session_factory() as s:
        user = s.scalar(select(User).where(User.email == token_email))
        profile = s.scalar(select(CitizenProfile).where(CitizenProfile.user_id == user.id))
        doc = Document(
            citizen_profile_id=profile.id, uploaded_by=user.id, document_type=DocumentType(dtype),
            status=DocumentStatus.VERIFIED, storage_key=f"k/{uuid.uuid4()}", filename="d.png",
            mime_type="image/png", size_bytes=100,
        )
        s.add(doc); s.commit()
        return str(doc.id)


# ------------------------------ create / list / get ------------------------- #
def test_create_application_eligible(client, db_session_factory):
    scheme_id, version_id = _make_scheme_version(db_session_factory)
    token = _register(client, "app1@example.com")
    _set_income(client, token, 100000)  # eligible
    r = client.post("/api/v1/applications", headers=_h(token), json={"scheme_version_id": version_id})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["application_number"].startswith("CL-")
    assert body["scheme_version_id"] == version_id
    assert body["status"] == "draft"


def test_create_application_not_eligible_409(client, db_session_factory):
    scheme_id, version_id = _make_scheme_version(db_session_factory)
    token = _register(client, "app2@example.com")
    _set_income(client, token, 900000)  # over the limit -> not_eligible
    r = client.post("/api/v1/applications", headers=_h(token), json={"scheme_version_id": version_id})
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "NOT_ELIGIBLE"


def test_list_own_applications_paginated(client, db_session_factory):
    scheme_id, version_id = _make_scheme_version(db_session_factory)
    token = _register(client, "app3@example.com")
    _set_income(client, token, 100000)
    for _ in range(3):
        client.post("/api/v1/applications", headers=_h(token), json={"scheme_version_id": version_id})
    page = client.get("/api/v1/applications?page=1&page_size=2", headers=_h(token)).json()
    assert len(page["items"]) == 2 and page["total"] == 3


def test_get_application_detail(client, db_session_factory):
    scheme_id, version_id = _make_scheme_version(db_session_factory)
    token = _register(client, "app4@example.com")
    _set_income(client, token, 100000)
    app_id = client.post("/api/v1/applications", headers=_h(token), json={"scheme_version_id": version_id}).json()["id"]
    detail = client.get(f"/api/v1/applications/{app_id}", headers=_h(token)).json()
    assert detail["eligibility"]["decision"] == "eligible"
    assert detail["eligibility"]["engine_version"] == "1.0.0"
    assert "checklist" in detail
    assert detail["review"] is None  # citizen view hides reviewer info


# ------------------------------ readiness ----------------------------------- #
def _create_app(client, token, version_id):
    return client.post("/api/v1/applications", headers=_h(token), json={"scheme_version_id": version_id}).json()["id"]


def test_readiness_missing_document(client, db_session_factory):
    _, version_id = _make_scheme_version(db_session_factory)
    token = _register(client, "rd1@example.com")
    _set_income(client, token, 100000)
    app_id = _create_app(client, token, version_id)
    cl = client.get(f"/api/v1/applications/{app_id}/checklist", headers=_h(token)).json()
    assert cl["all_required_satisfied"] is False
    assert any(i["document_type"] == "income_certificate" and i["status"] == "MISSING" for i in cl["items"])


def test_readiness_verified_document(client, db_session_factory):
    _, version_id = _make_scheme_version(db_session_factory)
    token = _register(client, "rd2@example.com")
    _set_income(client, token, 100000)
    _add_verified_document(db_session_factory, "rd2@example.com")
    app_id = _create_app(client, token, version_id)
    cl = client.get(f"/api/v1/applications/{app_id}/checklist", headers=_h(token)).json()
    assert cl["all_required_satisfied"] is True
    assert any(i["status"] == "VERIFIED" for i in cl["items"])


def test_readiness_processing_document_not_satisfied(client, db_session_factory):
    _, version_id = _make_scheme_version(db_session_factory)
    token = _register(client, "rd3@example.com")
    _set_income(client, token, 100000)
    # Add a PROCESSING document.
    from app.models.citizen_profile import CitizenProfile
    from app.models.document import Document
    from app.models.enums import DocumentStatus, DocumentType
    from app.models.user import User

    with db_session_factory() as s:
        user = s.scalar(select(User).where(User.email == "rd3@example.com"))
        profile = s.scalar(select(CitizenProfile).where(CitizenProfile.user_id == user.id))
        s.add(Document(citizen_profile_id=profile.id, document_type=DocumentType.INCOME_CERTIFICATE,
                       status=DocumentStatus.PROCESSING, storage_key=f"k/{uuid.uuid4()}"))
        s.commit()
    app_id = _create_app(client, token, version_id)
    cl = client.get(f"/api/v1/applications/{app_id}/checklist", headers=_h(token)).json()
    assert cl["all_required_satisfied"] is False
    assert any(i["status"] == "PROCESSING" for i in cl["items"])


def test_readiness_rejected_document_not_satisfied(client, db_session_factory):
    """A REJECTED document must not satisfy a requirement (prompt §12, §46)."""
    _, version_id = _make_scheme_version(db_session_factory)
    token = _register(client, "rd4@example.com")
    _set_income(client, token, 100000)
    from app.models.citizen_profile import CitizenProfile
    from app.models.document import Document
    from app.models.enums import DocumentStatus, DocumentType
    from app.models.user import User

    with db_session_factory() as s:
        user = s.scalar(select(User).where(User.email == "rd4@example.com"))
        profile = s.scalar(select(CitizenProfile).where(CitizenProfile.user_id == user.id))
        s.add(Document(citizen_profile_id=profile.id, document_type=DocumentType.INCOME_CERTIFICATE,
                       status=DocumentStatus.REJECTED, storage_key=f"k/{uuid.uuid4()}"))
        s.commit()
    app_id = _create_app(client, token, version_id)
    cl = client.get(f"/api/v1/applications/{app_id}/checklist", headers=_h(token)).json()
    assert cl["all_required_satisfied"] is False
    assert any(i["status"] == "REJECTED" for i in cl["items"])


def test_readiness_expired_document_not_satisfied(client, db_session_factory):
    """A previously-VERIFIED document whose extracted validity date has passed is
    EXPIRED and must not satisfy the requirement (prompt §34, §46)."""
    from datetime import date as _date

    _, version_id = _make_scheme_version(db_session_factory)
    token = _register(client, "rd5@example.com")
    _set_income(client, token, 100000)
    from app.models.citizen_profile import CitizenProfile
    from app.models.document import Document, DocumentExtractedField, DocumentExtraction
    from app.models.enums import (
        ConfidenceLevel,
        DocumentStatus,
        DocumentType,
        FieldValueType,
    )
    from app.models.user import User

    with db_session_factory() as s:
        user = s.scalar(select(User).where(User.email == "rd5@example.com"))
        profile = s.scalar(select(CitizenProfile).where(CitizenProfile.user_id == user.id))
        doc = Document(citizen_profile_id=profile.id, document_type=DocumentType.INCOME_CERTIFICATE,
                       status=DocumentStatus.VERIFIED, storage_key=f"k/{uuid.uuid4()}")
        s.add(doc); s.flush()
        extraction = DocumentExtraction(document_id=doc.id, extracted_fields={})
        s.add(extraction); s.flush()
        # A validity date in the past -> EXPIRED.
        s.add(DocumentExtractedField(
            extraction_id=extraction.id, document_id=doc.id, field_name="valid_until",
            value_type=FieldValueType.DATE, normalized_value=_date(2000, 1, 1).isoformat(),
            confidence=0.99, confidence_level=ConfidenceLevel.HIGH,
        ))
        s.commit()
    app_id = _create_app(client, token, version_id)
    cl = client.get(f"/api/v1/applications/{app_id}/checklist", headers=_h(token)).json()
    assert cl["all_required_satisfied"] is False
    assert any(i["status"] == "EXPIRED" for i in cl["items"])


# ------------------------------ submission ---------------------------------- #
def _ready_application(client, db_session_factory, email):
    _, version_id = _make_scheme_version(db_session_factory)
    token = _register(client, email)
    _set_income(client, token, 100000)
    _add_verified_document(db_session_factory, email)
    app_id = _create_app(client, token, version_id)
    return token, app_id


def test_submission_success(client, db_session_factory):
    token, app_id = _ready_application(client, db_session_factory, "sub1@example.com")
    r = client.post(f"/api/v1/applications/{app_id}/submit", headers=_h(token))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "submitted"
    assert body["submission"]["external_reference"].startswith("MOCK-CL-")
    assert body["submission"]["provider_environment"] in ("test", "development")

    from app.models.application import ApplicationSubmission

    with db_session_factory() as s:
        subs = s.scalars(select(ApplicationSubmission).where(ApplicationSubmission.application_id == uuid.UUID(app_id))).all()
        assert len(subs) == 1


def test_submission_missing_documents_422(client, db_session_factory):
    _, version_id = _make_scheme_version(db_session_factory)
    token = _register(client, "sub2@example.com")
    _set_income(client, token, 100000)  # eligible but no documents
    app_id = _create_app(client, token, version_id)
    r = client.post(f"/api/v1/applications/{app_id}/submit", headers=_h(token))
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "DOCUMENTS_INCOMPLETE"


def test_submission_duplicate_returns_conflict(client, db_session_factory):
    token, app_id = _ready_application(client, db_session_factory, "sub3@example.com")
    assert client.post(f"/api/v1/applications/{app_id}/submit", headers=_h(token)).status_code == 200
    r2 = client.post(f"/api/v1/applications/{app_id}/submit", headers=_h(token))
    assert r2.status_code == 409
    assert r2.json()["error"]["code"] == "APPLICATION_ALREADY_SUBMITTED"


def test_submission_idempotency_key(client, db_session_factory):
    token, app_id = _ready_application(client, db_session_factory, "sub4@example.com")
    headers = {**_h(token), "Idempotency-Key": "sub-key-1"}
    r1 = client.post(f"/api/v1/applications/{app_id}/submit", headers=headers)
    r2 = client.post(f"/api/v1/applications/{app_id}/submit", headers=headers)
    assert r1.status_code == 200 and r2.status_code == 200  # same logical submission
    from app.models.application import ApplicationSubmission

    with db_session_factory() as s:
        n = s.scalar(select(func.count()).select_from(ApplicationSubmission).where(
            ApplicationSubmission.application_id == uuid.UUID(app_id)))
        assert n == 1


def test_submission_provider_failure_rolls_back_to_failed(client, db_session_factory):
    token, app_id = _ready_application(client, db_session_factory, "sub5@example.com")
    r = client.post(f"/api/v1/applications/{app_id}/submit", headers=_h(token),
                    json={"simulate_provider_failure": True})
    assert r.status_code == 502
    assert r.json()["error"]["code"] == "SUBMISSION_FAILED"
    # Application is SUBMISSION_FAILED, and no live submission exists.
    detail = client.get(f"/api/v1/applications/{app_id}", headers=_h(token)).json()
    assert detail["status"] == "submission_failed"
    assert detail["submission"] is None
    # A retry can now succeed.
    r2 = client.post(f"/api/v1/applications/{app_id}/submit", headers=_h(token))
    assert r2.status_code == 200 and r2.json()["status"] == "submitted"


def test_notification_emitted_on_submission(client, db_session_factory):
    token, app_id = _ready_application(client, db_session_factory, "sub6@example.com")
    client.post(f"/api/v1/applications/{app_id}/submit", headers=_h(token))
    # Event-driven (Phase 6): the submit enqueues an outbox event; the worker
    # turns it into an in-app notification. Drain the outbox, then read the feed.
    from app.modules.notifications.service import OutboxDispatcher

    with db_session_factory() as s:
        OutboxDispatcher(session=s).dispatch_pending()
    page = client.get("/api/v1/notifications", headers=_h(token)).json()
    assert any(n["category"] == "status_change" for n in page["items"])


# ------------------------------ review / assign / action -------------------- #
def _submitted_app_with_reviewer(client, db_session_factory, email, admin_email, cw_email):
    token, app_id = _ready_application(client, db_session_factory, email)
    client.post(f"/api/v1/applications/{app_id}/submit", headers=_h(token))
    # admin + case worker
    _register(client, admin_email); _promote(db_session_factory, admin_email, "admin")
    admin = _login(client, admin_email)
    _register(client, cw_email); _promote(db_session_factory, cw_email, "agent")
    from app.models.user import User

    with db_session_factory() as s:
        cw_id = str(s.scalar(select(User.id).where(User.email == cw_email)))
    # assign the case worker
    client.post(f"/api/v1/applications/{app_id}/assign", headers=_h(admin), json={"case_worker_id": cw_id})
    return token, app_id, admin, _login(client, cw_email)


def test_review_approve_flow(client, db_session_factory):
    token, app_id, admin, cw = _submitted_app_with_reviewer(
        client, db_session_factory, "rv1@example.com", "adm1@example.com", "cw1@example.com")
    r = client.post(f"/api/v1/applications/{app_id}/review", headers=_h(cw),
                    json={"action": "approve", "reason": "Meets criteria."})
    assert r.status_code == 200 and r.json()["status"] == "approved"
    comp = client.post(f"/api/v1/applications/{app_id}/complete", headers=_h(cw))
    assert comp.status_code == 200 and comp.json()["status"] == "completed"


def test_review_request_action_then_resolve(client, db_session_factory):
    token, app_id, admin, cw = _submitted_app_with_reviewer(
        client, db_session_factory, "rv2@example.com", "adm2@example.com", "cw2@example.com")
    r = client.post(f"/api/v1/applications/{app_id}/review", headers=_h(cw),
                    json={"action": "request_action", "reason": "Need updated income proof.",
                          "required_items": ["income_certificate"]})
    assert r.status_code == 200 and r.json()["status"] == "action_required"
    # Citizen resolves.
    res = client.post(f"/api/v1/applications/{app_id}/resolve-action", headers=_h(token), json={"note": "Updated."})
    assert res.status_code == 200 and res.json()["status"] == "under_review"


def test_review_reject_requires_reason(client, db_session_factory):
    token, app_id, admin, cw = _submitted_app_with_reviewer(
        client, db_session_factory, "rv3@example.com", "adm3@example.com", "cw3@example.com")
    r = client.post(f"/api/v1/applications/{app_id}/review", headers=_h(cw),
                    json={"action": "reject", "reason": ""})
    assert r.status_code == 422  # empty reason rejected


def test_reassign_case_worker(client, db_session_factory):
    token, app_id, admin, cw = _submitted_app_with_reviewer(
        client, db_session_factory, "rv4@example.com", "adm4@example.com", "cw4@example.com")
    _register(client, "cw4b@example.com"); _promote(db_session_factory, "cw4b@example.com", "agent")
    from app.models.user import User

    with db_session_factory() as s:
        cw2_id = str(s.scalar(select(User.id).where(User.email == "cw4b@example.com")))
    r = client.post(f"/api/v1/applications/{app_id}/assign", headers=_h(admin), json={"case_worker_id": cw2_id})
    assert r.status_code == 200
    from app.models.application import ApplicationAssignment

    with db_session_factory() as s:
        actions = [a.action.value for a in s.scalars(
            select(ApplicationAssignment).where(ApplicationAssignment.application_id == uuid.UUID(app_id)))]
    assert "reassign" in actions


# ------------------------------ withdraw ------------------------------------ #
def test_withdraw_draft(client, db_session_factory):
    _, version_id = _make_scheme_version(db_session_factory)
    token = _register(client, "wd1@example.com")
    _set_income(client, token, 100000)
    app_id = _create_app(client, token, version_id)
    r = client.post(f"/api/v1/applications/{app_id}/withdraw", headers=_h(token), json={"reason": "changed mind"})
    assert r.status_code == 200 and r.json()["status"] == "withdrawn"


# ------------------------------ historical consistency (MANDATORY) ---------- #
def test_historical_consistency_scheme_version_immutable(client, db_session_factory):
    """Create app under version 1; publish version 2; the app still references
    version 1 and its eligibility snapshot is unchanged (prompt §52)."""
    scheme_id, v1_id = _make_scheme_version(db_session_factory, income_limit=250000)
    token = _register(client, "hist@example.com")
    _set_income(client, token, 100000)
    app_id = client.post("/api/v1/applications", headers=_h(token), json={"scheme_version_id": v1_id}).json()["id"]
    before = client.get(f"/api/v1/applications/{app_id}", headers=_h(token)).json()
    snap_before = before["eligibility"]

    # Publish a NEW version 2 for the same scheme with a stricter rule.
    # (Close v1's open-ended effective range first, respecting the single
    # open-published-version invariant from Phase 2.)
    from app.models.eligibility import EligibilityRule
    from app.models.scheme import SchemeVersion

    with db_session_factory() as s:
        # Close v1's open-ended range and COMMIT before inserting v2, so the
        # partial unique index (status='published' AND effective_to IS NULL)
        # deterministically no longer sees v1 as the open version regardless
        # of unit-of-work flush ordering.
        v1 = s.get(SchemeVersion, uuid.UUID(v1_id))
        v1.effective_to = date(2025, 12, 31)
        s.commit()
    with db_session_factory() as s:
        v2 = SchemeVersion(scheme_id=uuid.UUID(scheme_id), version_no=2, status="published",
                           benefits_summary="v2", effective_from=date(2026, 1, 1))
        s.add(v2); s.flush()
        s.add(EligibilityRule(scheme_version_id=v2.id, rule_code="INCOME", field_key="declared_annual_income",
                              operator="lte", value=50000, mandatory=True, sort_order=0,
                              explanation_text="Stricter income."))
        s.commit()

    after = client.get(f"/api/v1/applications/{app_id}", headers=_h(token)).json()
    assert after["scheme_version_id"] == v1_id  # still v1
    assert after["eligibility"] == snap_before  # snapshot unchanged
    assert after["eligibility"]["scheme_version_id"] == v1_id


def test_seed_applications_runs(client, db_session_factory):
    from app.seeds.seed_applications import seed

    with db_session_factory() as s:
        summary = seed(s)
    assert len(summary["application_ids"]) == 5
