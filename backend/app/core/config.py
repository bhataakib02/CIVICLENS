"""Typed application configuration (Pydantic Settings).

Secrets are never hardcoded here; they are read from the environment / .env.
See docs/security/secrets-management.md.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings sourced from environment variables / .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )

    # Runtime
    environment: Literal["development", "test", "staging", "production"] = "development"

    # Database (real PostgreSQL, psycopg v3 driver)
    database_url: str = Field(
        default="postgresql+psycopg://civiclens:civiclens@localhost:5432/civiclens"
    )

    # JWT
    jwt_secret_key: str = Field(default="dev-only-insecure-change-me-please-0000000000000000")
    jwt_algorithm: str = Field(default="HS256")
    jwt_issuer: str = Field(default="civiclens")
    access_token_expire_minutes: int = Field(default=15, ge=1)
    refresh_token_expire_days: int = Field(default=30, ge=1)

    # CORS: comma-separated env value (parsed via the `cors_origins` property).
    cors_origins_raw: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")

    # Password policy
    password_min_length: int = Field(default=12, ge=8)

    # --- Knowledge / RAG ---
    # Providers: "test" = deterministic in-repo provider (tests/dev only);
    # a real provider name (e.g. "openai") must be explicitly configured for
    # production. embedding_dimension MUST match the pgvector column (1536).
    embedding_provider: str = Field(default="test")
    embedding_dimension: int = Field(default=1536, ge=1)
    embedding_batch_size: int = Field(default=64, ge=1)
    llm_provider: str = Field(default="test")
    llm_model: str = Field(default="test-deterministic")
    # Ingestion / fetcher safety limits.
    fetch_timeout_seconds: float = Field(default=10.0, gt=0)
    fetch_max_bytes: int = Field(default=5_000_000, gt=0)
    fetch_max_redirects: int = Field(default=3, ge=0)
    fetch_max_retries: int = Field(default=3, ge=0)
    fetch_allow_private_ips: bool = Field(default=False)  # SSRF guard; True only in tests
    # Retrieval defaults.
    retrieval_candidate_limit: int = Field(default=30, ge=1)
    retrieval_min_score: float = Field(default=0.0, ge=0.0)

    # --- Documents / storage ---
    storage_provider: str = Field(default="local")  # "local" | "s3"
    storage_local_root: str = Field(default=".document_storage")
    s3_bucket: str = Field(default="", alias="S3_BUCKET")
    s3_region: str = Field(default="", alias="S3_REGION")
    s3_endpoint: str = Field(default="", alias="S3_ENDPOINT")
    document_max_size_mb: int = Field(default=10, ge=1)
    document_max_pages: int = Field(default=50, ge=1)
    document_max_image_pixels: int = Field(default=40_000_000, ge=1)  # zip-bomb / decompression guard
    signed_url_expiration_seconds: int = Field(default=600, ge=1)
    document_retention_days: int | None = Field(default=None)
    # Document AI providers (test-only bundled; production must configure real).
    ocr_provider: str = Field(default="test")
    extraction_provider: str = Field(default="test")
    malware_scanner_provider: str = Field(default="test")
    document_confidence_high: float = Field(default=0.90, ge=0.0, le=1.0)
    document_confidence_medium: float = Field(default=0.70, ge=0.0, le=1.0)

    # --- Applications / submission / notifications ---
    # "mock" = NON-PRODUCTION test provider; production must configure a real one.
    submission_provider: str = Field(default="mock")
    email_provider: str = Field(default="test")
    sms_provider: str = Field(default="test")
    push_provider: str = Field(default="test")

    # --- Event worker / outbox (prompt §31, §50) ---
    outbox_worker_batch_size: int = Field(default=50, ge=1)
    outbox_worker_concurrency: int = Field(default=1, ge=1)  # in-process default
    notification_max_attempts: int = Field(default=3, ge=1)
    notification_backoff_base_seconds: float = Field(default=2.0, gt=0)
    notification_backoff_max_seconds: float = Field(default=300.0, gt=0)
    notification_backoff_jitter_seconds: float = Field(default=1.0, ge=0)

    # --- Real-time (prompt §20-§23) ---
    # "memory" = single-process in-memory manager (dev/tests). "redis" enables
    # cross-instance pub/sub and makes Redis a readiness dependency (prompt §52).
    realtime_provider: str = Field(default="memory")
    redis_url: str = Field(default="", alias="REDIS_URL")
    websocket_heartbeat_seconds: float = Field(default=30.0, gt=0)

    # Default notification language + fallback (prompt §26).
    notification_default_language: str = Field(default="en")

    @property
    def redis_required(self) -> bool:
        """Redis is a required dependency only when realtime uses it."""
        return self.realtime_provider.lower() == "redis"

    @property
    def document_max_size_bytes(self) -> int:
        return self.document_max_size_mb * 1024 * 1024

    @property
    def cors_origins(self) -> list[str]:
        """Allowed CORS origins parsed from the comma-separated env value."""
        return [o.strip() for o in self.cors_origins_raw.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    def validate_production_config(self) -> None:
        """Enforce strict production configuration boundaries (Prompt §5, §63, §64).

        Fails startup if development defaults or insecure providers are detected in production.
        """
        if not self.is_production:
            return

        errors: list[str] = []

        if self.jwt_secret_key.startswith("dev-only") or len(self.jwt_secret_key) < 32:
            errors.append("JWT_SECRET_KEY is insecure or using development default.")

        if "*" in self.cors_origins:
            errors.append("CORS_ORIGINS contains wildcard '*' which is forbidden in production.")

        if self.storage_provider.lower() == "local":
            errors.append("STORAGE_PROVIDER='local' is forbidden in production; must use 's3'.")

        if self.ocr_provider.lower() == "test":
            errors.append("OCR_PROVIDER='test' (mock provider) is forbidden in production.")

        if self.submission_provider.lower() == "mock":
            errors.append("SUBMISSION_PROVIDER='mock' is forbidden in production.")

        if self.otp_provider.lower() == "test":
            errors.append("OTP_PROVIDER='test' (fixed OTP code) is forbidden in production.")

        if errors:
            raise ValueError(
                "CRITICAL PRODUCTION CONFIGURATION FAILURE:\n - " + "\n - ".join(errors)
            )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings accessor (single instance per process)."""
    return Settings()
