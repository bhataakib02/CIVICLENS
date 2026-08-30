# CivicLens Production Worker Dockerfile (Multi-stage)
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

COPY backend/requirements.txt .
RUN sed '/^pgserver/d' requirements.txt > requirements.runtime.txt \
    && pip install --prefix=/install -r requirements.runtime.txt

FROM python:3.12-slim AS runner

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/install/bin:$PATH" \
    PYTHONPATH="/install/lib/python3.12/site-packages:/app"

WORKDIR /app

COPY --from=builder /install /install
COPY backend/app ./app
COPY workers ./workers

RUN useradd --create-home --uid 10001 workeruser \
    && chown -R workeruser:workeruser /app
USER workeruser

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

CMD ["python", "-m", "workers.supervisor"]
