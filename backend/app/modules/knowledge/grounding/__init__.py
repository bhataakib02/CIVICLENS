"""Grounding: context assembly, citations, and injection/secret guardrails."""
from app.modules.knowledge.grounding.citations import (
    Citation,
    citations_for_indices,
    extract_evidence_refs,
)
from app.modules.knowledge.grounding.context import build_grounding_context
from app.modules.knowledge.grounding.guardrails import (
    contains_injection,
    filter_secrets,
    neutralize_injection,
    sanitize_evidence_text,
)

__all__ = [
    "build_grounding_context",
    "Citation",
    "citations_for_indices",
    "extract_evidence_refs",
    "contains_injection",
    "filter_secrets",
    "neutralize_injection",
    "sanitize_evidence_text",
]
