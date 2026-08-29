"""workers — Celery Async Task Definitions.

Background job definitions for OCR/extraction, knowledge ingestion, and
notification dispatch — the async half of the system's request handling
(ADR-006). Runs as a separate ECS/Fargate service from the API tier.

See ``docs/backend/background-jobs.md`` for the full job catalog and queue design.
"""

from workers.celery_app import celery_app

__all__ = ["celery_app"]
