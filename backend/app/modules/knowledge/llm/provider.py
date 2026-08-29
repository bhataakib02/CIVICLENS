"""LLM provider abstraction + deterministic grounded test provider (prompt §24, §40).

The application depends on LLMProvider, never on a vendor SDK directly.

- generate(prompt) -> str
- generate_structured(prompt, schema) -> validated pydantic model (with one
  retry on invalid JSON, then safe failure)

The DeterministicGroundedTestProvider is for tests/dev ONLY. Crucially, it is
STILL GROUNDED: it does not invent policy. It composes its answer strictly from
the [EVIDENCE n] blocks present in the prompt and cites exactly those markers.
If no evidence is present, it returns the insufficient-evidence response. This
lets the full RAG path (grounding -> generation -> citation validation ->
hallucination guard) be exercised deterministically without a network call.

Production requires an explicitly configured real provider; selecting "test"
in production raises.
"""
from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from typing import Type, TypeVar

from pydantic import BaseModel, ValidationError

from app.core.config import Settings, get_settings

T = TypeVar("T", bound=BaseModel)

_EVIDENCE_BLOCK_RE = re.compile(r"\[EVIDENCE\s+(\d+)\]\s*\(([^)]*)\)\n(.*?)(?=\n\[EVIDENCE|\Z)", re.DOTALL)
_ELIGIBILITY_MARKER = "=== DETERMINISTIC ELIGIBILITY RESULTS"


class LLMError(Exception):
    pass


class LLMProvider(ABC):
    name = "abstract"

    @abstractmethod
    def generate(self, prompt: str) -> str:  # pragma: no cover - abstract
        ...

    def generate_structured(self, prompt: str, schema: Type[T]) -> T:
        """Generate + validate JSON against `schema`, retrying once on failure."""
        last_err: Exception | None = None
        for _attempt in range(2):
            raw = self.generate(prompt)
            payload = _extract_json(raw)
            if payload is not None:
                try:
                    return schema.model_validate(payload)
                except ValidationError as exc:
                    last_err = exc
            else:
                last_err = LLMError("Model did not return valid JSON.")
        raise LLMError(f"Structured output invalid after retry: {last_err}")


def _extract_json(text: str) -> dict | None:
    text = text.strip()
    # Strip code fences if present.
    if text.startswith("```"):
        text = text.strip("`")
        text = text[text.find("{") :] if "{" in text else text
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        return json.loads(text[start:end])
    except (ValueError, json.JSONDecodeError):
        return None


class DeterministicGroundedTestProvider(LLMProvider):
    """Grounded, deterministic provider for tests/dev. Never invents policy."""

    name = "test-deterministic"

    def generate(self, prompt: str) -> str:
        return json.dumps(self._structured(prompt))

    def _structured(self, prompt: str) -> dict:
        evidence = _EVIDENCE_BLOCK_RE.findall(prompt)
        has_eligibility = _ELIGIBILITY_MARKER in prompt

        if not evidence:
            return {
                "answer": "I couldn't verify this from the available official sources.",
                "scheme_ids": [],
                "evidence_indices": [],
                "missing_information": ["No verified evidence was retrieved for this query."],
                "confidence": 0.0,
            }

        # Compose a grounded answer that quotes the first 1-2 evidence blocks and
        # cites their markers — no claim beyond the provided evidence.
        cited = []
        snippets = []
        for idx_str, _prov, body in evidence[:3]:
            idx = int(idx_str)
            cited.append(idx)
            snippet = " ".join(body.strip().split())[:200]
            snippets.append(f"According to the official source [EVIDENCE {idx}], {snippet}")

        answer = " ".join(snippets)
        if has_eligibility:
            answer += (
                " Your eligibility is based on the deterministic engine results shown above; "
                "I only explain them and do not decide eligibility."
            )
        return {
            "answer": answer,
            "scheme_ids": [],
            "evidence_indices": cited,
            "missing_information": [],
            "confidence": round(min(0.95, 0.6 + 0.1 * len(cited)), 3),
        }


def get_llm_provider(settings: Settings | None = None) -> LLMProvider:
    settings = settings or get_settings()
    provider = settings.llm_provider.lower()
    if provider == "test":
        if settings.is_production:
            raise LLMError(
                "The deterministic test LLM provider must not be used in production. "
                "Configure a real LLM_PROVIDER."
            )
        return DeterministicGroundedTestProvider()
    raise LLMError(
        f"Unknown or unconfigured LLM provider '{provider}'. Bundled option: 'test' (non-production)."
    )
