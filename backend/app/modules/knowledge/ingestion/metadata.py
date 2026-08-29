"""Metadata extraction: content hashing + source-type + trust inference.

Trust policy (prompt §5, source-policy.md): trust is derived from the URL's
registrable domain against a DOCUMENTED, configurable policy — not a silent
hardcoded allowlist. The default policy treats Indian government domains
(*.gov.in, *.nic.in) and *.gov as OFFICIAL_GOVERNMENT; a PDF from such a host
as OFFICIAL_DOCUMENT; everything else UNVERIFIED (an admin may later promote a
source to VERIFIED_SECONDARY explicitly). Nothing is auto-marked verified.
"""
from __future__ import annotations

import hashlib
from urllib.parse import urlparse

from app.models.enums import SourceTrustLevel, SourceType

# Documented government domain suffixes. Extendable via policy/config; not a
# silent hardcoded gate — the rationale is recorded here and in source-policy.md.
_GOV_SUFFIXES = (".gov.in", ".nic.in", ".gov", ".gob", ".govt.nz", ".gouv.fr")
_OFFICIAL_PORTAL_HINTS = ("portal", "seva", "myscheme", "india.gov")


def content_hash(content: bytes | str) -> str:
    data = content.encode("utf-8") if isinstance(content, str) else content
    return hashlib.sha256(data).hexdigest()


def detect_source_type(content_type: str) -> SourceType:
    ct = (content_type or "").lower()
    if "pdf" in ct:
        return SourceType.PDF
    if "html" in ct or "xhtml" in ct:
        return SourceType.HTML
    return SourceType.TEXT


def _registrable_host(url: str) -> str:
    return (urlparse(url).hostname or "").lower()


def infer_trust_level(url: str, source_type: SourceType) -> SourceTrustLevel:
    host = _registrable_host(url)
    is_gov = any(host == suf.lstrip(".") or host.endswith(suf) for suf in _GOV_SUFFIXES)
    if is_gov:
        if source_type is SourceType.PDF:
            return SourceTrustLevel.OFFICIAL_DOCUMENT
        if any(hint in host for hint in _OFFICIAL_PORTAL_HINTS):
            return SourceTrustLevel.OFFICIAL_PORTAL
        return SourceTrustLevel.OFFICIAL_GOVERNMENT
    return SourceTrustLevel.UNVERIFIED
