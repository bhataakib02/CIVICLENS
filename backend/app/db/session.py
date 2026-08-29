"""Database engine + session management (sync SQLAlchemy 2.x + psycopg v3).

Async is deliberately NOT used: ADR-001 (modular monolith) and the existing
docs describe a synchronous service/repository layer, and there is no
consistent async pattern to extend. Introducing async here would add
complexity for appearance only (see prompt technology requirements).

Transaction discipline: the `db_session` dependency yields a Session and
guarantees close(); services perform explicit commit()/rollback().
"""
from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings, get_settings

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def _build_engine(settings: Settings) -> Engine:
    return create_engine(
        settings.database_url,
        pool_pre_ping=True,  # detect dropped connections before use
        future=True,
    )


def get_engine(settings: Settings | None = None) -> Engine:
    """Return the process-wide engine, creating it on first use."""
    global _engine, _SessionLocal
    if _engine is None:
        settings = settings or get_settings()
        _engine = _build_engine(settings)
        _SessionLocal = sessionmaker(
            bind=_engine, autoflush=False, autocommit=False, expire_on_commit=False
        )
    return _engine


def get_sessionmaker() -> sessionmaker[Session]:
    if _SessionLocal is None:
        get_engine()
    assert _SessionLocal is not None
    return _SessionLocal


def reset_engine() -> None:
    """Dispose and clear the engine (used by tests to rebind DATABASE_URL)."""
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None


def db_session() -> Iterator[Session]:
    """FastAPI dependency yielding a Session with guaranteed close().

    Services own commit/rollback semantics. On an unhandled exception we roll
    back defensively so a failed request never leaves a dangling transaction.
    """
    session = get_sessionmaker()()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
