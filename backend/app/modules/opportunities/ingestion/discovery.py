"""Source Discovery Assistant workflow (prompt Part 10).

Automates host diagnostics, HTTPS validation, robots checking, connector candidate selection,
opportunity type inference, authority tier assignment, and sample opportunity extraction.
"""
from __future__ import annotations

import socket
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from app.modules.knowledge.ingestion.fetcher import SafeFetcher
from app.modules.opportunities.ingestion.robots import RobotsPolicyChecker
from app.modules.opportunities.ingestion.extractor import OpportunityExtractor
from app.modules.opportunities.schemas import SourceDiscoveryReport


STATE_KEYWORDS = {
    "maharashtra": "Maharashtra",
    "mpsc": "Maharashtra",
    "karnataka": "Karnataka",
    "kpsc": "Karnataka",
    "tamil": "Tamil Nadu",
    "tnpsc": "Tamil Nadu",
    "uttar": "Uttar Pradesh",
    "uppsc": "Uttar Pradesh",
    "bihar": "Bihar",
    "bpsc": "Bihar",
    "rajasthan": "Rajasthan",
    "rpsc": "Rajasthan",
    "bengal": "West Bengal",
    "wbpsc": "West Bengal",
    "psc.wb": "West Bengal",
    "gujarat": "Gujarat",
    "gpsc": "Gujarat",
    "kerala": "Kerala",
    "madhya": "Madhya Pradesh",
    "mppsc": "Madhya Pradesh",
    "telangana": "Telangana",
    "tspsc": "Telangana",
    "andhra": "Andhra Pradesh",
    "appsc": "Andhra Pradesh",
    "odisha": "Odisha",
    "opsc": "Odisha",
    "punjab": "Punjab",
    "ppsc": "Punjab",
    "haryana": "Haryana",
    "hpsc": "Haryana",
    "assam": "Assam",
    "apsc": "Assam",
    "jharkhand": "Jharkhand",
    "jpsc": "Jharkhand",
    "chhattisgarh": "Chhattisgarh",
    "cgpsc": "Chhattisgarh",
    "uttarakhand": "Uttarakhand",
    "ukpsc": "Uttarakhand",
    "himachal": "Himachal Pradesh",
    "hppsc": "Himachal Pradesh",
    "goa": "Goa",
    "delhi": "Delhi",
    "dsssb": "Delhi",
}


class SourceDiscoveryAssistant:
    """Admin-only workflow engine to discover and validate candidate sources."""

    def __init__(self, fetcher: Optional[SafeFetcher] = None) -> None:
        self.fetcher = fetcher or SafeFetcher()
        self.robots_checker = RobotsPolicyChecker()
        self.extractor = OpportunityExtractor()

    def discover(self, organization: str, domain: str) -> SourceDiscoveryReport:
        clean_domain = domain.lower().strip().replace("http://", "").replace("https://", "").split("/")[0]
        base_url = f"https://{clean_domain}"

        # 1. DNS Verification
        dns_status = "RESOLVED"
        try:
            socket.gethostbyname(clean_domain)
        except Exception:
            dns_status = "DNS_FAILED"

        # 2. HTTPS Fetch & Connectivity Test
        https_status = "UNREACHABLE"
        content_type = "text/html"
        raw_content = ""
        final_url = base_url

        if dns_status == "RESOLVED":
            try:
                res = self.fetcher.fetch(base_url)
                https_status = f"ACCESSIBLE_HTTP_{res.status_code}"
                content_type = res.content_type
                raw_content = res.content.decode("utf-8", errors="ignore")
                final_url = res.final_url
            except Exception as exc:
                https_status = f"HTTP_ERROR: {str(exc)[:100]}"

        # 3. Robots.txt Compliance Check
        robots_allowed = self.robots_checker.is_allowed(base_url)

        # 4. Connector Selection Inference
        candidate_connector = "HTML"
        if "rss" in content_type.lower() or "xml" in content_type.lower() or "feed" in clean_domain:
            candidate_connector = "RSS"
        elif "sitemap" in raw_content.lower() or "sitemap.xml" in base_url:
            candidate_connector = "SITEMAP"
        elif "json" in content_type.lower() or clean_domain.endswith(".json"):
            candidate_connector = "JSON"
        elif "pdf" in content_type.lower() or clean_domain.endswith(".pdf"):
            candidate_connector = "PDF"

        # 5. Candidate Opportunity Types Inference
        combined_text = (clean_domain + " " + raw_content[:10000]).lower()
        candidate_types: List[str] = []

        type_keywords = {
            "JOB": ["recruitment", "job", "vacancy", "post", "officer", "engineer"],
            "SCHOLARSHIP": ["scholarship", "financial assistance", "stipend", "grant for student"],
            "INTERNSHIP": ["internship", "intern", "trainee"],
            "APPRENTICESHIP": ["apprentice", "apprenticeship", "naps", "nats"],
            "FELLOWSHIP": ["fellowship", "research fellow", "postdoc", "jrf", "srf"],
            "GOVERNMENT_SCHEME": ["scheme", "yojana", "beneficiary", "myscheme"],
            "GRANT": ["grant", "funding", "birac", "serb", "research grant"],
            "TRAINING": ["training", "skill development", "nielit", "upskill"],
            "SKILL_PROGRAM": ["pmkvy", "skill program", "kaushal vikas", "nsdc"],
            "JOB_FAIR": ["job fair", "rozgar mela", "career fair"],
            "COMPETITION": ["hackathon", "competition", "contest", "challenge", "sih"],
            "ADMISSION": ["admission", "cuet", "entrance exam", "nta"],
        }

        for opp_type, keywords in type_keywords.items():
            if any(kw in combined_text for kw in keywords):
                candidate_types.append(opp_type)
        if not candidate_types:
            candidate_types = ["JOB"]

        # 6. Authority Tier Assignment
        if any(clean_domain.endswith(tld) for tld in [".gov.in", ".nic.in", ".ac.in", ".edu.in", ".gov", ".mil"]):
            suggested_authority = "OFFICIAL"
        elif any(clean_domain.endswith(tld) for tld in [".com", ".in", ".org", ".co", ".net"]):
            suggested_authority = "KNOWN_PRIVATE"
        else:
            suggested_authority = "UNVERIFIED"

        # 7. Geographic Scope & State Assignment
        suggested_scope = "NATIONAL"
        suggested_state: Optional[str] = None

        for kw, state_name in STATE_KEYWORDS.items():
            if kw in combined_text or kw in clean_domain:
                suggested_scope = "STATE"
                suggested_state = state_name
                break

        # 8. Sample Opportunity Extraction
        sample_opp: Optional[Dict[str, Any]] = None
        if raw_content:
            extracted = self.extractor.extract(raw_content, final_url, default_org=organization)
            sample_opp = extracted.model_dump()

        return SourceDiscoveryReport(
            organization=organization,
            domain=clean_domain,
            base_url=final_url,
            dns_status=dns_status,
            https_status=https_status,
            robots_allowed=robots_allowed,
            candidate_connector=candidate_connector,
            candidate_opportunity_types=candidate_types,
            suggested_authority_level=suggested_authority,
            suggested_geographic_scope=suggested_scope,
            suggested_state=suggested_state,
            sample_opportunity=sample_opp,
            is_approved_for_onboarding=False,
        )
