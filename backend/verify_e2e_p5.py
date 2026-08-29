"""One-off end-to-end verification for the application workflow slice.

Boots a real PostgreSQL (pgserver), runs `alembic upgrade head` on the CLEAN
database (migrations 0001-0005), seeds dev data, then exercises the live API:
health, list applications, create -> submit (mock provider) -> review ->
complete; finally compares generated OpenAPI to the contract.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from datetime import date

import pgserver

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
PW = "CorrectHorse9Battery!"


def main() -> int:
    data_dir = os.path.join(HERE, ".verify_pg5")
    server = pgserver.get_server(data_dir)
    try:
        url = server.get_uri(database="postgres").replace("postgresql://", "postgresql+psycopg://", 1)
        storage_root = tempfile.mkdtemp(prefix="civiclens_verify5_")
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
            "applications", "application_documents", "application_status_history",
            "application_submissions", "application_assignments", "application_actions",
            "document_requirements", "notifications", "outbox_events", "alembic_version",
        }
        assert expected <= tables, f"missing: {expected - tables}"
        print(">>> application tables OK")

        os.environ.update(env)
        from app.core.config import get_settings
        from app.db import session as sess

        get_settings.cache_clear()
        sess.reset_engine()

        # Build an eligible, document-ready citizen directly, then drive the API.
        from app.models.citizen_profile import CitizenProfile
        from app.models.document import Document
        from app.models.document_requirement import DocumentRequirement
        from app.models.eligibility import EligibilityRule
        from app.models.enums import DocumentStatus, DocumentType, UserRole, UserStatus
        from app.models.scheme import Scheme, SchemeVersion
        from app.models.user import User
        from app.core.security import hash_password

        s = sess.get_sessionmaker()()
        try:
            scheme = Scheme(canonical_name="Verify Emp", category="employment", scope="central")
            s.add(scheme); s.flush()
            v = SchemeVersion(scheme_id=scheme.id, version_no=1, status="published",
                              benefits_summary="b", effective_from=date(2025, 1, 1))
            s.add(v); s.flush()
            s.add(EligibilityRule(scheme_version_id=v.id, rule_code="INCOME",
                                  field_key="declared_annual_income", operator="lte", value=250000,
                                  mandatory=True, sort_order=0, explanation_text="x"))
            s.add(DocumentRequirement(scheme_version_id=v.id, document_type=DocumentType.INCOME_CERTIFICATE, is_mandatory=True))
            user = User(email="verify5@example.com", password_hash=hash_password(PW),
                        role=UserRole.CITIZEN, status=UserStatus.ACTIVE)
            user.profile = CitizenProfile(current_version_no=1, declared_annual_income=100000)
            s.add(user); s.flush()
            s.add(Document(citizen_profile_id=user.profile.id, document_type=DocumentType.INCOME_CERTIFICATE,
                           status=DocumentStatus.VERIFIED, storage_key="k/verify"))
            admin = User(email="verify5admin@example.com", password_hash=hash_password(PW),
                         role=UserRole.ADMIN, status=UserStatus.ACTIVE)
            cw = User(email="verify5cw@example.com", password_hash=hash_password(PW),
                      role=UserRole.AGENT, status=UserStatus.ACTIVE)
            s.add_all([admin, cw]); s.flush()
            version_id = str(v.id); cw_id = str(cw.id)
            s.commit()
        finally:
            s.close()

        from fastapi.testclient import TestClient

        from app.main import create_app

        with TestClient(create_app()) as client:
            assert client.get("/api/v1/health").status_code == 200
            assert client.get("/api/v1/health/ready").json()["status"] == "ready"

            def login(email):
                return {"Authorization": "Bearer " + client.post(
                    "/api/v1/auth/login", json={"email": email, "password": PW}).json()["access_token"]}

            ch = login("verify5@example.com")
            assert client.get("/api/v1/applications", headers=ch).status_code == 200

            app_id = client.post("/api/v1/applications", headers=ch, json={"scheme_version_id": version_id}).json()["id"]
            sub = client.post(f"/api/v1/applications/{app_id}/submit", headers=ch)
            print(">>> submit ->", sub.status_code, sub.json()["status"], "ref:", sub.json()["submission"]["external_reference"])
            assert sub.status_code == 200 and sub.json()["status"] == "submitted"

            ah = login("verify5admin@example.com")
            client.post(f"/api/v1/applications/{app_id}/assign", headers=ah, json={"case_worker_id": cw_id})
            cwh = login("verify5cw@example.com")
            rev = client.post(f"/api/v1/applications/{app_id}/review", headers=cwh,
                              json={"action": "approve", "reason": "ok"})
            comp = client.post(f"/api/v1/applications/{app_id}/complete", headers=cwh)
            print(">>> review ->", rev.json()["status"], "complete ->", comp.json()["status"])
            assert rev.json()["status"] == "approved" and comp.json()["status"] == "completed"

            # Notification emitted.
            notifs = client.get("/api/v1/notifications", headers=ch).json()
            print(">>> notifications:", len(notifs))
            assert len(notifs) >= 1

            gen_paths = client.get("/openapi.json").json()["paths"]

        import yaml

        with open(os.path.join(REPO, "openapi.yaml"), encoding="utf-8") as fh:
            contract = yaml.safe_load(fh)
        slice_paths = {
            "/applications": {"get", "post"},
            "/applications/{application_id}/submit": {"post"},
            "/applications/{application_id}/checklist": {"get"},
            "/applications/{application_id}/review": {"post"},
            "/applications/{application_id}/assign": {"post"},
            "/applications/{application_id}/complete": {"post"},
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
        print(">>> OpenAPI matches contract for the applications slice. OK")
        print(">>> ALL PROMPT-5 VERIFICATION CHECKS PASSED")
        return 0
    finally:
        server.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
