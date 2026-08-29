"""One-off end-to-end verification (not part of the test suite).

Boots a real PostgreSQL (pgserver), runs `alembic upgrade head` via the CLI
against the CLEAN database, starts the FastAPI app, and exercises:
    /api/v1/health, /api/v1/health/ready, /docs, /openapi.json
then compares the generated OpenAPI to the repository contract for the slice.
"""
from __future__ import annotations

import os
import subprocess
import sys

import pgserver

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)


def main() -> int:
    data_dir = os.path.join(HERE, ".verify_pgdata")
    server = pgserver.get_server(data_dir)
    try:
        url = server.get_uri(database="postgres").replace(
            "postgresql://", "postgresql+psycopg://", 1
        )
        env = {**os.environ, "DATABASE_URL": url, "ENVIRONMENT": "test"}

        # 1) alembic upgrade head against the clean DB (real CLI invocation).
        print(">>> alembic upgrade head")
        r = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=HERE,
            env=env,
            capture_output=True,
            text=True,
        )
        print(r.stdout)
        print(r.stderr)
        if r.returncode != 0:
            print("ALEMBIC FAILED")
            return 1

        # Confirm tables exist.
        from sqlalchemy import create_engine, inspect

        eng = create_engine(url)
        tables = set(inspect(eng).get_table_names())
        eng.dispose()
        expected = {
            "users",
            "citizen_profiles",
            "citizen_profile_versions",
            "addresses",
            "refresh_tokens",
            "audit_logs",
            "alembic_version",
        }
        print(">>> tables:", sorted(tables))
        assert expected <= tables, f"missing tables: {expected - tables}"

        # 2) Start the app and hit the live endpoints.
        os.environ["DATABASE_URL"] = url
        os.environ["ENVIRONMENT"] = "test"
        from app.core.config import get_settings
        from app.db import session as sess

        get_settings.cache_clear()
        sess.reset_engine()

        from fastapi.testclient import TestClient

        from app.main import create_app

        with TestClient(create_app()) as client:
            health = client.get("/api/v1/health")
            ready = client.get("/api/v1/health/ready")
            docs = client.get("/docs")
            spec = client.get("/openapi.json")
            print(">>> /api/v1/health ->", health.status_code, health.json())
            print(">>> /api/v1/health/ready ->", ready.status_code, ready.json())
            print(">>> /docs ->", docs.status_code)
            print(">>> /openapi.json ->", spec.status_code)

            assert health.status_code == 200 and health.json() == {"status": "ok"}
            assert ready.status_code == 200 and ready.json()["status"] == "ready"
            assert docs.status_code == 200
            gen = spec.json()

        # 3) Compare generated OpenAPI vs contract for the slice.
        import yaml

        with open(os.path.join(REPO, "openapi.yaml"), encoding="utf-8") as fh:
            contract = yaml.safe_load(fh)

        slice_paths = {
            "/health": {"get"},
            "/health/ready": {"get"},
            "/auth/register": {"post"},
            "/auth/login": {"post"},
            "/auth/refresh": {"post"},
            "/auth/logout": {"post"},
            "/me": {"get", "patch"},
            "/me/account": {"get"},
            "/me/profile": {"get", "put", "patch"},
            "/me/addresses": {"get", "post"},
            "/me/addresses/{address_id}": {"put", "delete"},
        }
        gen_paths = gen["paths"]
        mismatches = []
        for path, methods in slice_paths.items():
            if path not in contract["paths"]:
                mismatches.append(f"contract missing {path}")
            full = f"/api/v1{path}"
            if full not in gen_paths:
                mismatches.append(f"impl missing {full}")
                continue
            impl_methods = {m.lower() for m in gen_paths[full]}
            if not methods <= impl_methods:
                mismatches.append(f"{full} missing {methods - impl_methods}")

        if mismatches:
            print(">>> OPENAPI MISMATCHES:", mismatches)
            return 1
        print(">>> OpenAPI generated matches contract for the slice. OK")
        print(">>> ALL VERIFICATION CHECKS PASSED")
        return 0
    finally:
        server.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
