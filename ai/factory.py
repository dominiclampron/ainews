"""
ai/factory.py - Provider factory for creating AI providers.

Creates the appropriate provider based on configuration.
"""
from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from ai.base import AIProvider

if TYPE_CHECKING:
    from config.settings import Settings


# Lazy imports to avoid loading unused SDKs
_PROVIDER_CLASSES = {
    "gemini": "ai.gemini.GeminiProvider",
    "openai": "ai.openai_provider.OpenAIProvider",
    "claude": "ai.claude.ClaudeProvider",
    "local": "ai.local.LocalProvider",
}


def _import_provider_class(provider: str):
    """Dynamically import a provider class."""
    if provider not in _PROVIDER_CLASSES:
        raise ValueError(f"Unknown provider: {provider}")
    
    module_path, class_name = _PROVIDER_CLASSES[provider].rsplit(".", 1)
    module = __import__(module_path, fromlist=[class_name])
    return getattr(module, class_name)


def create_provider(
    provider: str,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    endpoint: Optional[str] = None,
    max_tokens: int = 1000,
) -> AIProvider:
    """
    Create an AI provider instance.
    
    Args:
        provider: Provider name (gemini, openai, claude, local)
        api_key: API key (auto-loaded from env if not provided)
        model: Model name (uses default if not provided)
        endpoint: Custom API endpoint
        max_tokens: Maximum response tokens
        
    Returns:
        AIProvider instance
        
    Example:
        >>> provider = create_provider("gemini", model="gemini-1.5-flash")
        >>> result = provider.summarize_article("Title", "Content...")
    """
    provider = provider.lower()
    
    # Auto-load API key from environment if not provided
    if api_key is None and provider != "local":
        from config.secrets import get_api_key
        api_key = get_api_key(provider)
    
    # Get default model if not provided
    if model is None:
        from config.setup import PROVIDERS
        provider_info = PROVIDERS.get(provider, {})
        model = provider_info.get("default_model", "")
    
    # Import and create provider
    provider_class = _import_provider_class(provider)
    return provider_class(
        api_key=api_key,
        model=model,
        endpoint=endpoint,
        max_tokens=max_tokens,
    )


def create_provider_from_settings(settings: Optional["Settings"] = None) -> Optional[AIProvider]:
    """
    Create a provider from current settings.
    
    Args:
        settings: Settings object (loads from file if not provided)
        
    Returns:
        AIProvider instance or None if not configured
    """
    if settings is None:
        from config.settings import get_settings
        settings = get_settings()
    
    if settings.ai.provider == "none":
        return None
    
    if not settings.ai.is_configured():
        return None
    
    return create_provider(
        provider=settings.ai.provider,
        model=settings.ai.model,
        endpoint=settings.ai.endpoint,
        max_tokens=settings.ai.max_tokens,
    )


def get_available_providers() -> list[str]:
    """Get list of available provider names."""
    return list(_PROVIDER_CLASSES.keys())


def test_provider(provider: str, api_key: Optional[str] = None) -> tuple[bool, str]:
    """
    Test a provider connection.
    
    Args:
        provider: Provider name
        api_key: Optional API key to test
        
    Returns:
        Tuple of (success, message)
    """
    try:
        instance = create_provider(provider, api_key=api_key)
        if instance.test_connection():
            return True, f"{provider} connection successful"
        else:
            return False, f"{provider} connection failed"
    except ImportError as e:
        return False, f"Missing SDK: {e}"
    except Exception as e:
        return False, f"Error: {e}"


def estimate_cost(
    provider: str,
    input_tokens: int,
    output_tokens: int,
) -> float:
    """
    Estimate cost for a provider call (USD).
    
    Approximate pricing as of 2024.
    
    Args:
        provider: Provider name
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        
    Returns:
        Estimated cost in USD
    """
    # Pricing per 1M tokens (approximate)
    PRICING = {
        "gemini": {"input": 0.075, "output": 0.30},  # Flash
        "openai": {"input": 0.15, "output": 0.60},   # gpt-4o-mini
        "claude": {"input": 0.25, "output": 1.25},   # Haiku
        "local": {"input": 0.0, "output": 0.0},
    }
    
    prices = PRICING.get(provider, {"input": 0, "output": 0})
    
    cost = (
        (input_tokens / 1_000_000) * prices["input"] +
        (output_tokens / 1_000_000) * prices["output"]
    )
    
    return round(cost, 6)
