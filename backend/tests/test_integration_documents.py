"""Integration tests: document upload/processing/verification/conflict/download/
delete against real PostgreSQL + local storage (prompt §43)."""
from __future__ import annotations

import pytest
from sqlalchemy import select

from tests.doc_helpers import INCOME_OCR_TEXT, income_png, jpeg_bytes, pdf_bytes, png_bytes

pytestmark = pytest.mark.integration

STRONG_PW = "CorrectHorse9Battery!"


def _register(client, email):
    return client.post("/api/v1/auth/register", json={"email": email, "password": STRONG_PW}).json()["access_token"]


def _h(t):
    return {"Authorization": f"Bearer {t}"}


def _upload(client, token, data: bytes, *, mime="image/png", dtype="income_certificate", filename="doc.png"):
    """Full secure flow: init -> PUT to signed URL -> complete. Returns document json."""
    init = client.post(
        "/api/v1/documents/upload-init",
        headers=_h(token),
        json={"document_type": dtype, "filename": filename, "mime_type": mime, "size_bytes": len(data)},
    )
    assert init.status_code == 200, init.text
    body = init.json()
    put = client.put(body["upload_url"], content=data)
    assert put.status_code == 204, put.text
    comp = client.post(f"/api/v1/documents/{body['document_id']}/complete", headers=_h(token))
    assert comp.status_code == 202, comp.text
    return body["document_id"], comp.json()


# ------------------------------ upload -------------------------------------- #
def test_upload_flow_png_processes_and_extracts(client, db_session_factory):
    token = _register(client, "doc1@example.com")
    doc_id, _ = _upload(client, token, income_png())
    # Processing ran synchronously via BackgroundTasks in TestClient.
    detail = client.get(f"/api/v1/documents/{doc_id}", headers=_h(token)).json()
    assert detail["status"] in ("verified", "verification_required")
    assert detail["classified_type"] == "income_certificate"
    income = next((f for f in detail["fields"] if f["field_name"] == "annual_income"), None)
    assert income is not None
    assert income["normalized_value"] == "200000"
    assert income["page_number"] == 1
    assert 0.0 <= income["confidence"] <= 1.0
    # storage_key must NOT be exposed anywhere in the response.
    assert "storage_key" not in detail

    from app.models.document import DocumentExtractedField

    with db_session_factory() as s:
        rows = s.scalars(select(DocumentExtractedField)).all()
        assert any(f.field_name == "annual_income" and f.normalized_value == "200000" for f in rows)


def test_upload_pdf_and_jpeg(client, db_session_factory):
    token = _register(client, "doc2@example.com")
    doc_pdf, _ = _upload(client, token, pdf_bytes(), mime="application/pdf", filename="d.pdf", dtype="income_certificate")
    assert client.get(f"/api/v1/documents/{doc_pdf}", headers=_h(token)).status_code == 200
    doc_jpg, _ = _upload(client, token, jpeg_bytes(), mime="image/jpeg", filename="d.jpg", dtype="identity_document")
    assert client.get(f"/api/v1/documents/{doc_jpg}", headers=_h(token)).status_code == 200


def test_upload_init_unsupported_type_rejected(client, db_session_factory):
    token = _register(client, "doc3@example.com")
    r = client.post(
        "/api/v1/documents/upload-init",
        headers=_h(token),
        json={"document_type": "income_certificate", "filename": "x.gif", "mime_type": "image/gif", "size_bytes": 100},
    )
    assert r.status_code == 422

def test_upload_init_oversized_rejected(client, db_session_factory):
    token = _register(client, "doc4@example.com")
    r = client.post(
        "/api/v1/documents/upload-init",
        headers=_h(token),
        json={"document_type": "income_certificate", "filename": "x.png", "mime_type": "image/png",
              "size_bytes": 999_000_000},
    )
    assert r.status_code == 422


def test_fake_mime_content_rejected_at_processing(client, db_session_factory):
    # Client declares image/png but uploads PDF bytes -> validation fails.
    token = _register(client, "doc5@example.com")
    init = client.post(
        "/api/v1/documents/upload-init", headers=_h(token),
        json={"document_type": "income_certificate", "filename": "x.png", "mime_type": "image/png",
              "size_bytes": len(pdf_bytes())},
    ).json()
    client.put(init["upload_url"], content=pdf_bytes())
    client.post(f"/api/v1/documents/{init['document_id']}/complete", headers=_h(token))
    detail = client.get(f"/api/v1/documents/{init['document_id']}", headers=_h(token)).json()
    assert detail["status"] in ("validation_failed", "processing_failed")


