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
    """HTML page fetcher for direct web pages."""

    def fetch_items(self, base_url: str) -> List[RawOpportunityDocument]:
        res: FetchResult = self.fetcher.fetch(base_url)
        content_str = res.content.decode("utf-8", errors="ignore")
        return [
            RawOpportunityDocument(
                url=res.final_url,
                content=content_str,
                content_type=res.content_type,
                source_identifier=res.final_url,
                retrieved_at=res.retrieved_at,
            )
        ]


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
        return documents


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
    """PDF Document connector."""

    def fetch_items(self, base_url: str) -> List[RawOpportunityDocument]:
        res = self.fetcher.fetch(base_url)
        # Store PDF metadata / string snippet
        content_str = f"PDF Document retrieved from {base_url} (size: {len(res.content)} bytes)"
        return [
            RawOpportunityDocument(
                url=res.final_url,
                content=content_str,
                content_type="application/pdf",
                source_identifier=res.final_url,
                retrieved_at=res.retrieved_at,
            )
        ]
