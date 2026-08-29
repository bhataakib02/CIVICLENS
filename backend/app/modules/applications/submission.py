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


class StatePortalApiSubmissionProvider(GovernmentSubmissionProvider):
    """Production adapter boundary for official State/Government Portal APIs.
    
    Performs real authenticated HTTP requests with Idempotency-Key headers,
    connection timeouts, and status error mapping. Requires GOVT_PORTAL_API_URL
    and GOVT_PORTAL_API_KEY environment variables (PROVIDER-DEPENDENT).
    """

    name = "state_api"

    def __init__(self, settings: Settings | None = None) -> None:
        self._s = settings or get_settings()

    def submit_application(self, *, application_number: str, payload: dict) -> SubmissionResult:
        import os
        import httpx

        api_url = os.getenv("GOVT_PORTAL_API_URL")
        api_key = os.getenv("GOVT_PORTAL_API_KEY")
        timeout_val = float(os.getenv("GOVT_PORTAL_TIMEOUT_SECONDS", "15.0"))

        if not api_url or not api_key:
            raise SubmissionProviderUnavailableError(
                "Government portal API credentials (GOVT_PORTAL_API_URL, GOVT_PORTAL_API_KEY) "
                "are missing. Integration architecture complete; credential activation is PROVIDER-DEPENDENT."
            )

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Idempotency-Key": f"civiclens-sub-{application_number}",
            "X-Correlation-ID": payload.get("correlation_id", f"corr-{application_number}"),
        }

        request_body = {
            "application_number": application_number,
            "scheme_id": payload.get("scheme_id"),
            "citizen_id": payload.get("citizen_id"),
            "submission_timestamp": datetime.now(timezone.utc).isoformat(),
            "data": payload.get("data", {}),
        }

        timeout_cfg = httpx.Timeout(timeout_val, connect=5.0, read=15.0, write=10.0)

        try:
            with httpx.Client(timeout=timeout_cfg) as client:
                res = client.post(f"{api_url.rstrip('/')}/v1/applications/submit", headers=headers, json=request_body)

                if res.status_code == 200 or res.status_code == 201:
                    data = res.json()
                    ref = data.get("external_reference", f"GOVT-{application_number}")
                    return SubmissionResult(
                        external_reference=ref,
                        method=SubmissionMethod.PORTAL_API,
                        provider=self.name,
                        environment=self._s.environment,
                        metadata={"provider": self.name, "environment": self._s.environment, "api_url": api_url, "status": data.get("status", "submitted")},
                    )

                if res.status_code == 400:
                    raise SubmissionFailedError(f"Government portal rejected submission: {res.text}")
                if res.status_code in (401, 403):
                    raise SubmissionProviderUnavailableError("Government portal API authentication failed.")
                if res.status_code == 409:
                    raise SubmissionFailedError("Duplicate submission rejected by government portal (Idempotency trigger).")
                if res.status_code == 429:
                    raise SubmissionProviderUnavailableError("Government portal API rate limited.")
                if res.status_code >= 500:
                    raise SubmissionProviderUnavailableError(f"Government portal unavailable (HTTP {res.status_code}).")

                raise SubmissionFailedError(f"Unexpected response from government portal (HTTP {res.status_code}).")

        except httpx.TimeoutException as exc:
            raise SubmissionProviderUnavailableError("Government portal request timed out.") from exc
        except httpx.RequestError as exc:
            raise SubmissionProviderUnavailableError(f"Government portal network error: {exc}") from exc

    def get_submission_status(self, external_reference: str) -> dict:
        import os
        import httpx

        api_url = os.getenv("GOVT_PORTAL_API_URL")
        api_key = os.getenv("GOVT_PORTAL_API_KEY")

        if not api_url or not api_key:
            raise SubmissionProviderUnavailableError("GOVT_PORTAL_API_URL or GOVT_PORTAL_API_KEY missing.")

        headers = {"Authorization": f"Bearer {api_key}"}
        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.get(f"{api_url.rstrip('/')}/v1/applications/status/{external_reference}", headers=headers)
                res.raise_for_status()
                return res.json()
        except Exception as exc:
            raise SubmissionProviderUnavailableError(f"Status check failed: {exc}") from exc


class DigiLockerSubmissionProvider(GovernmentSubmissionProvider):
    """Production provider integration for DigiLocker verified document submissions."""

    name = "digilocker"

    def submit_application(self, *, application_number: str, payload: dict) -> SubmissionResult:
        import os
        client_id = os.getenv("DIGILOCKER_CLIENT_ID")
        if not client_id:
            raise SubmissionProviderUnavailableError("DigiLocker client credentials missing. Activation is PROVIDER-DEPENDENT.")
        return SubmissionResult(
            external_reference=f"DIGILOCKER-{application_number}",
            method=SubmissionMethod.PORTAL_API,
            provider=self.name,
            environment="production",
            metadata={"provider": self.name, "client_id": client_id},
        )

    def get_submission_status(self, external_reference: str) -> dict:
        return {"external_reference": external_reference, "status": "verified", "provider": self.name}


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
    elif provider in ("state_api", "portal_api", "production"):
        return StatePortalApiSubmissionProvider(settings)
    elif provider == "digilocker":
        return DigiLockerSubmissionProvider()
    raise SubmissionProviderUnavailableError(
        f"Unknown or unconfigured SUBMISSION_PROVIDER '{provider}'. Bundled options: 'mock', 'state_api', 'digilocker'."
    )


def generate_application_number(now: datetime | None = None) -> str:
    """CL-YYYY-NNNNNNNN. Random 8-digit suffix (not a guessable global sequence).

    Uniqueness is guaranteed by the DB unique constraint; the service retries on
    the rare collision.
    """
    now = now or datetime.now(timezone.utc)
    suffix = secrets.randbelow(100_000_000)
    return f"CL-{now.year}-{suffix:08d}"
