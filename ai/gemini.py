"""
ai/gemini.py - Google Gemini AI provider.

Implements AIProvider interface for Google's Gemini models.
Includes rate limiting to prevent API timeouts.
"""
from __future__ import annotations

import time
from typing import Optional

from ai.base import (
    AIProvider,
    SummaryResult,
    DigestResult,
    ARTICLE_SUMMARY_PROMPT,
    DIGEST_PROMPT,
    DIGEST_ARTICLE_TEMPLATE,
)


class GeminiProvider(AIProvider):
    """
    Google Gemini AI provider.
    
    Uses the google-generativeai SDK for API calls.
    Includes rate limiting (12 requests per minute max).
    
    Models:
        - gemini-2.5-flash (fastest, newest)
        - gemini-1.5-flash (fast, cheap)
        - gemini-1.5-pro (more capable)
        - gemini-pro (legacy)
    
    Example:
        >>> provider = GeminiProvider(api_key="...", model="gemini-2.5-flash")
        >>> result = provider.summarize_article("OpenAI releases GPT-5", "...")
        >>> print(result.text)
    """
    
    PROVIDER_NAME = "gemini"
    
    # Rate limiting: max 12 requests per minute to avoid 5-minute timeout
    RATE_LIMIT = 12
    RATE_WINDOW = 60  # seconds
    
    # Class-level request tracking (shared across instances)
    _request_times = []
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-2.5-flash",
        endpoint: Optional[str] = None,
        max_tokens: int = 1000,
    ):
        super().__init__(api_key, model, endpoint, max_tokens)
        self._client = None
        self._model_instance = None
    
    def _rate_limit(self):
        """
        Enforce rate limiting: max 12 requests per minute.
        Sleeps if we've hit the limit.
        """
        now = time.time()
        
        # Remove requests older than the rate window
        GeminiProvider._request_times = [
            t for t in GeminiProvider._request_times 
            if now - t < self.RATE_WINDOW
        ]
        
        # If at limit, wait until oldest request expires
        if len(GeminiProvider._request_times) >= self.RATE_LIMIT:
            oldest = GeminiProvider._request_times[0]
            sleep_time = self.RATE_WINDOW - (now - oldest) + 1
            if sleep_time > 0:
                print(f"⏳ Rate limit reached, waiting {sleep_time:.0f}s...")
                time.sleep(sleep_time)
        
        # Record this request
        GeminiProvider._request_times.append(time.time())
    
    def _get_client(self):
        """Get or create the Gemini client."""
        if self._client is None:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._client = genai
                self._model_instance = genai.GenerativeModel(self.model)
            except ImportError:
                raise ImportError(
                    "google-generativeai package not installed. "
                    "Run: pip install google-generativeai"
                )
        return self._client, self._model_instance
    
    def summarize_article(self, title: str, content: str) -> SummaryResult:
        """Generate article summary using Gemini."""
        try:
            self._rate_limit()  # Enforce rate limiting
            _, model = self._get_client()
            
            prompt = ARTICLE_SUMMARY_PROMPT.format(
                title=title,
                content=content[:2000],  # Limit content length
            )
            
            response = model.generate_content(
                prompt,
                generation_config={
                    "max_output_tokens": self.max_tokens,
                    "temperature": 0.3,
                }
            )
            
            # Get token count if available
            token_count = 0
            if hasattr(response, 'usage_metadata'):
                token_count = (
                    response.usage_metadata.prompt_token_count +
                    response.usage_metadata.candidates_token_count
                )
            
            return SummaryResult(
                text=response.text.strip(),
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
        """Generate news digest using Gemini."""
        try:
            self._rate_limit()  # Enforce rate limiting
            _, model = self._get_client()
            
            # Format articles for prompt
            articles_text = ""
            for art in articles[:50]:  # Limit to 50 articles
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
            
            response = model.generate_content(
                prompt,
                generation_config={
                    "max_output_tokens": 2000,
                    "temperature": 0.4,
                }
            )
            
            token_count = 0
            if hasattr(response, 'usage_metadata'):
                token_count = (
                    response.usage_metadata.prompt_token_count +
                    response.usage_metadata.candidates_token_count
                )
            
            return DigestResult(
                text=response.text.strip(),
                token_count=token_count,
                article_count=len(articles),
                model=self.model,
                provider=self.PROVIDER_NAME,
            )
            
        except Exception as e:
            return DigestResult.failure(str(e), self.PROVIDER_NAME)
    
    def test_connection(self) -> bool:
        """Test Gemini API connection."""
        try:
            _, model = self._get_client()
            response = model.generate_content(
                "Say 'OK' if you can read this.",
                generation_config={"max_output_tokens": 10}
            )
            return "ok" in response.text.lower()
        except Exception:
            return False
