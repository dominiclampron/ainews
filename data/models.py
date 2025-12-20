"""
data/models.py - Data models for article storage and retrieval.

Provides:
- ArticleRecord: Database representation of an article
- SummaryRecord: AI-generated summary
- DigestRecord: Weekly/daily compilation
- CRUD operations for each model
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from data.database import get_cursor

if TYPE_CHECKING:
    from core.article import Article


@dataclass
class ArticleRecord:
    """
    Database record for a stored article.
    
    Mirrors the Article dataclass but with database-specific fields.
    """
    id: Optional[int] = None
    url: str = ""
    url_hash: str = ""
    title: str = ""
    outlet: str = ""
    outlet_key: str = ""
    category: str = "ai_headlines"
    published_at: Optional[datetime] = None
    summary: str = ""
    image_url: Optional[str] = None
    
    # Scoring
    recency_score: float = 0.0
    importance_score: float = 0.0
    source_score: float = 0.0
    final_score: float = 0.0
    
    # Metadata
    priority: str = "normal"
    why_matters: str = ""
    reading_time_min: int = 0
    
    # Clustering
    cluster_id: Optional[str] = None
    is_cluster_primary: bool = True
    related_articles: list = field(default_factory=list)
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def from_article(cls, article: "Article") -> "ArticleRecord":
        """Create record from Article dataclass."""
        return cls(
            url=article.url,
            url_hash=hashlib.sha1(article.url.encode()).hexdigest()[:16],
            title=article.title,
            outlet=article.outlet,
            outlet_key=article.outlet_key,
            category=article.category,
            published_at=article.published,
            summary=article.summary,
            image_url=article.image_url,
            recency_score=article.recency_score,
            importance_score=article.importance_score,
            source_score=article.source_score,
            final_score=article.final_score,
            priority=article.priority,
            why_matters=article.why_matters,
            reading_time_min=article.reading_time_min,
            cluster_id=article.cluster_id,
            is_cluster_primary=article.is_cluster_primary,
            related_articles=article.related_articles,
        )
    
    @classmethod
    def from_row(cls, row) -> "ArticleRecord":
        """Create record from database row."""
        related = []
        if row["related_articles_json"]:
            try:
                related = json.loads(row["related_articles_json"])
            except json.JSONDecodeError:
                pass
        
        return cls(
            id=row["id"],
            url=row["url"],
            url_hash=row["url_hash"],
            title=row["title"],
            outlet=row["outlet"] or "",
            outlet_key=row["outlet_key"] or "",
            category=row["category"] or "ai_headlines",
            published_at=_parse_datetime(row["published_at"]),
            summary=row["summary"] or "",
            image_url=row["image_url"],
            recency_score=row["recency_score"] or 0.0,
            importance_score=row["importance_score"] or 0.0,
            source_score=row["source_score"] or 0.0,
            final_score=row["final_score"] or 0.0,
            priority=row["priority"] or "normal",
            why_matters=row["why_matters"] or "",
            reading_time_min=row["reading_time_min"] or 0,
            cluster_id=row["cluster_id"],
            is_cluster_primary=bool(row["is_cluster_primary"]),
            related_articles=related,
            created_at=_parse_datetime(row["created_at"]),
            updated_at=_parse_datetime(row["updated_at"]),
        )


@dataclass
class SummaryRecord:
    """Database record for an AI-generated summary."""
    id: Optional[int] = None
    article_id: int = 0
    provider: str = ""
    model: str = ""
    summary_text: str = ""
    token_count: int = 0
    created_at: Optional[datetime] = None
    
    @classmethod
    def from_row(cls, row) -> "SummaryRecord":
        return cls(
            id=row["id"],
            article_id=row["article_id"],
            provider=row["provider"],
            model=row["model"],
            summary_text=row["summary_text"],
            token_count=row["token_count"] or 0,
            created_at=_parse_datetime(row["created_at"]),
        )


@dataclass
class DigestRecord:
    """Database record for a news digest."""
    id: Optional[int] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    digest_type: str = "weekly"
    digest_text: str = ""
    article_count: int = 0
    provider: Optional[str] = None
    model: Optional[str] = None
    created_at: Optional[datetime] = None
    
    @classmethod
    def from_row(cls, row) -> "DigestRecord":
        return cls(
            id=row["id"],
            period_start=_parse_datetime(row["period_start"]),
            period_end=_parse_datetime(row["period_end"]),
            digest_type=row["digest_type"] or "weekly",
            digest_text=row["digest_text"],
            article_count=row["article_count"] or 0,
            provider=row["provider"],
            model=row["model"],
            created_at=_parse_datetime(row["created_at"]),
        )


def _parse_datetime(value) -> Optional[datetime]:
    """Parse datetime from database string."""
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


# =============================================================================
# ARTICLE CRUD OPERATIONS
# =============================================================================

def save_article(record: ArticleRecord) -> int:
    """
    Save article to database (insert or update).
    
    Args:
        record: ArticleRecord to save
        
    Returns:
        Article ID
    """
    related_json = json.dumps(record.related_articles) if record.related_articles else None
    
    with get_cursor() as cursor:
        # Check if article exists
        cursor.execute(
            "SELECT id FROM articles WHERE url_hash = ?",
            (record.url_hash or hashlib.sha1(record.url.encode()).hexdigest()[:16],)
        )
        existing = cursor.fetchone()
        
        if existing:
            # Update
            cursor.execute("""
                UPDATE articles SET
                    title = ?, outlet = ?, outlet_key = ?, category = ?,
                    published_at = ?, summary = ?, image_url = ?,
                    recency_score = ?, importance_score = ?, source_score = ?,
                    final_score = ?, priority = ?, why_matters = ?,
                    reading_time_min = ?, cluster_id = ?, is_cluster_primary = ?,
                    related_articles_json = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                record.title, record.outlet, record.outlet_key, record.category,
                record.published_at, record.summary, record.image_url,
                record.recency_score, record.importance_score, record.source_score,
                record.final_score, record.priority, record.why_matters,
                record.reading_time_min, record.cluster_id, int(record.is_cluster_primary),
                related_json, existing["id"]
            ))
            return existing["id"]
        else:
            # Insert
            cursor.execute("""
                INSERT INTO articles (
                    url, url_hash, title, outlet, outlet_key, category,
                    published_at, summary, image_url,
                    recency_score, importance_score, source_score, final_score,
                    priority, why_matters, reading_time_min,
                    cluster_id, is_cluster_primary, related_articles_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.url, record.url_hash or hashlib.sha1(record.url.encode()).hexdigest()[:16],
                record.title, record.outlet, record.outlet_key, record.category,
                record.published_at, record.summary, record.image_url,
                record.recency_score, record.importance_score, record.source_score,
                record.final_score, record.priority, record.why_matters,
                record.reading_time_min, record.cluster_id, int(record.is_cluster_primary),
                related_json
            ))
            return cursor.lastrowid


def save_articles(articles: list) -> int:
    """
    Save multiple articles to database.
    
    Args:
        articles: List of Article dataclass objects
        
    Returns:
        Number of articles saved
    """
    count = 0
    for article in articles:
        try:
            record = ArticleRecord.from_article(article)
            save_article(record)
            count += 1
        except Exception as e:
            print(f"⚠️ Error saving article: {e}")
    return count


def get_article_by_url(url: str) -> Optional[ArticleRecord]:
    """Get article by URL."""
    url_hash = hashlib.sha1(url.encode()).hexdigest()[:16]
    
    with get_cursor() as cursor:
        cursor.execute("SELECT * FROM articles WHERE url_hash = ?", (url_hash,))
        row = cursor.fetchone()
        if row:
            return ArticleRecord.from_row(row)
    return None


def get_article_by_id(article_id: int) -> Optional[ArticleRecord]:
    """Get article by ID."""
    with get_cursor() as cursor:
        cursor.execute("SELECT * FROM articles WHERE id = ?", (article_id,))
        row = cursor.fetchone()
        if row:
            return ArticleRecord.from_row(row)
    return None


def get_recent_articles(
    limit: int = 100,
    category: Optional[str] = None,
    days: int = 7
) -> list[ArticleRecord]:
    """
    Get recent articles from database.
    
    Args:
        limit: Maximum articles to return
        category: Filter by category (optional)
        days: Only articles from last N days
        
    Returns:
        List of ArticleRecord objects
    """
    query = """
        SELECT * FROM articles
        WHERE created_at >= datetime('now', ?)
    """
    params = [f"-{days} days"]
    
    if category:
        query += " AND category = ?"
        params.append(category)
    
    query += " ORDER BY final_score DESC LIMIT ?"
    params.append(limit)
    
    with get_cursor() as cursor:
        cursor.execute(query, params)
        return [ArticleRecord.from_row(row) for row in cursor.fetchall()]


def get_articles_for_digest(
    start_date: datetime,
    end_date: datetime,
    limit: int = 100
) -> list[ArticleRecord]:
    """Get articles for a digest period."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT * FROM articles
            WHERE published_at BETWEEN ? AND ?
            ORDER BY final_score DESC
            LIMIT ?
        """, (start_date, end_date, limit))
        return [ArticleRecord.from_row(row) for row in cursor.fetchall()]


def delete_old_articles(days: int = 90) -> int:
    """Delete articles older than N days."""
    with get_cursor() as cursor:
        cursor.execute("""
            DELETE FROM articles
            WHERE created_at < datetime('now', ?)
        """, (f"-{days} days",))
        return cursor.rowcount


def article_exists(url: str) -> bool:
    """Check if article already exists in database."""
    url_hash = hashlib.sha1(url.encode()).hexdigest()[:16]
    
    with get_cursor() as cursor:
        cursor.execute("SELECT 1 FROM articles WHERE url_hash = ?", (url_hash,))
        return cursor.fetchone() is not None


# =============================================================================
# SUMMARY CRUD OPERATIONS
# =============================================================================

def save_summary(record: SummaryRecord) -> int:
    """Save AI summary to database."""
    with get_cursor() as cursor:
        cursor.execute("""
            INSERT INTO ai_summaries (article_id, provider, model, summary_text, token_count)
            VALUES (?, ?, ?, ?, ?)
        """, (record.article_id, record.provider, record.model, 
              record.summary_text, record.token_count))
        return cursor.lastrowid


def get_summary_for_article(article_id: int) -> Optional[SummaryRecord]:
    """Get most recent summary for an article."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT * FROM ai_summaries
            WHERE article_id = ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (article_id,))
        row = cursor.fetchone()
        if row:
            return SummaryRecord.from_row(row)
    return None


# =============================================================================
# DIGEST CRUD OPERATIONS
# =============================================================================

def save_digest(record: DigestRecord) -> int:
    """Save digest to database."""
    with get_cursor() as cursor:
        cursor.execute("""
            INSERT INTO digests (period_start, period_end, digest_type, 
                                digest_text, article_count, provider, model)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (record.period_start, record.period_end, record.digest_type,
              record.digest_text, record.article_count, record.provider, record.model))
        return cursor.lastrowid


def get_recent_digests(limit: int = 10) -> list[DigestRecord]:
    """Get recent digests."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT * FROM digests
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        return [DigestRecord.from_row(row) for row in cursor.fetchall()]


def get_digest_for_period(start: datetime, end: datetime) -> Optional[DigestRecord]:
    """Get digest for a specific period if it exists."""
    with get_cursor() as cursor:
        cursor.execute("""
            SELECT * FROM digests
            WHERE period_start = ? AND period_end = ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (start, end))
        row = cursor.fetchone()
        if row:
            return DigestRecord.from_row(row)
    return None
