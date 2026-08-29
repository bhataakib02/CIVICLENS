"""Knowledge + assistant schemas (Pydantic v2).

Conform to openapi.yaml (KnowledgeSourceInput, AssistantResponse) and extend
deliberately (documented in openapi.yaml) for /knowledge/search,
/knowledge/sources (job), and /assistant/query.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ------------------------------ sources ------------------------------------- #
class KnowledgeSourceInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=512)
    url: str = Field(min_length=1)
    publisher: str = Field(min_length=1, max_length=255)
    scheme_id: uuid.UUID | None = None
    scheme_version_id: uuid.UUID | None = None
    published_date: datetime | None = None


class IngestionJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: str
    url: str
    knowledge_source_id: str | None = None
    attempts: int
    max_attempts: int
    error: str | None = None
    result: dict | None = None
    created_at: datetime


class KnowledgeSourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    url: str
    publisher: str
    source_type: str | None = None
    trust_level: str
    verification_status: str
    scheme_id: str | None = None
    created_at: datetime


class SourceVerifyInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    verification_status: str
    trust_level: str | None = None


# ------------------------------ search -------------------------------------- #
class KnowledgeSearchInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1)
    scheme_id: uuid.UUID | None = None
    scheme_version_id: uuid.UUID | None = None
    limit: int = Field(default=10, ge=1, le=50)


class SearchResultItem(BaseModel):
    chunk_id: str
    source_id: str
    content: str
    source_url: str
    page_number: int | None = None
    section: str | None = None
    score: float


# ------------------------------ assistant ----------------------------------- #
class AssistantQueryInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1)
    scheme_id: uuid.UUID | None = None
    scheme_version_id: uuid.UUID | None = None
    conversation_id: uuid.UUID | None = None


class CitationOut(BaseModel):
    source_id: str
    chunk_id: str
    source_url: str
    page_number: int | None = None
    section: str | None = None


class AssistantResponse(BaseModel):
    conversation_id: str
    answer: str
    citations: list[CitationOut]
    scheme_ids: list[str] = Field(default_factory=list)
    eligibility_tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    confidence: float
    grounded: bool
