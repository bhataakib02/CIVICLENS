"""Security tests: document object-level authorization + isolation (prompt §44)."""
from __future__ import annotations

import time
import uuid

import pytest

from tests.doc_helpers import income_png

pytestmark = pytest.mark.security

STRONG_PW = "CorrectHorse9Battery!"


def _register(client, email):
    return client.post("/api/v1/auth/register", json={"email": email, "password": STRONG_PW}).json()["access_token"]


def _h(t):
    return {"Authorization": f"Bearer {t}"}


def _upload(client, token, data=None):
    data = data or income_png()
    init = client.post(
        "/api/v1/documents/upload-init", headers=_h(token),
        json={"document_type": "income_certificate", "filename": "d.png", "mime_type": "image/png",
              "size_bytes": len(data)},
    ).json()
    client.put(init["upload_url"], content=data)
    client.post(f"/api/v1/documents/{init['document_id']}/complete", headers=_h(token))
    return init["document_id"]


def test_citizen_cannot_read_another_document(client, db_session_factory):
    a = _register(client, "a_sec@example.com")
    b = _register(client, "b_sec@example.com")
    doc_a = _upload(client, a)
    r = client.get(f"/api/v1/documents/{doc_a}", headers=_h(b))
    assert r.status_code == 404  # no existence disclosure
    assert r.json()["error"]["code"] == "NOT_FOUND"


def test_citizen_cannot_download_another_document(client, db_session_factory):
    a = _register(client, "a_dl@example.com")
    b = _register(client, "b_dl@example.com")
    doc_a = _upload(client, a)
    assert client.get(f"/api/v1/documents/{doc_a}/download", headers=_h(b)).status_code == 404


def test_citizen_cannot_delete_another_document(client, db_session_factory):
    a = _register(client, "a_del@example.com")
    b = _register(client, "b_del@example.com")
    doc_a = _upload(client, a)
    assert client.delete(f"/api/v1/documents/{doc_a}", headers=_h(b)).status_code == 404
    # A's document is still intact.
    assert client.get(f"/api/v1/documents/{doc_a}", headers=_h(a)).status_code == 200


def test_citizen_cannot_confirm_another_document(client, db_session_factory):
    a = _register(client, "a_cfm@example.com")
    b = _register(client, "b_cfm@example.com")
    doc_a = _upload(client, a)
    r = client.post(f"/api/v1/documents/{doc_a}/confirm", headers=_h(b), json={"action": "confirm"})
    assert r.status_code == 404


def test_document_list_isolated_per_citizen(client, db_session_factory):
    a = _register(client, "a_list@example.com")
    b = _register(client, "b_list@example.com")
    doc_a = _upload(client, a)
    b_list = client.get("/api/v1/documents", headers=_h(b)).json()
    assert all(d["id"] != doc_a for d in b_list)


def test_storage_key_never_exposed(client, db_session_factory):
    token = _register(client, "keyhide@example.com")
    doc_id = _upload(client, token)
    detail = client.get(f"/api/v1/documents/{doc_id}", headers=_h(token)).text
    listing = client.get("/api/v1/documents", headers=_h(token)).text
    assert "storage_key" not in detail and "storage_key" not in listing
    # The opaque storage layout prefix must not leak either.
    assert "documents/" not in detail.replace("/api/v1/documents", "")


def test_unauthenticated_document_access_fails(client):
    assert client.get("/api/v1/documents").status_code == 401
    assert client.post("/api/v1/documents/upload-init", json={}).status_code == 401
    assert client.get(f"/api/v1/documents/{uuid.uuid4()}").status_code == 401


def test_expired_signed_download_url_rejected(client, db_session_factory):
    token = _register(client, "expiry@example.com")
    doc_id = _upload(client, token)
    dl = client.get(f"/api/v1/documents/{doc_id}/download", headers=_h(token)).json()
    url = dl["download_url"]
    # Tamper the expires param to the past -> signature check fails.
    import re

    expired_url = re.sub(r"expires=\d+", f"expires={int(time.time()) - 100}", url)
    r = client.get(expired_url)
    assert r.status_code in (400, 422)  # ValidationError envelope for bad signature


def test_tampered_signature_rejected(client, db_session_factory):
    token = _register(client, "tamper@example.com")
    doc_id = _upload(client, token)
    url = client.get(f"/api/v1/documents/{doc_id}/download", headers=_h(token)).json()["download_url"]
    import re

    bad = re.sub(r"sig=[0-9a-f]+", "sig=deadbeef", url)
    assert client.get(bad).status_code in (400, 422)


def test_path_traversal_filename_does_not_escape(client, db_session_factory):
    # A malicious filename must not affect the storage key / disk path.
    token = _register(client, "trav@example.com")
    data = income_png()
    init = client.post(
        "/api/v1/documents/upload-init", headers=_h(token),
        json={"document_type": "income_certificate", "filename": "../../../../etc/passwd",
              "mime_type": "image/png", "size_bytes": len(data)},
    ).json()
    # The upload URL's storage key is generated, not derived from the filename.
    assert "etc/passwd" not in init["upload_url"]
    client.put(init["upload_url"], content=data)
    comp = client.post(f"/api/v1/documents/{init['document_id']}/complete", headers=_h(token))
    assert comp.status_code == 202  # processed safely; filename is just metadata