def test_corrupt_file_processing_failed(client, db_session_factory):
    token = _register(client, "doc6@example.com")
    corrupt = b"%PDF-1.4\nnot really a pdf"
    init = client.post(
        "/api/v1/documents/upload-init", headers=_h(token),
        json={"document_type": "income_certificate", "filename": "x.pdf", "mime_type": "application/pdf",
              "size_bytes": len(corrupt)},
    ).json()
    client.put(init["upload_url"], content=corrupt)
    client.post(f"/api/v1/documents/{init['document_id']}/complete", headers=_h(token))
    detail = client.get(f"/api/v1/documents/{init['document_id']}", headers=_h(token)).json()
    assert detail["status"] == "validation_failed"


def test_malicious_file_rejected(client, db_session_factory):
    # A PNG carrying the EICAR test signature -> malware detected -> rejected.
    token = _register(client, "doc7@example.com")
    eicar = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
    data = png_bytes(4, 4) + eicar
    init = client.post(
        "/api/v1/documents/upload-init", headers=_h(token),
        json={"document_type": "income_certificate", "filename": "x.png", "mime_type": "image/png",
              "size_bytes": len(data)},
    ).json()
    client.put(init["upload_url"], content=data)
    client.post(f"/api/v1/documents/{init['document_id']}/complete", headers=_h(token))
    detail = client.get(f"/api/v1/documents/{init['document_id']}", headers=_h(token)).json()
    assert detail["status"] == "rejected"


def test_duplicate_upload_detected_not_deleted(client, db_session_factory):
    token = _register(client, "doc8@example.com")
    d1, _ = _upload(client, token, income_png())
    d2, _ = _upload(client, token, income_png())  # identical content
    # Both documents still exist (policy: flag, don't auto-delete).
    listing = client.get("/api/v1/documents", headers=_h(token)).json()
    ids = {d["id"] for d in listing}
    assert d1 in ids and d2 in ids


# ------------------------------ verification -------------------------------- #
def test_low_confidence_requires_verification_then_confirm(client, db_session_factory):
    # An OTHER document with no recognized fields -> verification_required.
    token = _register(client, "doc9@example.com")
    doc_id, _ = _upload(
        client, token, income_png("Some unstructured note with no labeled fields"),
        dtype="other",
    )
    detail = client.get(f"/api/v1/documents/{doc_id}", headers=_h(token)).json()
    assert detail["status"] == "verification_required"
    # Confirm it.
    confirmed = client.post(f"/api/v1/documents/{doc_id}/confirm", headers=_h(token), json={"action": "confirm"})
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "verified"


def test_correction_preserves_original_extraction(client, db_session_factory):
    token = _register(client, "doc10@example.com")
    doc_id, _ = _upload(client, token, income_png())
    r = client.post(
        f"/api/v1/documents/{doc_id}/confirm",
        headers=_h(token),
        json={"action": "correct", "corrected_fields": {"annual_income": "150000"}, "correction_reason": "typo"},
    )
    assert r.status_code == 200
    detail = r.json()
    income = next(f for f in detail["fields"] if f["field_name"] == "annual_income")
    # Original raw + normalized preserved; correction stored separately.
    assert income["raw_value"] and "2,00,000" in income["raw_value"]
    assert income["normalized_value"] == "200000"
    assert income["verified_value"] == "150000"
    assert income["verification_status"] == "corrected"


def test_reject_document(client, db_session_factory):
    token = _register(client, "doc11@example.com")
    doc_id, _ = _upload(client, token, income_png())
    r = client.post(f"/api/v1/documents/{doc_id}/confirm", headers=_h(token), json={"action": "reject"})
    assert r.status_code == 200
    assert r.json()["status"] == "rejected"


def test_verification_audit_events(client, db_session_factory):
    token = _register(client, "doc12@example.com")
    doc_id, _ = _upload(client, token, income_png())
    client.post(f"/api/v1/documents/{doc_id}/confirm", headers=_h(token), json={"action": "confirm"})
    from app.models.audit_log import AuditLog

    with db_session_factory() as s:
        actions = set(s.scalars(select(AuditLog.action)).all())
    assert "document.upload_init" in actions
    assert "document.uploaded" in actions
    assert "document.processing_completed" in actions
    assert "document.verified" in actions
    # No raw document content in any audit diff.
    with db_session_factory() as s:
        for log in s.scalars(select(AuditLog)).all():
            blob = str(log.diff or {}).lower()
            assert "annual income" not in blob and "2,00,000" not in blob


