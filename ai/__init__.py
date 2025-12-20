# ai/__init__.py
"""
AI module - Provider integrations for summary generation.

Supports:
- Google Gemini (gemini-1.5-flash, gemini-1.5-pro)
- OpenAI (gpt-4o-mini, gpt-4o, gpt-4-turbo)
- Anthropic Claude (claude-3-haiku, claude-3-sonnet, claude-3-opus)
- Local LLMs via Ollama (llama2, mistral, etc.)
"""

from ai.base import (
    AIProvider,
    SummaryResult,
    DigestResult,
    ARTICLE_SUMMARY_PROMPT,
    DIGEST_PROMPT,
)
from ai.factory import (
    create_provider,
    create_provider_from_settings,
    get_available_providers,
    test_provider,
    estimate_cost,
)
from ai.summarizer import (
    Summarizer,
    SummaryStats,
    DigestOutput,
    get_summarizer,
    generate_weekly_digest,
    generate_daily_digest,
)

# Lazy imports for providers (avoid loading unused SDKs)
def get_gemini_provider():
    from ai.gemini import GeminiProvider
    return GeminiProvider

def get_openai_provider():
    from ai.openai_provider import OpenAIProvider
    return OpenAIProvider

def get_claude_provider():
    from ai.claude import ClaudeProvider
    return ClaudeProvider

def get_local_provider():
    from ai.local import LocalProvider
    return LocalProvider

__all__ = [
    # Base classes
    "AIProvider",
    "SummaryResult",
    "DigestResult",
    # Prompts
    "ARTICLE_SUMMARY_PROMPT",
    "DIGEST_PROMPT",
    # Factory
    "create_provider",
    "create_provider_from_settings",
    "get_available_providers",
    "test_provider",
    "estimate_cost",
    # Summarizer
    "Summarizer",
    "SummaryStats",
    "DigestOutput",
    "get_summarizer",
    "generate_weekly_digest",
    "generate_daily_digest",
    # Provider getters (lazy)
    "get_gemini_provider",
    "get_openai_provider",
    "get_claude_provider",
    "get_local_provider",
]
