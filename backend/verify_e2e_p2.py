"""One-off end-to-end verification for the scheme + eligibility slice.

Boots a real PostgreSQL (pgserver), runs `alembic upgrade head` on the CLEAN
database (both migrations 0001 + 0002), seeds demo data, then exercises the
live API: health, schemes list, and an eligibility check; finally compares the
generated OpenAPI to the repository contract for this slice.
"""
from __future__ import annotations

import os
import subprocess
import sys

import pgserver

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
STRONG_PW = "CorrectHorse9Battery!"


def main() -> int:
    data_dir = os.path.join(HERE, ".verify_pg2")
    server = pgserver.get_server(data_dir)
    try:
        url = server.get_uri(database="postgres").replace(
            "postgresql://", "postgresql+psycopg://", 1
        )
        env = {**os.environ, "DATABASE_URL": url, "ENVIRONMENT": "test"}

        print(">>> alembic upgrade head (clean DB)")
        r = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=HERE, env=env, capture_output=True, text=True,
        )
        print(r.stdout, r.stderr)
        if r.returncode != 0:
            print("ALEMBIC FAILED")
            return 1

        from sqlalchemy import create_engine, inspect

        eng = create_engine(url)
        tables = set(inspect(eng).get_table_names())
        eng.dispose()
        expected = {
            "users", "citizen_profiles", "citizen_profile_versions", "addresses",
            "refresh_tokens", "audit_logs", "schemes", "scheme_versions",
            "eligibility_rules", "eligibility_checks", "alembic_version",
        }
        assert expected <= tables, f"missing tables: {expected - tables}"
        print(">>> tables OK:", sorted(tables))

        os.environ["DATABASE_URL"] = url
        os.environ["ENVIRONMENT"] = "test"
        from app.core.config import get_settings
        from app.db import session as sess

        get_settings.cache_clear()
        sess.reset_engine()

        # Seed real user accounts.
        from app.seeds.seed_requested_users import seed

        s = sess.get_sessionmaker()()
        try:
            summary = seed(s)
        finally:
            s.close()
        print(">>> seeded:", summary)

        from fastapi.testclient import TestClient

        from app.main import create_app

        with TestClient(create_app()) as client:
            assert client.get("/api/v1/health").status_code == 200
            assert client.get("/api/v1/health/ready").json()["status"] == "ready"

            # Login as the seeded eligible citizen and check Scheme A.
            login = client.post(
                "/api/v1/auth/login",
                json={"email": "demo.eligible@example.com", "password": "CivicDemoPass123!"},
            )
            token = login.json()["access_token"]
            h = {"Authorization": f"Bearer {token}"}

            schemes = client.get("/api/v1/schemes", headers=h)
            print(">>> /schemes ->", schemes.status_code, "total:", schemes.json()["total"])
            assert schemes.status_code == 200 and schemes.json()["total"] >= 3

            va = summary["scheme_a_version_id"]
            chk = client.post(
                "/api/v1/eligibility/check", headers=h, json={"scheme_version_id": va}
            )
            body = chk.json()
            print(">>> eligibility (eligible citizen, Scheme A) ->", chk.status_code, body["result"])
            assert chk.status_code == 200 and body["result"] == "eligible"
            assert body["engine_version"] == "1.0.0"

            # not-eligible citizen
            login2 = client.post(
                "/api/v1/auth/login",
                json={"email": "demo.noteligible@example.com", "password": "CivicDemoPass123!"},
            )
            h2 = {"Authorization": f"Bearer {login2.json()['access_token']}"}
            chk2 = client.post("/api/v1/eligibility/check", headers=h2, json={"scheme_version_id": va})
            print(">>> eligibility (not-eligible citizen) ->", chk2.json()["result"])
            assert chk2.json()["result"] == "not_eligible"

            gen_paths = client.get("/openapi.json").json()["paths"]

        # OpenAPI sync for the slice.
        import yaml

        with open(os.path.join(REPO, "openapi.yaml"), encoding="utf-8") as fh:
            contract = yaml.safe_load(fh)

        slice_paths = {
            "/schemes": {"get", "post"},
            "/schemes/{scheme_id}/versions": {"get", "post"},
            "/scheme-versions/{scheme_version_id}/rules": {"get", "post"},
            "/eligibility/check": {"post"},
            "/admin/scheme-versions/{scheme_version_id}/publish": {"post"},
            "/admin/scheme-versions/{scheme_version_id}/supersede": {"post"},
            "/admin/rules/validate": {"post"},
        }
        mismatches = []
        for path, methods in slice_paths.items():
            if path not in contract["paths"]:
                mismatches.append(f"contract missing {path}")
            full = f"/api/v1{path}"
            if full not in gen_paths:
                mismatches.append(f"impl missing {full}")
                continue
            if not methods <= {m.lower() for m in gen_paths[full]}:
                mismatches.append(f"{full} method mismatch")
        if mismatches:
            print(">>> OPENAPI MISMATCHES:", mismatches)
            return 1
        print(">>> OpenAPI matches contract for the scheme+eligibility slice. OK")
        print(">>> ALL PROMPT-2 VERIFICATION CHECKS PASSED")
        return 0
    finally:
        server.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
