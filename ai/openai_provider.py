"""
ai/openai_provider.py - OpenAI ChatGPT provider.

Implements AIProvider interface for OpenAI's GPT models.
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


class OpenAIProvider(AIProvider):
    """
    OpenAI ChatGPT provider.
    
    Uses the openai SDK for API calls.
    
    Models:
        - gpt-4o-mini (fast, cheap)
        - gpt-4o (most capable)
        - gpt-4-turbo (good balance)
        - gpt-3.5-turbo (legacy, cheap)
    
    Example:
        >>> provider = OpenAIProvider(api_key="...", model="gpt-4o-mini")
        >>> result = provider.summarize_article("OpenAI releases GPT-5", "...")
        >>> print(result.text)
    """
    
    PROVIDER_NAME = "openai"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        endpoint: Optional[str] = None,
        max_tokens: int = 1000,
    ):
        super().__init__(api_key, model, endpoint, max_tokens)
        self._client = None
    
    def _get_client(self):
        """Get or create the OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI
                
                kwargs = {"api_key": self.api_key}
                if self.endpoint:
                    kwargs["base_url"] = self.endpoint
                
                self._client = OpenAI(**kwargs)
            except ImportError:
                raise ImportError(
                    "openai package not installed. "
                    "Run: pip install openai"
                )
        return self._client
    
    def summarize_article(self, title: str, content: str) -> SummaryResult:
        """Generate article summary using OpenAI."""
        try:
            client = self._get_client()
            
            prompt = ARTICLE_SUMMARY_PROMPT.format(
                title=title,
                content=content[:2000],
            )
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a concise news summarizer."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=0.3,
            )
            
            token_count = 0
            if response.usage:
                token_count = response.usage.total_tokens
            
            return SummaryResult(
                text=response.choices[0].message.content.strip(),
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
        """Generate news digest using OpenAI."""
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
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional news editor creating a digest."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.4,
            )
            
            token_count = 0
            if response.usage:
                token_count = response.usage.total_tokens
            
            return DigestResult(
                text=response.choices[0].message.content.strip(),
                token_count=token_count,
                article_count=len(articles),
                model=self.model,
                provider=self.PROVIDER_NAME,
            )
            
        except Exception as e:
            return DigestResult.failure(str(e), self.PROVIDER_NAME)
    
    def test_connection(self) -> bool:
        """Test OpenAI API connection."""
        try:
            client = self._get_client()
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Say OK"}],
                max_tokens=5,
            )
            return "ok" in response.choices[0].message.content.lower()
        except Exception:
            return False
