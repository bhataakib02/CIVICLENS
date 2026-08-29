"""Structured LLM output schema + hallucination guard (prompt §25, §26).

LLMAnswer is the validated internal structure the model must return. The
hallucination guard checks the model output against the retrieved evidence:
- every cited evidence_index must exist in the provided markers;
- if the answer makes factual claims but cites no valid evidence, it is
  downgraded to the safe insufficient-evidence response.

The guard PREFERS "I don't have enough verified information." over an
unsupported confident answer.
"""
from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, Field

from app.modules.knowledge.grounding.citations import Citation, citations_for_indices
from app.modules.knowledge.retrieval.semantic import RetrievedChunk

INSUFFICIENT_EVIDENCE_ANSWER = (
    "I couldn't verify this from the available official sources."
)


class LLMAnswer(BaseModel):
    """Validated model output (never trust raw LLM JSON)."""

    answer: str = Field(min_length=1)
    scheme_ids: list[str] = Field(default_factory=list)
    evidence_indices: list[int] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


@dataclass
class GuardedAnswer:
    answer: str
    citations: list[Citation]
    missing_information: list[str]
    confidence: float
    grounded: bool
    rejected_reason: str | None = None


def guard_answer(
    llm_answer: LLMAnswer,
    markers: dict[int, RetrievedChunk],
) -> GuardedAnswer:
    """Validate citations against evidence; downgrade unsupported answers."""
    citations, invalid = citations_for_indices(llm_answer.evidence_indices, markers)

    # No evidence available at all -> safe insufficient response.
    if not markers:
        return GuardedAnswer(
            answer=INSUFFICIENT_EVIDENCE_ANSWER,
            citations=[],
            missing_information=llm_answer.missing_information
            or ["No verified evidence was retrieved."],
            confidence=0.0,
            grounded=False,
            rejected_reason="no_evidence",
        )

    # Model cited a non-existent evidence marker -> fabrication signal.
    if invalid:
        return GuardedAnswer(
            answer=INSUFFICIENT_EVIDENCE_ANSWER,
            citations=[],
            missing_information=["The generated answer referenced unavailable sources."],
            confidence=0.0,
            grounded=False,
            rejected_reason=f"invalid_citations:{invalid}",
        )

    # Answer makes a substantive claim but cites nothing -> unsupported.
    if not citations and not _is_refusal(llm_answer.answer):
        return GuardedAnswer(
            answer=INSUFFICIENT_EVIDENCE_ANSWER,
            citations=[],
            missing_information=["The answer was not supported by any cited evidence."],
            confidence=0.0,
            grounded=False,
            rejected_reason="unsupported_claim",
        )

    return GuardedAnswer(
        answer=llm_answer.answer,
        citations=citations,
        missing_information=llm_answer.missing_information,
        confidence=llm_answer.confidence,
        grounded=True,
    )


def _is_refusal(answer: str) -> bool:
    lowered = answer.lower()
    return any(
        p in lowered
        for p in ("couldn't verify", "could not verify", "don't have enough", "do not have enough")
    )
