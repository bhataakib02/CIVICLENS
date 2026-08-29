"""One-off end-to-end verification for the knowledge + RAG slice.

Boots a real PostgreSQL (pgserver), runs `alembic upgrade head` on the CLEAN
database (migrations 0001+0002+0003 incl. pgvector), seeds demo schemes +
knowledge, then exercises the live API: health, knowledge/search, and
assistant/query; finally compares generated OpenAPI to the contract.
"""
from __future__ import annotations

import os
import subprocess
import sys

import pgserver

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)


def main() -> int:
    data_dir = os.path.join(HERE, ".verify_pg3")
    server = pgserver.get_server(data_dir)
    try:
        url = server.get_uri(database="postgres").replace("postgresql://", "postgresql+psycopg://", 1)
        env = {**os.environ, "DATABASE_URL": url, "ENVIRONMENT": "test"}

        print(">>> alembic upgrade head (clean DB)")
        r = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=HERE, env=env, capture_output=True, text=True,
        )
        print(r.stdout, r.stderr)
        if r.returncode != 0:
            return 1

        from sqlalchemy import create_engine, inspect

        eng = create_engine(url)
        tables = set(inspect(eng).get_table_names())
        eng.dispose()
        expected = {
            "users", "citizen_profiles", "addresses", "refresh_tokens", "audit_logs",
            "schemes", "scheme_versions", "eligibility_rules", "eligibility_checks",
            "knowledge_sources", "knowledge_chunks", "ingestion_jobs", "alembic_version",
        }
        assert expected <= tables, f"missing: {expected - tables}"
        print(">>> tables OK:", sorted(tables))

        os.environ["DATABASE_URL"] = url
        os.environ["ENVIRONMENT"] = "test"
        from app.core.config import get_settings
        from app.db import session as sess

        get_settings.cache_clear()
        sess.reset_engine()

        # Seed schemes then knowledge (knowledge links to schemes).
        from app.seeds.seed_demo import seed as seed_schemes
        from app.seeds.seed_knowledge import seed as seed_knowledge

        s = sess.get_sessionmaker()()
        try:
            sch = seed_schemes(s)
            kn = seed_knowledge(s)
        finally:
            s.close()
        print(">>> seeded schemes:", sch)
        print(">>> seeded knowledge sources:", kn)

        from fastapi.testclient import TestClient

        from app.main import create_app

        with TestClient(create_app()) as client:
            assert client.get("/api/v1/health").status_code == 200
            assert client.get("/api/v1/health/ready").json()["status"] == "ready"

            # Register a citizen (all authenticated users may search/query).
            client.post("/api/v1/auth/register", json={"email": "verify@example.com", "password": "CorrectHorse9Battery!"})
            login = client.post("/api/v1/auth/login", json={"email": "verify@example.com", "password": "CorrectHorse9Battery!"})
            h = {"Authorization": f"Bearer {login.json()['access_token']}"}

            search = client.post(
                "/api/v1/knowledge/search", headers=h,
                json={"query": "what documents are required for income support", "limit": 5},
            )
            print(">>> /knowledge/search ->", search.status_code, "results:", len(search.json()))
            assert search.status_code == 200 and len(search.json()) >= 1

            aq = client.post(
                "/api/v1/assistant/query", headers=h,
                json={"query": "What documents are required for income support?"},
            )
            body = aq.json()
            print(">>> /assistant/query ->", aq.status_code, "grounded:", body["grounded"], "citations:", len(body["citations"]))
            assert aq.status_code == 200 and body["grounded"] and len(body["citations"]) >= 1

            gen_paths = client.get("/openapi.json").json()["paths"]

        import yaml

        with open(os.path.join(REPO, "openapi.yaml"), encoding="utf-8") as fh:
            contract = yaml.safe_load(fh)
        slice_paths = {
            "/knowledge/search": {"post"},
            "/knowledge/sources": {"get", "post"},
            "/knowledge/jobs/{job_id}": {"get"},
            "/knowledge/sources/{source_id}/verify": {"post"},
            "/assistant/query": {"post"},
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
        print(">>> OpenAPI matches contract for the knowledge slice. OK")
        print(">>> ALL PROMPT-3 VERIFICATION CHECKS PASSED")
        return 0
    finally:
        server.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
