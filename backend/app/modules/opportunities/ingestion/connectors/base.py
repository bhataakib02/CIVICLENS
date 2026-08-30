"""Connector interface and concrete implementations (prompt §7).

Implements RSSConnector, SitemapConnector, HTMLConnector, JSONConnector, APIConnector, PDFConnector.
"""
from __future__ import annotations

import abc
import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Any, List

from app.modules.knowledge.ingestion.fetcher import SafeFetcher, FetchResult


@dataclass
class RawOpportunityDocument:
    url: str
    content: str
    content_type: str
    source_identifier: str | None = None
    retrieved_at: float = 0.0


class BaseOpportunityConnector(abc.ABC):
    """Abstract base class for all opportunity connectors."""

    def __init__(self, fetcher: SafeFetcher | None = None) -> None:
        self.fetcher = fetcher or SafeFetcher()

    @abc.abstractmethod
    def fetch_items(self, base_url: str) -> List[RawOpportunityDocument]:
        """Fetch raw documents from the source."""
        pass


class HTMLConnector(BaseOpportunityConnector):
    """HTML page fetcher for direct web pages with candidate link discovery (prompt §7, §11)."""

    OPPORTUNITY_PATH_PATTERNS = [
        r"/jobs?",
        r"/careers?",
        r"/recruitments?",
        r"/vacanc(?:y|ies)",
        r"/notifications?",
        r"/scholarships?",
        r"/internships?",
        r"/apprenticeships?",
        r"/fellowships?",
        r"/schemes?",
        r"/benefits?",
        r"/grants?",
        r"/trainings?",
        r"/admissions?",
    ]

    def fetch_items(self, base_url: str) -> List[RawOpportunityDocument]:
        import re
        from urllib.parse import urljoin, urlparse

        res: FetchResult = self.fetcher.fetch(base_url)
        content_str = res.content.decode("utf-8", errors="ignore")
        docs = [
            RawOpportunityDocument(
                url=res.final_url,
                content=content_str,
                content_type=res.content_type,
                source_identifier=res.final_url,
                retrieved_at=res.retrieved_at,
            )
        ]

        # Candidate subpage link discovery
        base_domain = urlparse(res.final_url).hostname or ""
        hrefs = re.findall(r'href=["\']([^"\']+)["\']', content_str, re.IGNORECASE)
        candidate_urls = []
        for href in hrefs:
            abs_url = urljoin(res.final_url, href)
            parsed = urlparse(abs_url)
            if parsed.hostname == base_domain:
                path = parsed.path.lower()
                for pat in self.OPPORTUNITY_PATH_PATTERNS:
                    if re.search(pat, path):
                        if abs_url not in candidate_urls and abs_url != res.final_url:
                            candidate_urls.append(abs_url)
                        break

        # Limit candidate crawl pass to top 5 discovered links per pass
        for cand_url in candidate_urls[:5]:
            try:
                sub_res = self.fetcher.fetch(cand_url)
                sub_content = sub_res.content.decode("utf-8", errors="ignore")
                docs.append(
                    RawOpportunityDocument(
                        url=sub_res.final_url,
                        content=sub_content,
                        content_type=sub_res.content_type,
                        source_identifier=sub_res.final_url,
                        retrieved_at=sub_res.retrieved_at,
                    )
                )
            except Exception:
                continue

        return docs


class RSSConnector(BaseOpportunityConnector):
    """RSS / Atom feed connector."""

    def fetch_items(self, base_url: str) -> List[RawOpportunityDocument]:
        res = self.fetcher.fetch(base_url)
        content_str = res.content.decode("utf-8", errors="ignore")
        documents = []

        try:
            root = ET.fromstring(content_str)
            # RSS channel/item
            for item in root.findall(".//item"):
                title = item.findtext("title") or ""
                link = item.findtext("link") or base_url
                desc = item.findtext("description") or ""
                guid = item.findtext("guid") or link

                item_content = f"Title: {title}\nLink: {link}\nDescription: {desc}"
                documents.append(
                    RawOpportunityDocument(
                        url=link,
                        content=item_content,
                        content_type="text/html",
                        source_identifier=guid,
                        retrieved_at=res.retrieved_at,
                    )
                )
        except Exception:
            # Fallback treat as single document
            documents.append(
                RawOpportunityDocument(
                    url=res.final_url,
                    content=content_str,
                    content_type="text/html",
                    source_identifier=base_url,
                    retrieved_at=res.retrieved_at,
                )
            )
        return documents


