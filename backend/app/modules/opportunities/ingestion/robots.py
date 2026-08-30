"""Robots.txt parser and crawl policy validator (prompt §8).

Enforces robots.txt guidelines and TOS boundaries without stealth scraping.
"""
from __future__ import annotations

from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

from app.core.logging import get_logger
from app.modules.knowledge.ingestion.fetcher import SafeFetcher

logger = get_logger("civiclens.opportunities.robots")


class RobotsPolicyChecker:
    """Utility to fetch, parse, and verify domain robots.txt rules."""

    def __init__(self, user_agent: str = "CivicLens-OpportunityCrawler/1.0", fetcher: SafeFetcher | None = None) -> None:
        self.user_agent = user_agent
        self.fetcher = fetcher or SafeFetcher()
        self._parsers: dict[str, RobotFileParser] = {}

    def is_allowed(self, url: str, robots_txt_content: str | None = None) -> bool:
        """Check if a target URL is allowed under the domain's robots.txt rules."""
        parsed = urlparse(url)
        domain = parsed.hostname or ""
        if not domain:
            return False

        parser = self._parsers.get(domain)
        if not parser:
            parser = RobotFileParser()
            if robots_txt_content is not None:
                parser.parse(robots_txt_content.splitlines())
            else:
                robots_url = f"{parsed.scheme or 'https'}://{domain}/robots.txt"
                try:
                    res = self.fetcher.fetch(robots_url)
                    text = res.content.decode("utf-8", errors="ignore")
                    if res.status_code == 200 and text and not text.strip().startswith("<"):
                        parser.parse(text.splitlines())
                    else:
                        # 404/403 or non-text content -> no restrictive robots rules published
                        parser.allow_all = True
                except Exception as exc:
                    logger.warning("robots_fetch_warning", extra={"domain": domain, "error": str(exc)})
                    parser.allow_all = True
            self._parsers[domain] = parser

        allowed = parser.can_fetch(self.user_agent, url) or parser.can_fetch("*", url)
        if not allowed and not getattr(parser, "allow_all", False):
            logger.info("robots_disallowed", extra={"url": url, "user_agent": self.user_agent})
            return False
        return True
