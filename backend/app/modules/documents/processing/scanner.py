"""Malware scanner abstraction (prompt §14).

The application depends on MalwareScanner, never on a specific engine. A real
deployment would wire ClamAV or a cloud scanning API behind this interface.

Fail-closed: if no scanner is configured in production, the factory raises and
processing does NOT proceed (we never claim AV protection we don't have).

The bundled TestMalwareScanner is for dev/tests ONLY. It detects the standard
EICAR test signature and an in-repo sentinel so malicious-file handling can be
tested deterministically without a real engine.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.core.config import Settings, get_settings

# EICAR standard antivirus test string (not real malware).
_EICAR = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
# In-repo sentinel used by tests to simulate a detected threat.
_TEST_MALWARE_SENTINEL = b"CIVICLENS-TEST-MALWARE"


class ScannerUnavailableError(Exception):
    """No scanner configured (fail-closed in production)."""


@dataclass
class ScanResult:
    clean: bool
    signature: str | None = None
    scanner: str = "unknown"


class MalwareScanner(ABC):
    name = "abstract"

    @abstractmethod
    def scan(self, data: bytes) -> ScanResult:  # pragma: no cover - abstract
        ...


class TestMalwareScanner(MalwareScanner):
    """Deterministic scanner for dev/tests ONLY. NOT real antivirus."""

    name = "test"

    def scan(self, data: bytes) -> ScanResult:
        if _EICAR in data:
            return ScanResult(clean=False, signature="EICAR-Test-Signature", scanner=self.name)
        if _TEST_MALWARE_SENTINEL in data:
            return ScanResult(clean=False, signature="CivicLens-Test-Malware", scanner=self.name)
        return ScanResult(clean=True, scanner=self.name)


def get_malware_scanner(settings: Settings | None = None) -> MalwareScanner:
    settings = settings or get_settings()
    provider = settings.malware_scanner_provider.lower()
    if provider == "test":
        if settings.is_production:
            raise ScannerUnavailableError(
                "The test malware scanner must not be used in production. "
                "Configure a real MALWARE_SCANNER_PROVIDER."
            )
        return TestMalwareScanner()
    if provider in ("", "none"):
        # No scanner configured: fail closed (never process unscanned in prod).
        raise ScannerUnavailableError("No malware scanner configured.")
    raise ScannerUnavailableError(f"Unknown MALWARE_SCANNER_PROVIDER '{provider}'.")
