"""
ai/local.py - Local LLM provider (Ollama).

Implements AIProvider interface for locally-hosted models via Ollama.
No API key required, models run on user's machine.
"""
from __future__ import annotations

import json
from typing import Optional

import requests

from ai.base import (
    AIProvider,
    SummaryResult,
    DigestResult,
    ARTICLE_SUMMARY_PROMPT,
    DIGEST_PROMPT,
    DIGEST_ARTICLE_TEMPLATE,
)


class LocalProvider(AIProvider):
    """
    Local LLM provider using Ollama.
    
    Requires Ollama to be installed and running locally.
    https://ollama.ai/
    
    Models (must be pulled first):
        - llama2 (general purpose)
        - mistral (fast, good quality)
        - codellama (code-focused)
        - mixtral (mixture of experts)
    
    Example:
        >>> provider = LocalProvider(model="mistral")
        >>> result = provider.summarize_article("Title", "Content...")
        >>> print(result.text)
    """
    
    PROVIDER_NAME = "local"
    DEFAULT_ENDPOINT = "http://localhost:11434"
    
    def __init__(
        self,
        api_key: Optional[str] = None,  # Not used
        model: str = "llama2",
        endpoint: Optional[str] = None,
        max_tokens: int = 1000,
    ):
        super().__init__(api_key, model, endpoint, max_tokens)
        self.base_url = endpoint or self.DEFAULT_ENDPOINT
    
    def _call_ollama(self, prompt: str, max_tokens: int = None) -> tuple[str, int]:
        """
        Make a request to Ollama API.
        
        Args:
            prompt: The prompt to send
            max_tokens: Maximum tokens (num_predict in Ollama)
            
        Returns:
            Tuple of (response_text, token_count)
        """
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens or self.max_tokens,
                "temperature": 0.3,
            }
        }
        
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        
        data = response.json()
        text = data.get("response", "")
        
        # Estimate token count (Ollama provides eval_count)
        token_count = data.get("eval_count", 0) + data.get("prompt_eval_count", 0)
        
        return text, token_count
    
    def summarize_article(self, title: str, content: str) -> SummaryResult:
        """Generate article summary using local LLM."""
        try:
            prompt = ARTICLE_SUMMARY_PROMPT.format(
                title=title,
                content=content[:2000],
            )
            
            text, token_count = self._call_ollama(prompt, self.max_tokens)
            
            return SummaryResult(
                text=text.strip(),
                token_count=token_count,
                model=self.model,
                provider=self.PROVIDER_NAME,
            )
            
        except requests.exceptions.ConnectionError:
            return SummaryResult.failure(
                "Cannot connect to Ollama. Is it running? (ollama serve)",
                self.PROVIDER_NAME
            )
        except Exception as e:
            return SummaryResult.failure(str(e), self.PROVIDER_NAME)
    
    def generate_digest(
        self,
        articles: list[dict],
        period: str = "weekly",
    ) -> DigestResult:
        """Generate news digest using local LLM."""
        try:
            # Format articles for prompt
            articles_text = ""
            for art in articles[:30]:  # Limit for local models
                articles_text += DIGEST_ARTICLE_TEMPLATE.format(
                    title=art.get("title", "Untitled"),
                    outlet=art.get("outlet", "Unknown"),
                    category=art.get("category", "General"),
                    summary=art.get("summary", "")[:150],
                )
            
            prompt = DIGEST_PROMPT.format(
                count=len(articles),
                period=period,
                articles=articles_text,
            )
            
            text, token_count = self._call_ollama(prompt, 2000)
            
            return DigestResult(
                text=text.strip(),
                token_count=token_count,
                article_count=len(articles),
                model=self.model,
                provider=self.PROVIDER_NAME,
            )
            
        except requests.exceptions.ConnectionError:
            return DigestResult.failure(
                "Cannot connect to Ollama. Is it running?",
                self.PROVIDER_NAME
            )
        except Exception as e:
            return DigestResult.failure(str(e), self.PROVIDER_NAME)
    
    def test_connection(self) -> bool:
        """Test Ollama connection."""
        try:
            # Check if Ollama is running
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code != 200:
                return False
            
            # Check if the model is available
            data = response.json()
            models = [m.get("name", "").split(":")[0] for m in data.get("models", [])]
            
            return self.model in models or f"{self.model}:latest" in [m.get("name", "") for m in data.get("models", [])]
            
        except Exception:
            return False
    
    def list_available_models(self) -> list[str]:
        """List models available in Ollama."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            data = response.json()
            return [m.get("name", "") for m in data.get("models", [])]
        except Exception:
            return []
    
    def is_available(self) -> bool:
        """Check if Ollama is running."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except Exception:
            return False
