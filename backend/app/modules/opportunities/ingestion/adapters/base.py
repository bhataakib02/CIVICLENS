"""Base interface for source-specific extraction adapters (prompt Phase 7)."""
from __future__ import annotations

import abc
from typing import List

from app.modules.opportunities.ingestion.extractor import OpportunityExtractionSchema


class BaseSourceAdapter(abc.ABC):
    """Abstract adapter interface for specialized portal structures."""

    @abc.abstractmethod
    def parse_opportunities(self, raw_content: str, source_url: str) -> List[OpportunityExtractionSchema]:
        """Extract structured opportunity schemas using domain-specific heuristics."""
        pass
