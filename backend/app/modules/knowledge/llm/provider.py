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


class OpenAILLMProvider(LLMProvider):
    """Production LLM provider using OpenAI API."""

    name = "openai"

    def __init__(self, model: str = "gpt-4o") -> None:
        import os
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", model)

    def generate(self, prompt: str) -> str:
        if not self.api_key:
            raise LLMError("OpenAI API key (OPENAI_API_KEY) missing. Activation is PROVIDER-DEPENDENT.")
        try:
            import httpx

            url = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
            }
            with httpx.Client(timeout=30.0) as client:
                res = client.post(url, headers=headers, json=payload)
                res.raise_for_status()
                return res.json()["choices"][0]["message"]["content"]
        except Exception as exc:
            raise LLMError(f"OpenAI generation failed: {exc}") from exc


class AnthropicLLMProvider(LLMProvider):
    """Production LLM provider using Anthropic Claude Messages API."""

    name = "anthropic"

    def __init__(self, model: str = "claude-3-5-sonnet-20241022") -> None:
        import os
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.model = os.getenv("ANTHROPIC_MODEL", model)

    def generate(self, prompt: str) -> str:
        if not self.api_key:
            raise LLMError("Anthropic API key (ANTHROPIC_API_KEY) missing. Activation is PROVIDER-DEPENDENT.")
        try:
            import httpx

            url = "https://api.anthropic.com/v1/messages"
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }
            payload = {
                "model": self.model,
                "max_tokens": 2048,
                "messages": [{"role": "user", "content": prompt}],
            }
            with httpx.Client(timeout=30.0) as client:
                res = client.post(url, headers=headers, json=payload)
                res.raise_for_status()
                return res.json()["content"][0]["text"]
        except Exception as exc:
            raise LLMError(f"Anthropic generation failed: {exc}") from exc


class AWSBedrockLLMProvider(LLMProvider):
    """Production LLM provider using AWS Bedrock Converse API."""

    name = "aws_bedrock"

    def __init__(self, model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0") -> None:
        import os
        self.region = os.getenv("AWS_REGION", "ap-south-1")
        self.model_id = os.getenv("BEDROCK_MODEL_ID", model_id)
        self.access_key = os.getenv("AWS_ACCESS_KEY_ID")

    def generate(self, prompt: str) -> str:
        if not self.access_key:
            raise LLMError("AWS Bedrock credentials missing. Activation is PROVIDER-DEPENDENT.")
        try:
            import boto3

            client = boto3.client("bedrock-runtime", region_name=self.region)
            response = client.converse(
                modelId=self.model_id,
                messages=[{"role": "user", "content": [{"text": prompt}]}],
                inferenceConfig={"maxTokens": 2048, "temperature": 0.1},
            )
            return response["output"]["message"]["content"][0]["text"]
        except Exception as exc:
            raise LLMError(f"AWS Bedrock generation failed: {exc}") from exc


class OllamaLLMProvider(LLMProvider):
    """Production LLM provider using Ollama local server."""

    name = "ollama"

    def __init__(self, model: str = "llama3:8b") -> None:
        import os
        self.host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", model)

    def generate(self, prompt: str) -> str:
        try:
            import httpx

            url = f"{self.host.rstrip('/')}/api/generate"
            payload = {"model": self.model, "prompt": prompt, "stream": False}
            with httpx.Client(timeout=60.0) as client:
                res = client.post(url, json=payload)
                res.raise_for_status()
                return res.json()["response"]
        except Exception as exc:
            raise LLMError(f"Ollama generation failed: {exc}") from exc


def get_llm_provider(settings: Settings | None = None) -> LLMProvider:
    settings = settings or get_settings()
    provider = settings.llm_provider.lower()

    if provider in ("test", "test-deterministic"):
        if settings.is_production:
            raise LLMError(
                "The deterministic test LLM provider must not be used in production. "
                "Configure a real LLM_PROVIDER ('openai', 'anthropic', 'aws_bedrock', 'ollama')."
            )
        return DeterministicGroundedTestProvider()

    if provider == "openai":
        return OpenAILLMProvider()

    if provider == "anthropic":
        return AnthropicLLMProvider()

    if provider in ("aws_bedrock", "bedrock"):
        return AWSBedrockLLMProvider()

    if provider == "ollama":
        return OllamaLLMProvider()

    raise LLMError(
        f"Unknown or unconfigured LLM provider '{provider}'. "
        "Supported values: 'test', 'openai', 'anthropic', 'aws_bedrock', 'ollama'."
    )

