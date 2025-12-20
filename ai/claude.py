"""
ai/claude.py - Anthropic Claude provider.

Implements AIProvider interface for Anthropic's Claude models.
"""
from __future__ import annotations

from typing import Optional

from ai.base import (
    AIProvider,
    SummaryResult,
    DigestResult,
    ARTICLE_SUMMARY_PROMPT,
    DIGEST_PROMPT,
    DIGEST_ARTICLE_TEMPLATE,
)


class ClaudeProvider(AIProvider):
    """
    Anthropic Claude provider.
    
    Uses the anthropic SDK for API calls.
    
    Models:
        - claude-3-haiku-20240307 (fast, cheap)
        - claude-3-sonnet-20240229 (balanced)
        - claude-3-opus-20240229 (most capable)
    
    Example:
        >>> provider = ClaudeProvider(api_key="...", model="claude-3-haiku-20240307")
        >>> result = provider.summarize_article("OpenAI releases GPT-5", "...")
        >>> print(result.text)
    """
    
    PROVIDER_NAME = "claude"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-haiku-20240307",
        endpoint: Optional[str] = None,
        max_tokens: int = 1000,
    ):
        super().__init__(api_key, model, endpoint, max_tokens)
        self._client = None
    
    def _get_client(self):
        """Get or create the Anthropic client."""
        if self._client is None:
            try:
                import anthropic
                
                kwargs = {"api_key": self.api_key}
                if self.endpoint:
                    kwargs["base_url"] = self.endpoint
                
                self._client = anthropic.Anthropic(**kwargs)
            except ImportError:
                raise ImportError(
                    "anthropic package not installed. "
                    "Run: pip install anthropic"
                )
        return self._client
    
    def summarize_article(self, title: str, content: str) -> SummaryResult:
        """Generate article summary using Claude."""
        try:
            client = self._get_client()
            
            prompt = ARTICLE_SUMMARY_PROMPT.format(
                title=title,
                content=content[:2000],
            )
            
            response = client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[
                    {"role": "user", "content": prompt}
                ],
            )
            
            # Calculate token count
            token_count = response.usage.input_tokens + response.usage.output_tokens
            
            # Extract text from response
            text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    text += block.text
            
            return SummaryResult(
                text=text.strip(),
                token_count=token_count,
                model=self.model,
                provider=self.PROVIDER_NAME,
            )
            
        except Exception as e:
            return SummaryResult.failure(str(e), self.PROVIDER_NAME)
    
    def generate_digest(
        self,
        articles: list[dict],
        period: str = "weekly",
    ) -> DigestResult:
        """Generate news digest using Claude."""
        try:
            client = self._get_client()
            
            # Format articles for prompt
            articles_text = ""
            for art in articles[:50]:
                articles_text += DIGEST_ARTICLE_TEMPLATE.format(
                    title=art.get("title", "Untitled"),
                    outlet=art.get("outlet", "Unknown"),
                    category=art.get("category", "General"),
                    summary=art.get("summary", "")[:200],
                )
            
            prompt = DIGEST_PROMPT.format(
                count=len(articles),
                period=period,
                articles=articles_text,
            )
            
            response = client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[
                    {"role": "user", "content": prompt}
                ],
            )
            
            token_count = response.usage.input_tokens + response.usage.output_tokens
            
            text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    text += block.text
            
            return DigestResult(
                text=text.strip(),
                token_count=token_count,
                article_count=len(articles),
                model=self.model,
                provider=self.PROVIDER_NAME,
            )
            
        except Exception as e:
            return DigestResult.failure(str(e), self.PROVIDER_NAME)
    
    def test_connection(self) -> bool:
        """Test Claude API connection."""
        try:
            client = self._get_client()
            response = client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "Say OK"}],
            )
            text = "".join(b.text for b in response.content if hasattr(b, "text"))
            return "ok" in text.lower()
        except Exception:
            return False
