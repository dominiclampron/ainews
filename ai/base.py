"""
ai/base.py - Abstract base class for AI providers.

Defines the interface that all AI providers must implement.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class SummaryResult:
    """
    Result from an AI summarization call.
    
    Attributes:
        text: The generated summary text
        token_count: Tokens used (input + output)
        model: Model name used
        provider: Provider name
        success: Whether the call succeeded
        error: Error message if failed
    """
    text: str
    token_count: int = 0
    model: str = ""
    provider: str = ""
    success: bool = True
    error: Optional[str] = None
    
    @classmethod
    def failure(cls, error: str, provider: str = "") -> "SummaryResult":
        """Create a failure result."""
        return cls(
            text="",
            success=False,
            error=error,
            provider=provider,
        )


@dataclass
class DigestResult:
    """
    Result from a digest generation call.
    
    Attributes:
        text: The generated digest text
        token_count: Tokens used
        article_count: Number of articles in digest
        model: Model name used
        provider: Provider name
        success: Whether the call succeeded
        error: Error message if failed
    """
    text: str
    token_count: int = 0
    article_count: int = 0
    model: str = ""
    provider: str = ""
    success: bool = True
    error: Optional[str] = None
    
    @classmethod
    def failure(cls, error: str, provider: str = "") -> "DigestResult":
        """Create a failure result."""
        return cls(
            text="",
            success=False,
            error=error,
            provider=provider,
        )


class AIProvider(ABC):
    """
    Abstract base class for AI providers.
    
    All providers (Gemini, OpenAI, Claude, Local) must implement this interface.
    
    Example:
        >>> provider = GeminiProvider(api_key="...", model="gemini-1.5-flash")
        >>> result = provider.summarize_article("Title", "Content...")
        >>> print(result.text)
    """
    
    # Provider name (set by subclasses)
    PROVIDER_NAME: str = "base"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "",
        endpoint: Optional[str] = None,
        max_tokens: int = 1000,
    ):
        """
        Initialize the provider.
        
        Args:
            api_key: API key (not needed for local)
            model: Model name to use
            endpoint: Custom API endpoint (optional)
            max_tokens: Maximum tokens for responses
        """
        self.api_key = api_key
        self.model = model
        self.endpoint = endpoint
        self.max_tokens = max_tokens
    
    @abstractmethod
    def summarize_article(self, title: str, content: str) -> SummaryResult:
        """
        Generate a summary for a single article.
        
        Args:
            title: Article headline
            content: Article body/description
            
        Returns:
            SummaryResult with generated summary
        """
        pass
    
    @abstractmethod
    def generate_digest(
        self,
        articles: list[dict],
        period: str = "weekly",
    ) -> DigestResult:
        """
        Generate a digest from multiple articles.
        
        Args:
            articles: List of article dicts with 'title', 'summary', 'category', 'outlet'
            period: Time period description (e.g., "weekly", "Dec 13-19")
            
        Returns:
            DigestResult with generated digest
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test if the provider is configured and reachable.
        
        Returns:
            True if connection successful
        """
        pass
    
    def get_provider_name(self) -> str:
        """Get the provider name."""
        return self.PROVIDER_NAME
    
    def get_model_name(self) -> str:
        """Get the model name."""
        return self.model
    
    def is_available(self) -> bool:
        """Check if provider is available (API key set, etc.)."""
        if self.PROVIDER_NAME == "local":
            return True
        return bool(self.api_key)


# =============================================================================
# PROMPT TEMPLATES
# =============================================================================

ARTICLE_SUMMARY_PROMPT = """Summarize this news article in 2-3 concise sentences.
Focus on the key facts and why it matters.

Title: {title}

Content:
{content}

Summary:"""

DIGEST_PROMPT = """Create a news digest summarizing these {count} articles from {period}.

Group by theme when possible. Highlight the most important stories first.
Use markdown formatting with headers and bullet points.

Articles:
{articles}

Generate a professional news digest:"""

DIGEST_ARTICLE_TEMPLATE = """
### {title}
- Source: {outlet}
- Category: {category}
- Summary: {summary}
"""
