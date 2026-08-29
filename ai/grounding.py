"""Citation verification and context grounding.

Re-exports the canonical grounding subsystem from the backend. This module
handles context assembly for the LLM, citation extraction from generated
responses, and guardrails (injection detection, secret filtering).

See ``docs/ai/hallucination-controls.md``.
"""

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
    # Context assembly
    "build_grounding_context",
    # Citations
    "Citation",
    "citations_for_indices",
    "extract_evidence_refs",
    # Guardrails
    "contains_injection",
    "filter_secrets",
    "neutralize_injection",
    "sanitize_evidence_text",
]