# ------------------------------ conflict ------------------------------------ #
def test_conflict_detection_income(client, db_session_factory):
    token = _register(client, "doc13@example.com")
    # Profile income 999999; document says 200000 -> conflict.
    client.patch("/api/v1/me", headers=_h(token), json={"declared_annual_income": "999999"})
    doc_id, _ = _upload(client, token, income_png())
    detail = client.get(f"/api/v1/documents/{doc_id}", headers=_h(token)).json()
    assert detail["status"] == "verification_required"
    assert any(c["field"] == "annual_income" for c in detail["conflicts"])


def test_no_conflict_when_matching(client, db_session_factory):
    token = _register(client, "doc14@example.com")
    client.patch("/api/v1/me", headers=_h(token), json={"declared_annual_income": "200000"})
    doc_id, _ = _upload(client, token, income_png())
    detail = client.get(f"/api/v1/documents/{doc_id}", headers=_h(token)).json()
    assert not any(c["field"] == "annual_income" for c in detail["conflicts"])


# ------------------------------ download / delete --------------------------- #
def test_download_returns_signed_url_and_serves_bytes(client, db_session_factory):
    token = _register(client, "doc15@example.com")
    doc_id, _ = _upload(client, token, income_png())
    dl = client.get(f"/api/v1/documents/{doc_id}/download", headers=_h(token))
    assert dl.status_code == 200
    url = dl.json()["download_url"]
    assert "/documents/_local-object" in url  # never a public URL
    served = client.get(url)
    assert served.status_code == 200 and len(served.content) > 0


def test_delete_removes_object_and_row(client, db_session_factory):
    token = _register(client, "doc16@example.com")
    doc_id, _ = _upload(client, token, income_png())
    dele = client.delete(f"/api/v1/documents/{doc_id}", headers=_h(token))
    assert dele.status_code == 204
    # No longer listed / retrievable.
    assert client.get(f"/api/v1/documents/{doc_id}", headers=_h(token)).status_code == 404
    listing = client.get("/api/v1/documents", headers=_h(token)).json()
    assert all(d["id"] != doc_id for d in listing)


# ------------------------------ eligibility integration --------------------- #
def test_verified_document_facts_feed_eligibility(client, db_session_factory):
    """A verified income doc becomes evidence in the eligibility context;
    the deterministic engine still decides (prompt §52)."""
    from datetime import date

    from app.models.scheme import Scheme, SchemeVersion
    from app.models.eligibility import EligibilityRule
    from app.modules.documents.evidence import DocumentFactsProvider
    from app.modules.eligibility.compiler import compile_rows
    from app.modules.eligibility.context import ContextBuilder
    from app.modules.eligibility.engine import evaluate
    from app.models.citizen_profile import CitizenProfile
    from app.models.user import User

    token = _register(client, "doc17@example.com")
    doc_id, _ = _upload(client, token, income_png())  # income 200000, auto-verified
    detail = client.get(f"/api/v1/documents/{doc_id}", headers=_h(token)).json()
    # Ensure the doc is verified (auto or via confirm).
    if detail["status"] != "verified":
        client.post(f"/api/v1/documents/{doc_id}/confirm", headers=_h(token), json={"action": "confirm"})

    with db_session_factory() as s:
        user = s.scalar(select(User).where(User.email == "doc17@example.com"))
        profile = s.scalar(select(CitizenProfile).where(CitizenProfile.user_id == user.id))
        scheme = Scheme(canonical_name="Income Scheme", category="social_security", scope="state")
        s.add(scheme); s.flush()
        v = SchemeVersion(scheme_id=scheme.id, version_no=1, status="published",
                          benefits_summary="b", effective_from=date(2025, 1, 1))
        s.add(v); s.flush()
        s.add(EligibilityRule(
            scheme_version_id=v.id, rule_code="INCOME", field_key="declared_annual_income",
            operator="lte", value=250000, mandatory=True, sort_order=0,
            explanation_text="Income within limit.",
        ))
        s.flush()

        # Build context WITH document facts as evidence.
        doc_facts = DocumentFactsProvider(s).verified_facts(profile.id)
        assert doc_facts.get("declared_annual_income") == 200000.0

        ctx = ContextBuilder().build(
            citizen_profile=profile, primary_address=None,
            evaluation_date=date(2026, 1, 1), scheme_version_id=v.id, extra_facts=doc_facts,
        )
        rows = s.scalars(select(EligibilityRule).where(EligibilityRule.scheme_version_id == v.id)).all()
        result = evaluate(compile_rows(rows), ctx)
    # Engine decided PASS from the verified document evidence (200000 <= 250000).
    assert result.decision.value == "eligible"


def test_seed_documents_runs(client, db_session_factory):
    from app.seeds.seed_documents import seed

    with db_session_factory() as s:
        summary = seed(s)
    assert summary["document_id"]
