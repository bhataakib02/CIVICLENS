# CivicLens backend image.
# Python 3.12 (prompt target). App also runs on 3.11.
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps kept minimal; psycopg[binary] ships its own libpq.
COPY requirements.txt .
# pgserver is a test-only dependency (bundled Postgres for integration tests);
# exclude it from the runtime image.
RUN sed '/^pgserver/d' requirements.txt > requirements.runtime.txt \
    && pip install -r requirements.runtime.txt

COPY alembic.ini pyproject.toml ./
COPY alembic ./alembic
COPY app ./app

# Run as a non-root user.
RUN useradd --create-home --uid 10001 appuser
USER appuser

EXPOSE 8000

# Apply migrations, then serve. DATABASE_URL / JWT_SECRET_KEY injected at runtime.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