class SitemapConnector(BaseOpportunityConnector):
    """XML Sitemap connector."""

    def fetch_items(self, base_url: str) -> List[RawOpportunityDocument]:
        res = self.fetcher.fetch(base_url)
        content_str = res.content.decode("utf-8", errors="ignore")
        urls = []

        try:
            root = ET.fromstring(content_str)
            for loc in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc"):
                if loc.text:
                    urls.append(loc.text.strip())
        except Exception:
            urls = [base_url]

        documents = []
        for url in urls[:10]:  # Limit top urls per crawl pass
            try:
                sub_res = self.fetcher.fetch(url)
                documents.append(
                    RawOpportunityDocument(
                        url=sub_res.final_url,
                        content=sub_res.content.decode("utf-8", errors="ignore"),
                        content_type=sub_res.content_type,
                        source_identifier=sub_res.final_url,
                        retrieved_at=sub_res.retrieved_at,
                    )
                )
            except Exception:
                continue
        return documents if documents else [
            RawOpportunityDocument(
                url=res.final_url,
                content=content_str,
                content_type=res.content_type,
                source_identifier=res.final_url,
                retrieved_at=res.retrieved_at,
            )
        ]


class JSONConnector(BaseOpportunityConnector):
    """JSON feed / static payload connector."""

    def fetch_items(self, base_url: str) -> List[RawOpportunityDocument]:
        res = self.fetcher.fetch(base_url)
        content_str = res.content.decode("utf-8", errors="ignore")
        documents = []

        try:
            data = json.loads(content_str)
            items = data if isinstance(data, list) else data.get("items", [data])
            for idx, item in enumerate(items):
                item_url = item.get("url") or item.get("link") or f"{base_url}#{idx}"
                documents.append(
                    RawOpportunityDocument(
                        url=item_url,
                        content=json.dumps(item),
                        content_type="application/json",
                        source_identifier=str(item.get("id") or item_url),
                        retrieved_at=res.retrieved_at,
                    )
                )
        except Exception:
            documents.append(
                RawOpportunityDocument(
                    url=res.final_url,
                    content=content_str,
                    content_type="application/json",
                    source_identifier=base_url,
                    retrieved_at=res.retrieved_at,
                )
            )
        return documents


class APIConnector(JSONConnector):
    """REST API endpoint connector."""

    pass


class PDFConnector(BaseOpportunityConnector):
    """PDF Document connector with text extraction (prompt §12)."""

    def fetch_items(self, base_url: str) -> List[RawOpportunityDocument]:
        res = self.fetcher.fetch(base_url)
        extracted_text = ""

        try:
            import io
            import pypdf

            reader = pypdf.PdfReader(io.BytesIO(res.content))
            pages_text = []
            for page in reader.pages:
                txt = page.extract_text()
                if txt:
                    pages_text.append(txt)
            extracted_text = "\n".join(pages_text)
        except Exception:
            pass

        if not extracted_text:
            import re

            decoded = res.content.decode("latin-1", errors="ignore")
            # Strip non-printable binary bytes
            extracted_text = re.sub(r"[^\x20-\x7E\n\r\t]", " ", decoded)

        content_str = extracted_text.strip() or f"PDF Document retrieved from {base_url} (size: {len(res.content)} bytes)"
        return [
            RawOpportunityDocument(
                url=res.final_url,
                content=content_str,
                content_type="application/pdf",
                source_identifier=res.final_url,
                retrieved_at=res.retrieved_at,
            )
        ]


def get_connector_for_source(
    crawl_policy: dict | None = None,
    source_type: str | None = None,
    base_url: str = "",
    fetcher: SafeFetcher | None = None,
) -> BaseOpportunityConnector:
    """Factory function for selecting the appropriate connector instance (prompt §6)."""
    crawl_policy = crawl_policy or {}
    conn_type = (crawl_policy.get("connector_type") or "").upper()
    url_lower = base_url.lower()

    if conn_type == "RSS" or "feed" in url_lower or "rss" in url_lower or url_lower.endswith(".xml"):
        return RSSConnector(fetcher=fetcher)
    elif conn_type == "SITEMAP" or "sitemap" in url_lower:
        return SitemapConnector(fetcher=fetcher)
    elif conn_type == "JSON" or conn_type == "API" or url_lower.endswith(".json"):
        return JSONConnector(fetcher=fetcher)
    elif conn_type == "PDF" or url_lower.endswith(".pdf"):
        return PDFConnector(fetcher=fetcher)
    return HTMLConnector(fetcher=fetcher)

