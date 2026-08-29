"""One-off end-to-end verification for the document intelligence slice.

Boots a real PostgreSQL (pgserver), runs `alembic upgrade head` on the CLEAN
database (migrations 0001-0004), then exercises the live API: health, the full
secure upload flow (init -> signed PUT -> complete -> processed detail),
download, and delete; finally compares generated OpenAPI to the contract.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile

import pgserver

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
PW = "CorrectHorse9Battery!"


def main() -> int:
    data_dir = os.path.join(HERE, ".verify_pg4")
    server = pgserver.get_server(data_dir)
    try:
        url = server.get_uri(database="postgres").replace("postgresql://", "postgresql+psycopg://", 1)
        storage_root = tempfile.mkdtemp(prefix="civiclens_verify_docs_")
        env = {**os.environ, "DATABASE_URL": url, "ENVIRONMENT": "test",
               "STORAGE_PROVIDER": "local", "STORAGE_LOCAL_ROOT": storage_root}

        print(">>> alembic upgrade head (clean DB)")
        r = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"],
                           cwd=HERE, env=env, capture_output=True, text=True)
        print(r.stdout, r.stderr)
        if r.returncode != 0:
            return 1

        from sqlalchemy import create_engine, inspect

        eng = create_engine(url)
        tables = set(inspect(eng).get_table_names())
        eng.dispose()
        expected = {
            "documents", "document_processing_jobs", "document_extractions",
            "document_extracted_fields", "document_verifications", "alembic_version",
        }
        assert expected <= tables, f"missing: {expected - tables}"
        print(">>> document tables OK:", sorted(t for t in tables if 'document' in t))

        os.environ.update(env)
        from app.core.config import get_settings
        from app.db import session as sess
        from app.modules.documents.storage import reset_storage_cache

        get_settings.cache_clear()
        sess.reset_engine()
        reset_storage_cache()

        from fastapi.testclient import TestClient

        from app.main import create_app
        from tests.doc_helpers import income_png  # reuse the builder

        with TestClient(create_app()) as client:
            assert client.get("/api/v1/health").status_code == 200
            assert client.get("/api/v1/health/ready").json()["status"] == "ready"

            client.post("/api/v1/auth/register", json={"email": "vdoc@example.com", "password": PW})
            token = client.post("/api/v1/auth/login", json={"email": "vdoc@example.com", "password": PW}).json()["access_token"]
            h = {"Authorization": f"Bearer {token}"}

            assert client.get("/api/v1/documents", headers=h).status_code == 200

            data = income_png()
            init = client.post("/api/v1/documents/upload-init", headers=h,
                               json={"document_type": "income_certificate", "filename": "d.png",
                                     "mime_type": "image/png", "size_bytes": len(data)}).json()
            client.put(init["upload_url"], content=data)
            comp = client.post(f"/api/v1/documents/{init['document_id']}/complete", headers=h)
            print(">>> upload complete ->", comp.status_code)
            detail = client.get(f"/api/v1/documents/{init['document_id']}", headers=h).json()
            income = next((f for f in detail["fields"] if f["field_name"] == "annual_income"), None)
            print(">>> processed status:", detail["status"], "income normalized:", income and income["normalized_value"])
            assert detail["status"] in ("verified", "verification_required")
            assert income and income["normalized_value"] == "200000"
            assert "storage_key" not in detail

            dl = client.get(f"/api/v1/documents/{init['document_id']}/download", headers=h)
            assert dl.status_code == 200 and client.get(dl.json()["download_url"]).status_code == 200
            print(">>> download OK")

            assert client.delete(f"/api/v1/documents/{init['document_id']}", headers=h).status_code == 204
            assert client.get(f"/api/v1/documents/{init['document_id']}", headers=h).status_code == 404
            print(">>> delete OK")

            gen_paths = client.get("/openapi.json").json()["paths"]

        import yaml

        with open(os.path.join(REPO, "openapi.yaml"), encoding="utf-8") as fh:
            contract = yaml.safe_load(fh)
        slice_paths = {
            "/documents": {"get", "post"},
            "/documents/upload-init": {"post"},
            "/documents/{document_id}/complete": {"post"},
            "/documents/{document_id}": {"get", "delete"},
            "/documents/{document_id}/download": {"get"},
            "/documents/{document_id}/confirm": {"post"},
        }
        mismatches = []
        for path, methods in slice_paths.items():
            if path not in contract["paths"]:
                mismatches.append(f"contract missing {path}")
            full = f"/api/v1{path}"
            if full not in gen_paths or not methods <= {m.lower() for m in gen_paths[full]}:
                mismatches.append(f"impl mismatch {full}")
        if mismatches:
            print(">>> OPENAPI MISMATCHES:", mismatches)
            return 1
        print(">>> OpenAPI matches contract for the documents slice. OK")
        print(">>> ALL PROMPT-4 VERIFICATION CHECKS PASSED")
        return 0
    finally:
        server.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
