"""Application link extraction, classification, and validation (prompt §17, §18, §19, §20, §23, §44).

SSRF-safe verification of external URLs with HTTP status checks, redirect chain verification, open redirect guards, and official source precedence.
"""
from __future__ import annotations

import re
from urllib.parse import urlparse
from dataclasses import dataclass
from typing import List, Optional

from app.core.config import get_settings
from app.modules.knowledge.ingestion.fetcher import SafeFetcher, SsrfError
from app.models.enums import OpportunityLinkType


@dataclass
class VerifiedLinkResult:
    url: str
    domain: str
    link_type: OpportunityLinkType
    is_official: bool
    is_valid: bool
    http_status: Optional[int]
    redirect_target: Optional[str]
    error_message: Optional[str] = None


class LinkValidator:
    """Validates external application links and checks safety."""

    def __init__(self, fetcher: SafeFetcher | None = None) -> None:
        self.fetcher = fetcher or SafeFetcher()

    @staticmethod
    def classify_link(url: str, text: str = "") -> OpportunityLinkType:
        combined = f"{url} {text}".lower()
        if "notification" in combined or "advt" in combined or "circular" in combined:
            return OpportunityLinkType.NOTIFICATION
        elif "apply" in combined or "registration" in combined or "form" in combined:
            return OpportunityLinkType.APPLY
        elif "login" in combined or "signin" in combined:
            return OpportunityLinkType.LOGIN
        elif "download" in combined or ".pdf" in combined:
            return OpportunityLinkType.DOWNLOAD
        elif "result" in combined or "merit" in combined:
            return OpportunityLinkType.RESULT
        elif "syllabus" in combined or "pattern" in combined:
            return OpportunityLinkType.SYLLABUS
        return OpportunityLinkType.APPLY

    @staticmethod
    def is_official_domain(url: str, source_domain: str) -> bool:
        """Verify if target URL domain matches official source or government portal."""
        target_domain = urlparse(url).hostname or ""
        source_domain = source_domain.lower().strip()
        target_domain = target_domain.lower().strip()

        if target_domain == source_domain or target_domain.endswith("." + source_domain):
            return True
        if target_domain.endswith(".gov.in") or target_domain.endswith(".nic.in") or target_domain.endswith(".edu.in"):
            return True
        return False

    def validate_link(self, url: str, source_domain: str) -> VerifiedLinkResult:
        parsed = urlparse(url)
        domain = parsed.hostname or ""
        is_official = self.is_official_domain(url, source_domain)
        link_type = self.classify_link(url)

        if not domain:
            return VerifiedLinkResult(
                url=url,
                domain=domain,
                link_type=link_type,
                is_official=False,
                is_valid=False,
                http_status=None,
                redirect_target=None,
                error_message="Invalid URL structure",
            )

        try:
            res = self.fetcher.fetch(url)
            is_valid = res.status_code < 400
            return VerifiedLinkResult(
                url=url,
                domain=domain,
                link_type=link_type,
                is_official=is_official,
                is_valid=is_valid,
                http_status=res.status_code,
                redirect_target=res.final_url if res.final_url != url else None,
                error_message=None if is_valid else f"HTTP {res.status_code}",
            )
        except SsrfError as exc:
            return VerifiedLinkResult(
                url=url,
                domain=domain,
                link_type=link_type,
                is_official=False,
                is_valid=False,
                http_status=403,
                redirect_target=None,
                error_message=f"SSRF Guard: {exc}",
            )
        except Exception as exc:
            return VerifiedLinkResult(
                url=url,
                domain=domain,
                link_type=link_type,
                is_official=is_official,
                is_valid=False,
                http_status=None,
                redirect_target=None,
                error_message=str(exc)[:250],
            )
