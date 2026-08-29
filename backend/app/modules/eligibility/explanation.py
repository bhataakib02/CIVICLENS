"""Explanation service (prompt §19).

Transforms a deterministic EngineResult into human-readable text. This layer
is strictly downstream of the decision:

    Rule Engine -> Decision -> Explanation

It NEVER changes the decision and it is NOT an LLM (ADR-003). It is a pure,
deterministic string builder over the already-computed rule_breakdown, so the
same result always renders the same explanation.
"""
from __future__ import annotations

from app.modules.eligibility.engine import EngineResult
from app.modules.eligibility.rule_types import Decision

_DECISION_HEADLINE = {
    Decision.ELIGIBLE: "You appear eligible for this scheme.",
    Decision.LIKELY_ELIGIBLE: "You are likely eligible, pending some optional details.",
    Decision.NOT_ELIGIBLE: "You do not appear to be eligible for this scheme.",
    Decision.INSUFFICIENT_DATA: "We need more information before we can determine your eligibility.",
}


def build_explanation(result: EngineResult) -> str:
    """Return a deterministic multi-line, citizen-facing explanation."""
    lines: list[str] = [_DECISION_HEADLINE[result.decision], ""]

    passed = [r for r in result.rule_breakdown if r.outcome == "pass"]
    failed = [r for r in result.rule_breakdown if r.outcome == "fail"]

    if passed:
        lines.append("What you meet:")
        for r in passed:
            lines.append(f"  \u2713 {r.explanation}")
        lines.append("")

    if failed:
        lines.append("What does not match:")
        for r in failed:
            lines.append(f"  \u2717 {r.explanation}")
        lines.append("")

    if result.conflicts:
        lines.append("Conflicting information to resolve:")
        for c in result.conflicts:
            values = ", ".join(str(v) for v in c["values"])
            sources = ", ".join(c["sources"])
            lines.append(
                f"  ! {_pretty(c['field'])}: different values ({values}) from {sources}."
            )
        lines.append("")

    if result.missing_information:
        lines.append("Required next steps:")
        for m in result.missing_information:
            lines.append(f"  \u2192 {m['reason']}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _pretty(field_key: str) -> str:
    return field_key.replace("_", " ").capitalize()
