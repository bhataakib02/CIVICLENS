"""Robots.txt parser and crawl policy validator (prompt §8).

Enforces robots.txt guidelines and TOS boundaries without stealth scraping.
"""
from __future__ import annotations

from urllib.parse import urlparse
import robotparser

from app.core.logging import get_logger

logger = get_logger("civiclens.opportunities.robots")


class RobotsPolicyChecker:
    """Utility to fetch, parse, and verify domain robots.txt rules."""

    def __init__(self, user_agent: str = "CivicLens-OpportunityCrawler/1.0") -> None:
        self.user_agent = user_agent
        self._parsers: dict[str, robotparser.RobotFileParser] = {}

    def is_allowed(self, url: str, robots_txt_content: str | None = None) -> bool:
        """Check if a target URL is allowed under the domain's robots.txt rules."""
        parsed = urlparse(url)
        domain = parsed.hostname or ""
        if not domain:
            return False

        parser = self._parsers.get(domain)
        if not parser:
            parser = robotparser.RobotFileParser()
            if robots_txt_content:
                parser.parse(robots_txt_content.splitlines())
            else:
                robots_url = f"{parsed.scheme}://{domain}/robots.txt"
                parser.set_url(robots_url)
                try:
                    parser.read()
                except Exception as exc:
                    logger.warning("robots_fetch_warning", extra={"domain": domain, "error": str(exc)})
                    # Allow crawling if robots.txt does not exist or fails to fetch unless explicitly blocked
                    return True
            self._parsers[domain] = parser

        allowed = parser.can_fetch(self.user_agent, url)
        if not allowed:
            logger.info("robots_disallowed", extra={"url": url, "user_agent": self.user_agent})
        return allowed
