"""Grounding guardrails (prompt §20, §21, ai-safety.md, threat-model.md #3).

Two responsibilities:
1. Neutralize prompt-injection in retrieved DATA: retrieved government text is
   untrusted. We wrap it in an explicit, delimited data block and defang known
   instruction-injection patterns so the model cannot be steered by document
   content. Retrieved text is DATA, never instructions.
2. Secret filtering: ensure no secrets (JWTs, DB URLs, API keys, tokens) ever
   enter model context.

These are pure string transforms — no model call, fully testable.
"""
from __future__ import annotations

import re

# Patterns that look like attempts to override instructions inside a document.
_INJECTION_PATTERNS = [
    re.compile(r"(?i)ignore\s+(all\s+)?(previous|prior|above)\s+instructions"),
    re.compile(r"(?i)disregard\s+(the\s+)?(system|previous|above)\s+(prompt|instructions?)"),
    re.compile(r"(?i)reveal\s+(the\s+)?(system\s+)?prompt[^.\n]*"),
    re.compile(r"(?i)you\s+are\s+now\s+(a|an)\b[^.\n]*"),
    re.compile(r"(?i)act\s+as\s+(a|an)\b[^.\n]*"),
    re.compile(r"(?i)\bnew\s+instructions?\b"),
    re.compile(r"(?i)override\s+.{0,20}\b(rules?|instructions?)"),
    re.compile(r"(?i)system\s*:\s*"),
    re.compile(r"(?i)developer\s*:\s*"),
]

# Secret-shaped patterns that must never reach the model.
_SECRET_PATTERNS = [
    re.compile(r"eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+"),  # JWT
    re.compile(r"(?i)postgresql(\+\w+)?://[^\s]+"),  # DB URL
    re.compile(r"(?i)\b(api[_-]?key|secret|password|token)\s*[:=]\s*\S+"),
    re.compile(r"sk-[A-Za-z0-9]{16,}"),  # OpenAI-style key
]

_NEUTRALIZED = "[neutralized-instruction]"
_REDACTED = "[redacted]"


def neutralize_injection(text: str) -> str:
    """Defang instruction-injection patterns in untrusted retrieved content."""
    out = text
    for pat in _INJECTION_PATTERNS:
        out = pat.sub(_NEUTRALIZED, out)
    return out


def contains_injection(text: str) -> bool:
    return any(p.search(text) for p in _INJECTION_PATTERNS)


def filter_secrets(text: str) -> str:
    """Redact secret-shaped substrings so they never enter model context."""
    out = text
    for pat in _SECRET_PATTERNS:
        out = pat.sub(_REDACTED, out)
    return out


def sanitize_evidence_text(text: str) -> str:
    """Full sanitization applied to any retrieved chunk before it becomes context."""
    return filter_secrets(neutralize_injection(text))
