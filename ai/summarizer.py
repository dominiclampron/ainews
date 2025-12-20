"""
ai/summarizer.py - Summary and digest generation service.

High-level service that orchestrates:
- Article summarization
- Digest generation
- Database storage
- Output formatting
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Optional, Literal

from ai.base import SummaryResult, DigestResult
from ai.factory import create_provider_from_settings
from config.settings import get_settings
from data.models import (
    ArticleRecord,
    SummaryRecord,
    DigestRecord,
    save_summary,
    get_summary_for_article,
    save_digest,
    get_articles_for_digest,
    get_recent_articles,
)


OutputFormat = Literal["markdown", "html", "text"]


@dataclass
class SummaryStats:
    """Statistics from a summarization run."""
    articles_processed: int = 0
    articles_skipped: int = 0
    articles_failed: int = 0
    total_tokens: int = 0
    provider: str = ""
    model: str = ""
    duration_seconds: float = 0.0


@dataclass
class DigestOutput:
    """Output from digest generation."""
    text: str
    format: OutputFormat
    article_count: int
    period_start: Optional[dt.datetime] = None
    period_end: Optional[dt.datetime] = None
    provider: str = ""
    model: str = ""
    token_count: int = 0
    success: bool = True
    error: Optional[str] = None


class Summarizer:
    """
    Summary and digest generation service.
    
    Handles all AI-powered text generation with caching
    and database integration.
    
    Example:
        >>> summarizer = Summarizer()
        >>> if summarizer.is_available():
        ...     digest = summarizer.generate_weekly_digest()
        ...     print(digest.text)
    """
    
    def __init__(self):
        self._provider = None
        self._settings = None
    
    def _get_provider(self):
        """Get or create the AI provider."""
        if self._provider is None:
            self._provider = create_provider_from_settings()
        return self._provider
    
    def _get_settings(self):
        """Get current settings."""
        if self._settings is None:
            self._settings = get_settings()
        return self._settings
    
    def is_available(self) -> bool:
        """Check if AI summarization is available."""
        settings = self._get_settings()
        return settings.is_ai_ready()
    
    def get_provider_info(self) -> dict:
        """Get information about the current provider."""
        settings = self._get_settings()
        return {
            "provider": settings.ai.provider,
            "model": settings.ai.model,
            "available": self.is_available(),
        }
    
    def summarize_article(
        self,
        article: ArticleRecord,
        force: bool = False,
    ) -> Optional[SummaryResult]:
        """
        Generate AI summary for a single article.
        
        Args:
            article: Article to summarize
            force: If True, regenerate even if cached
            
        Returns:
            SummaryResult or None if failed
        """
        if not self.is_available():
            return None
        
        # Check for cached summary
        if not force and article.id:
            existing = get_summary_for_article(article.id)
            if existing:
                return SummaryResult(
                    text=existing.summary_text,
                    token_count=existing.token_count,
                    model=existing.model,
                    provider=existing.provider,
                )
        
        # Generate new summary
        provider = self._get_provider()
        result = provider.summarize_article(article.title, article.summary)
        
        # Save to database if successful
        if result.success and article.id:
            record = SummaryRecord(
                article_id=article.id,
                provider=result.provider,
                model=result.model,
                summary_text=result.text,
                token_count=result.token_count,
            )
            save_summary(record)
        
        return result
    
    def summarize_articles(
        self,
        articles: list[ArticleRecord],
        force: bool = False,
        progress_callback=None,
    ) -> SummaryStats:
        """
        Summarize multiple articles.
        
        Args:
            articles: List of articles to summarize
            force: If True, regenerate all summaries
            progress_callback: Optional callback(current, total)
            
        Returns:
            SummaryStats with results
        """
        import time
        start_time = time.time()
        
        stats = SummaryStats()
        provider = self._get_provider()
        if provider:
            stats.provider = provider.get_provider_name()
            stats.model = provider.get_model_name()
        
        for i, article in enumerate(articles):
            if progress_callback:
                progress_callback(i + 1, len(articles))
            
            result = self.summarize_article(article, force=force)
            
            if result is None:
                stats.articles_skipped += 1
            elif result.success:
                stats.articles_processed += 1
                stats.total_tokens += result.token_count
            else:
                stats.articles_failed += 1
        
        stats.duration_seconds = time.time() - start_time
        return stats
    
    def generate_digest(
        self,
        articles: list[ArticleRecord],
        period: str = "weekly",
        output_format: OutputFormat = "markdown",
    ) -> DigestOutput:
        """
        Generate a news digest from articles.
        
        Args:
            articles: Articles to include in digest
            period: Period description (e.g., "Dec 13-19, 2025")
            output_format: Output format
            
        Returns:
            DigestOutput with generated digest
        """
        if not self.is_available():
            return DigestOutput(
                text="",
                format=output_format,
                article_count=len(articles),
                success=False,
                error="AI provider not configured",
            )
        
        # Convert articles to dict format for provider
        articles_data = []
        for art in articles:
            articles_data.append({
                "title": art.title,
                "summary": art.summary,
                "category": art.category,
                "outlet": art.outlet,
            })
        
        # Generate digest
        provider = self._get_provider()
        result = provider.generate_digest(articles_data, period)
        
        if not result.success:
            return DigestOutput(
                text="",
                format=output_format,
                article_count=len(articles),
                success=False,
                error=result.error,
            )
        
        # Format output
        text = result.text
        if output_format == "html":
            text = self._markdown_to_html(text)
        elif output_format == "text":
            text = self._markdown_to_text(text)
        
        return DigestOutput(
            text=text,
            format=output_format,
            article_count=len(articles),
            provider=result.provider,
            model=result.model,
            token_count=result.token_count,
            success=True,
        )
    
    def generate_weekly_digest(
        self,
        output_format: OutputFormat = "markdown",
        save_to_db: bool = True,
    ) -> DigestOutput:
        """
        Generate a digest for the past week.
        
        Args:
            output_format: Output format (markdown, html, text)
            save_to_db: Whether to save the digest to database
            
        Returns:
            DigestOutput with generated digest
        """
        end_date = dt.datetime.now(dt.timezone.utc)
        start_date = end_date - dt.timedelta(days=7)
        
        period = f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}"
        
        # Get articles from database
        articles = get_recent_articles(limit=100, days=7)
        
        if not articles:
            return DigestOutput(
                text="No articles found for the past week.",
                format=output_format,
                article_count=0,
                period_start=start_date,
                period_end=end_date,
                success=True,
            )
        
        # Generate digest
        output = self.generate_digest(articles, period, output_format)
        output.period_start = start_date
        output.period_end = end_date
        
        # Save to database
        if save_to_db and output.success:
            record = DigestRecord(
                period_start=start_date,
                period_end=end_date,
                digest_type="weekly",
                digest_text=output.text,
                article_count=output.article_count,
                provider=output.provider,
                model=output.model,
            )
            save_digest(record)
        
        return output
    
    def generate_daily_digest(
        self,
        output_format: OutputFormat = "markdown",
        save_to_db: bool = True,
    ) -> DigestOutput:
        """
        Generate a digest for the past 24 hours.
        
        Args:
            output_format: Output format
            save_to_db: Whether to save to database
            
        Returns:
            DigestOutput with generated digest
        """
        end_date = dt.datetime.now(dt.timezone.utc)
        start_date = end_date - dt.timedelta(days=1)
        
        period = f"{end_date.strftime('%B %d, %Y')}"
        
        articles = get_recent_articles(limit=50, days=1)
        
        if not articles:
            return DigestOutput(
                text="No articles found for today.",
                format=output_format,
                article_count=0,
                period_start=start_date,
                period_end=end_date,
                success=True,
            )
        
        output = self.generate_digest(articles, period, output_format)
        output.period_start = start_date
        output.period_end = end_date
        
        if save_to_db and output.success:
            record = DigestRecord(
                period_start=start_date,
                period_end=end_date,
                digest_type="daily",
                digest_text=output.text,
                article_count=output.article_count,
                provider=output.provider,
                model=output.model,
            )
            save_digest(record)
        
        return output
    
    def generate_monthly_digest(
        self,
        output_format: OutputFormat = "markdown",
        save_to_db: bool = True,
    ) -> DigestOutput:
        """
        Generate a digest for the past 30 days.
        
        Args:
            output_format: Output format (markdown, html, text)
            save_to_db: Whether to save the digest to database
            
        Returns:
            DigestOutput with generated digest
        """
        end_date = dt.datetime.now(dt.timezone.utc)
        start_date = end_date - dt.timedelta(days=30)
        
        period = f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}"
        
        # Get articles from database
        articles = get_recent_articles(limit=200, days=30)
        
        if not articles:
            return DigestOutput(
                text="No articles found for the past month.",
                format=output_format,
                article_count=0,
                period_start=start_date,
                period_end=end_date,
                success=True,
            )
        
        # Generate digest
        output = self.generate_digest(articles, period, output_format)
        output.period_start = start_date
        output.period_end = end_date
        
        # Save to database
        if save_to_db and output.success:
            record = DigestRecord(
                period_start=start_date,
                period_end=end_date,
                digest_type="monthly",
                digest_text=output.text,
                article_count=output.article_count,
                provider=output.provider,
                model=output.model,
            )
            save_digest(record)
        
        return output
    
    def _markdown_to_html(self, markdown_text: str) -> str:
        """Convert markdown to HTML."""
        try:
            import re
            
            html = markdown_text
            
            # Headers
            html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
            html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
            html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
            
            # Bold and italic
            html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
            html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
            
            # Lists
            html = re.sub(r'^- (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
            
            # Line breaks
            html = html.replace('\n\n', '</p><p>')
            html = f'<p>{html}</p>'
            
            return html
        except Exception:
            return f'<pre>{markdown_text}</pre>'
    
    def _markdown_to_text(self, markdown_text: str) -> str:
        """Convert markdown to plain text."""
        import re
        
        text = markdown_text
        
        # Remove markdown formatting
        text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        text = re.sub(r'^- ', '• ', text, flags=re.MULTILINE)
        
        return text


# Convenience functions

def get_summarizer() -> Summarizer:
    """Get a Summarizer instance."""
    return Summarizer()


def generate_weekly_digest(output_format: OutputFormat = "markdown") -> DigestOutput:
    """Generate weekly digest (convenience function)."""
    return Summarizer().generate_weekly_digest(output_format)


def generate_daily_digest(output_format: OutputFormat = "markdown") -> DigestOutput:
    """Generate daily digest (convenience function)."""
    return Summarizer().generate_daily_digest(output_format)
