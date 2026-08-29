"""Pytest fixtures.

Integration/security tests run against a REAL PostgreSQL provided by the
`pgserver` package (a bundled Postgres binary) — no mocks, no SQLite. The
schema is created by running the actual Alembic migration, so migration
correctness is exercised too.

Unit tests (test_unit_*) do not require the DB and skip cleanly if pgserver
is unavailable.
"""
from __future__ import annotations

import os
from collections.abc import Iterator

import pytest

# Ensure a deterministic secret/config for tests before app imports settings.
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-fixed-for-deterministic-tests-000000")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "15")
os.environ.setdefault("REFRESH_TOKEN_EXPIRE_DAYS", "30")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")
# Documents: local storage under a temp dir for tests.
os.environ.setdefault("STORAGE_PROVIDER", "local")
os.environ.setdefault(
    "STORAGE_LOCAL_ROOT", os.path.join(os.environ.get("TEMP", "/tmp"), "civiclens_test_storage")
)


@pytest.fixture(scope="session")
def pg_database_url(tmp_path_factory: pytest.TempPathFactory) -> Iterator[str]:
    """Start a real ephemeral PostgreSQL for the test session."""
    pgserver = pytest.importorskip("pgserver")
    data_dir = tmp_path_factory.mktemp("pgdata")
    server = pgserver.get_server(str(data_dir))
    try:
        # psycopg v3 SQLAlchemy URL.
        raw = server.get_uri(database="postgres")
        url = raw.replace("postgresql://", "postgresql+psycopg://", 1)
        yield url
    finally:
        server.cleanup()


@pytest.fixture(scope="session", autouse=False)
def _configure_db(pg_database_url: str) -> Iterator[None]:
    """Point the app + Alembic at the test DB and run the migration once."""
    os.environ["DATABASE_URL"] = pg_database_url

    from app.core.config import get_settings
    from app.db import session as db_session_mod

    get_settings.cache_clear()  # type: ignore[attr-defined]
    db_session_mod.reset_engine()

    # Run the real Alembic migration against the clean database.
    from alembic import command
    from alembic.config import Config

    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cfg = Config(os.path.join(here, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(here, "alembic"))
    command.upgrade(cfg, "head")

    yield

    db_session_mod.reset_engine()


@pytest.fixture()
def db_clean(_configure_db: None) -> Iterator[None]:
    """Truncate all slice tables between tests for isolation."""
    from sqlalchemy import text

    from app.db.session import get_engine

    engine = get_engine()
    with engine.begin() as conn:
        # Truncate every data table (all except alembic_version) so each test
        # starts from a clean slate regardless of which modules it touches.
        rows = conn.execute(
            text(
                "SELECT tablename FROM pg_tables WHERE schemaname='public' "
                "AND tablename <> 'alembic_version'"
            )
        ).scalars().all()
        if rows:
            joined = ", ".join(f'"{t}"' for t in rows)
            conn.execute(text(f"TRUNCATE {joined} RESTART IDENTITY CASCADE"))
    yield


@pytest.fixture()
def client(db_clean: None):
    """A TestClient bound to the app configured against the real test DB."""
    from fastapi.testclient import TestClient

    from app.main import create_app

    app = create_app()
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def db_session_factory(db_clean: None):
    from app.db.session import get_sessionmaker

    return get_sessionmaker()
