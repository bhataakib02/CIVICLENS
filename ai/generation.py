"""Prompt assembly and LLM generation orchestration.

Re-exports the canonical LLM provider interface and all bundled providers from
the backend. Consumer code should import from ``ai.generation`` instead of
reaching into ``backend.app.modules.knowledge.llm`` directly.

See ``docs/ai/prompt-engineering.md`` and ``docs/ai/rag-architecture.md``.
"""

from app.modules.knowledge.llm.provider import (
    AnthropicLLMProvider,
    AWSBedrockLLMProvider,
    DeterministicGroundedTestProvider,
    LLMError,
    LLMProvider,
    OllamaLLMProvider,
    OpenAILLMProvider,
    get_llm_provider,
)

__all__ = [
    "LLMProvider",
    "LLMError",
    "get_llm_provider",
    # Bundled providers
    "DeterministicGroundedTestProvider",
    "OpenAILLMProvider",
    "AnthropicLLMProvider",
    "AWSBedrockLLMProvider",
    "OllamaLLMProvider",
]
