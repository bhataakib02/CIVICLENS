"""Government submission provider abstraction + application number (prompt §20, §21, §28, §57).

CivicLens does NOT ship a real government portal integration. The abstraction
lets a real provider be configured; the bundled MockSubmissionProvider is
clearly NON-PRODUCTION (its results carry environment=development, provider=mock)
and generates DETERMINISTIC test references. The factory FAILS CLOSED: selecting
the mock provider while ENVIRONMENT=production raises.

Application numbers are human-readable, non-sensitive references: CL-YYYY-NNNNNNNN
(no Aadhaar/phone/email). The numeric suffix is derived from a random component
so it is not a guessable global sequence.
"""
from __future__ import annotations

import secrets
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone

from app.core.config import Settings, get_settings
from app.models.enums import SubmissionMethod


class SubmissionProviderError(Exception):
    pass


class SubmissionProviderUnavailableError(SubmissionProviderError):
    pass


class SubmissionFailedError(SubmissionProviderError):
    """The external provider rejected/failed the submission (transient or permanent)."""


@dataclass
class SubmissionResult:
    external_reference: str
    method: SubmissionMethod
    provider: str
    environment: str
    metadata: dict  # non-sensitive only


class GovernmentSubmissionProvider(ABC):
    name = "abstract"

    @abstractmethod
    def submit_application(self, *, application_number: str, payload: dict) -> SubmissionResult:  # pragma: no cover
        ...

    @abstractmethod
    def get_submission_status(self, external_reference: str) -> dict:  # pragma: no cover
        ...


class MockSubmissionProvider(GovernmentSubmissionProvider):
    """NON-PRODUCTION mock. Generates deterministic test references; performs no
    real network call. Clearly labels itself provider=mock, environment=development."""

    name = "mock"

    def __init__(self, settings: Settings | None = None) -> None:
        self._s = settings or get_settings()

    def submit_application(self, *, application_number: str, payload: dict) -> SubmissionResult:
        # Deterministic reference derived from the application number (test-stable).
        ref = f"MOCK-{application_number}"
        # Allow tests to simulate a provider failure via a payload flag.
        if payload.get("_simulate_provider_failure"):
            raise SubmissionFailedError("Mock provider simulated failure.")
        return SubmissionResult(
            external_reference=ref,
            method=SubmissionMethod.MOCK,
            provider=self.name,
            environment=self._s.environment,
            metadata={"provider": "mock", "environment": self._s.environment,
                      "note": "NON-PRODUCTION mock submission; no government portal was called."},
        )

    def get_submission_status(self, external_reference: str) -> dict:
        return {"external_reference": external_reference, "status": "acknowledged",
                "provider": "mock", "environment": self._s.environment}


def get_submission_provider(settings: Settings | None = None) -> GovernmentSubmissionProvider:
    settings = settings or get_settings()
    provider = settings.submission_provider.lower()
    if provider == "mock":
        if settings.is_production:
            raise SubmissionProviderUnavailableError(
                "The mock submission provider must not be used in production. "
                "Configure a real SUBMISSION_PROVIDER integration."
            )
        return MockSubmissionProvider(settings)
    # A real provider (e.g. a state portal API client) would be constructed here.
    raise SubmissionProviderUnavailableError(
        f"Unknown or unconfigured SUBMISSION_PROVIDER '{provider}'. Bundled option: 'mock' (non-production)."
    )


def generate_application_number(now: datetime | None = None) -> str:
    """CL-YYYY-NNNNNNNN. Random 8-digit suffix (not a guessable global sequence).

    Uniqueness is guaranteed by the DB unique constraint; the service retries on
    the rare collision.
    """
    now = now or datetime.now(timezone.utc)
    suffix = secrets.randbelow(100_000_000)
    return f"CL-{now.year}-{suffix:08d}"
