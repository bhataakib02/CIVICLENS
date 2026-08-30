"""Pre-enablement source validation pipeline (prompt Phase 4, Phase 5).

Validates candidate crawl targets via DNS, HTTPS, domain association, robots.txt, connector test, and opportunity detection.
"""
from __future__ import annotations

import re
import socket
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

from app.core.logging import get_logger
from app.modules.knowledge.ingestion.fetcher import SafeFetcher, SsrfError
from app.modules.opportunities.ingestion.connectors.base import get_connector_for_source
from app.modules.opportunities.ingestion.extractor import OpportunityExtractor
from app.modules.opportunities.ingestion.robots import RobotsPolicyChecker

logger = get_logger("civiclens.opportunities.validator")


@dataclass
class SourceValidationResult:
    url: str
    domain: str
    domain_valid: bool
    dns_valid: bool
    https_valid: bool
    robots_allowed: bool
    connector: str
    sample_pages: int
    opportunity_detected: bool
    extraction_possible: bool
    recommended_authority: str
    recommended_category: str
    health_status: str
    error_message: Optional[str] = None


class SourceValidator:
    """Automated pre-enablement validation engine for crawl targets."""

    def __init__(self, fetcher: SafeFetcher | None = None) -> None:
        self.fetcher = fetcher or SafeFetcher()
        self.robots_checker = RobotsPolicyChecker()
        self.extractor = OpportunityExtractor()

    def validate_source(self, url: str, domain: Optional[str] = None) -> SourceValidationResult:
        parsed = urlparse(url)
        target_domain = domain or parsed.hostname or ""

        if not target_domain or "." not in target_domain:
            return SourceValidationResult(
                url=url,
                domain=target_domain,
                domain_valid=False,
                dns_valid=False,
                https_valid=False,
                robots_allowed=False,
                connector="HTML",
                sample_pages=0,
                opportunity_detected=False,
                extraction_possible=False,
                recommended_authority="UNVERIFIED",
                recommended_category="OTHER",
                health_status="FAILED",
                error_message="Invalid URL structure or domain missing",
            )

        # 1. DNS Resolution Check
        try:
            socket.gethostbyname(target_domain)
            dns_valid = True
        except Exception as exc:
            return SourceValidationResult(
                url=url,
                domain=target_domain,
                domain_valid=True,
                dns_valid=False,
                https_valid=False,
                robots_allowed=False,
                connector="HTML",
                sample_pages=0,
                opportunity_detected=False,
                extraction_possible=False,
                recommended_authority="UNVERIFIED",
                recommended_category="OTHER",
                health_status="FAILED",
                error_message=f"DNS resolution failed: {exc}",
            )

        # 2. HTTPS Connectivity Check
        try:
            res = self.fetcher.fetch(url)
            https_valid = res.status_code < 400
        except SsrfError as exc:
            return SourceValidationResult(
                url=url,
                domain=target_domain,
                domain_valid=True,
                dns_valid=True,
                https_valid=False,
                robots_allowed=False,
                connector="HTML",
                sample_pages=0,
                opportunity_detected=False,
                extraction_possible=False,
                recommended_authority="UNVERIFIED",
                recommended_category="OTHER",
                health_status="BLOCKED",
                error_message=f"SSRF policy blocked URL: {exc}",
            )
        except Exception as exc:
            return SourceValidationResult(
                url=url,
                domain=target_domain,
                domain_valid=True,
                dns_valid=True,
                https_valid=False,
                robots_allowed=False,
                connector="HTML",
                sample_pages=0,
                opportunity_detected=False,
                extraction_possible=False,
                recommended_authority="UNVERIFIED",
                recommended_category="OTHER",
                health_status="DEGRADED",
                error_message=f"HTTPS fetch failed: {exc}",
            )

        # 3. Robots.txt Compliance Check
        robots_allowed = self.robots_checker.is_allowed(url)
        if not robots_allowed:
            return SourceValidationResult(
                url=url,
                domain=target_domain,
                domain_valid=True,
                dns_valid=True,
                https_valid=True,
                robots_allowed=False,
                connector="HTML",
                sample_pages=0,
                opportunity_detected=False,
                extraction_possible=False,
                recommended_authority="UNVERIFIED",
                recommended_category="OTHER",
                health_status="BLOCKED",
                error_message="Disallowed by domain robots.txt policy",
            )

        # 4. Connector Test & Sample Item Extraction
        connector_obj = get_connector_for_source(base_url=url, fetcher=self.fetcher)
        connector_name = connector_obj.__class__.__name__.replace("Connector", "").upper()

        sample_pages = 0
        opportunity_detected = False
        extraction_possible = False
        detected_type = "OTHER"

        try:
            docs = connector_obj.fetch_items(url)
            sample_pages = len(docs)
            for doc in docs[:3]:
                extracted = self.extractor.extract(doc.content, doc.url, default_org=target_domain)
                if extracted.title and extracted.organization:
                    opportunity_detected = True
                    extraction_possible = True
                    detected_type = extracted.type
                    break
        except Exception as exc:
            logger.warning("connector_test_warning", extra={"url": url, "error": str(exc)})

        is_official = any(target_domain.endswith(tld) for tld in (".gov.in", ".nic.in", ".edu.in", ".res.in", ".ac.in"))
        recommended_authority = "OFFICIAL" if is_official else "KNOWN_PRIVATE"

        health_status = "HEALTHY" if (https_valid and robots_allowed and sample_pages > 0) else "DEGRADED"

        return SourceValidationResult(
            url=url,
            domain=target_domain,
            domain_valid=True,
            dns_valid=dns_valid,
            https_valid=https_valid,
            robots_allowed=robots_allowed,
            connector=connector_name,
            sample_pages=sample_pages,
            opportunity_detected=opportunity_detected,
            extraction_possible=extraction_possible,
            recommended_authority=recommended_authority,
            recommended_category=detected_type,
            health_status=health_status,
            error_message=None if health_status == "HEALTHY" else "Partial content or limited structure detected",
        )
