"""SSRF-safe HTTP fetcher (prompt §7, threat-model.md, ai-safety.md).

Only administrative ingestion may fetch URLs. Every fetch:
- resolves the hostname and rejects loopback / private / link-local / CGN /
  multicast / reserved / cloud-metadata addresses BEFORE connecting;
- re-validates the host on each redirect hop (redirects can point at internal
  IPs), with a redirect cap;
- enforces a connect/read timeout, a maximum response size (streamed, so a
  huge body can't exhaust memory), and an allowed content-type set;
- retries a bounded number of times on transient errors only.

Rejected inputs raise SsrfError (never fetched). This is a security boundary:
treat all URLs as untrusted (even admin-supplied).
"""
from __future__ import annotations

import ipaddress
import socket
import time
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger("civiclens.knowledge.fetcher")

# Cloud metadata endpoints (AWS/GCP/Azure/OpenStack) — always blocked.
_METADATA_HOSTS = {"169.254.169.254", "metadata.google.internal", "metadata"}

_ALLOWED_SCHEMES = {"http", "https"}
_ALLOWED_CONTENT_TYPES = (
    "text/html",
    "application/xhtml+xml",
    "application/pdf",
    "text/plain",
)
_TRANSIENT_STATUS = {429, 500, 502, 503, 504}


class FetchError(Exception):
    pass


class SsrfError(FetchError):
    """The URL/host is not permitted (SSRF guard)."""


class ContentTypeError(FetchError):
    pass


class ResponseTooLargeError(FetchError):
    pass


@dataclass
class FetchResult:
    url: str
    final_url: str
    status_code: int
    content_type: str
    content: bytes
    retrieved_at: float


def _is_blocked_ip(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return True  # unparseable => block
    return (
        addr.is_private
        or addr.is_loopback
        or addr.is_link_local
        or addr.is_multicast
        or addr.is_reserved
        or addr.is_unspecified
        or str(addr) in _METADATA_HOSTS
    )


def _resolve_and_validate_host(host: str, *, allow_private: bool) -> None:
    if not host:
        raise SsrfError("Missing host.")
    if host.lower() in _METADATA_HOSTS:
        raise SsrfError("Blocked metadata host.")
    if allow_private:
        return  # test-only escape hatch (settings.fetch_allow_private_ips)
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as exc:
        raise SsrfError(f"Host resolution failed for '{host}'.") from exc
    for info in infos:
        ip = info[4][0]
        if _is_blocked_ip(ip):
            raise SsrfError(f"Blocked address for host '{host}': {ip}")


def _validate_url(url: str, *, allow_private: bool) -> str:
    parsed = urlparse(url)
    if parsed.scheme.lower() not in _ALLOWED_SCHEMES:
        raise SsrfError(f"Scheme '{parsed.scheme}' not allowed.")
    host = parsed.hostname or ""
    _resolve_and_validate_host(host, allow_private=allow_private)
    return host


class SafeFetcher:
    def __init__(self, settings: Settings | None = None) -> None:
        self._s = settings or get_settings()

    def fetch(self, url: str) -> FetchResult:
        """Fetch a URL safely. Manual redirect handling re-validates each hop."""
        allow_private = self._s.fetch_allow_private_ips
        max_redirects = self._s.fetch_max_redirects
        attempts = self._s.fetch_max_retries + 1

        last_exc: Exception | None = None
        for attempt in range(1, attempts + 1):
            try:
                return self._fetch_once(url, allow_private=allow_private, max_redirects=max_redirects)
            except (SsrfError, ContentTypeError, ResponseTooLargeError):
                # Permanent errors — do not retry.
                raise
            except (httpx.TransportError, httpx.TimeoutException) as exc:
                last_exc = exc
                logger.warning(
                    "fetch_retry", extra={"attempt": attempt, "url_host": urlparse(url).hostname}
                )
                time.sleep(min(0.05 * attempt, 0.2))
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code in _TRANSIENT_STATUS and attempt < attempts:
                    last_exc = exc
                    time.sleep(min(0.05 * attempt, 0.2))
                    continue
                raise FetchError(f"HTTP {exc.response.status_code}") from exc
        raise FetchError(f"Fetch failed after {attempts} attempts.") from last_exc

    def _fetch_once(self, url: str, *, allow_private: bool, max_redirects: int) -> FetchResult:
        current = url
        for _hop in range(max_redirects + 1):
            _validate_url(current, allow_private=allow_private)
            with httpx.Client(
                follow_redirects=False,
                timeout=self._s.fetch_timeout_seconds,
                headers={"User-Agent": "CivicLens-Ingestion/1.0"},
            ) as client:
                with client.stream("GET", current) as resp:
                    if resp.is_redirect:
                        location = resp.headers.get("location")
                        if not location:
                            raise FetchError("Redirect without Location header.")
                        current = str(httpx.URL(current).join(location))
                        continue
                    resp.raise_for_status()
                    content_type = resp.headers.get("content-type", "").split(";")[0].strip().lower()
                    if content_type and not any(
                        content_type == ct for ct in _ALLOWED_CONTENT_TYPES
                    ):
                        raise ContentTypeError(f"Disallowed content-type '{content_type}'.")
                    body = self._read_capped(resp)
                    return FetchResult(
                        url=url,
                        final_url=current,
                        status_code=resp.status_code,
                        content_type=content_type or "application/octet-stream",
                        content=body,
                        retrieved_at=time.time(),
                    )
        raise FetchError("Too many redirects.")

    def _read_capped(self, resp: httpx.Response) -> bytes:
        max_bytes = self._s.fetch_max_bytes
        chunks: list[bytes] = []
        total = 0
        for chunk in resp.iter_bytes():
            total += len(chunk)
            if total > max_bytes:
                raise ResponseTooLargeError(f"Response exceeds {max_bytes} bytes.")
            chunks.append(chunk)
        return b"".join(chunks)
