"""
core/article.py - Article dataclass definition.

The Article dataclass represents a single news article with all its metadata,
scoring components, and clustering information.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Article:
    """
    Represents a single news article with metadata and scoring.
    
    Attributes:
        title: Article headline
        url: Full URL to the article
        outlet: Human-readable source name (e.g., "TechCrunch")
        outlet_key: Domain key for grouping (e.g., "techcrunch.com")
        published: Publication datetime (timezone-aware)
        summary: Article description/summary text
        image_url: OpenGraph or feed image URL
        category: Classified category key (e.g., "ai_headlines")
        
    Scoring Components:
        recency_score: 0.0-1.0 score based on age (newer = higher)
        importance_score: 0.0-1.0 score based on keywords
        source_score: 0.0-1.0 score based on source reputation
        final_score: Weighted composite score
        
    Metadata:
        priority: "breaking", "important", or "normal"
        why_matters: Generated contextual explanation
        
    Clustering (Phase 3+):
        related_articles: List of (outlet, url) tuples for same story
        cluster_id: Unique ID for story cluster
        is_cluster_primary: True if this is the main article in cluster
        
    UI:
        reading_time_min: Estimated reading time in minutes
    """
    # Required fields
    title: str
    url: str
    outlet: str
    outlet_key: str
    published: Optional[dt.datetime]
    summary: str
    image_url: Optional[str]
    category: str = "ai_headlines"
    
    # Scoring components
    recency_score: float = 0.0
    importance_score: float = 0.0
    source_score: float = 0.0
    final_score: float = 0.0
    
    # Metadata
    priority: str = "normal"  # breaking, important, normal
    why_matters: str = ""
    
    # Phase 3: Multi-source clustering
    related_articles: list = field(default_factory=list)  # List of (outlet, url) tuples
    cluster_id: Optional[str] = None  # ID for grouping same story
    is_cluster_primary: bool = True  # Is this the primary article for the cluster?
    
    # Phase 3: Reading time
    reading_time_min: int = 0  # Estimated reading time in minutes
    
    # v0.7: Classification transparency (opt-in display via --debug-classify)
    classification_confidence: float = 0.0  # 0.0-1.0 confidence in category
    classification_runner_up: Optional[str] = None  # Second-best category
    classification_signals: dict = field(default_factory=dict)  # Contributing factors
    entities_detected: list = field(default_factory=list)  # NER entities found
    secondary_categories: list = field(default_factory=list)  # Multi-category support (internal)
    
    def __repr__(self) -> str:
        """Short representation for debugging."""
        return f"Article(title={self.title[:50]!r}..., outlet={self.outlet!r}, score={self.final_score:.2f})"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for template rendering."""
        return {
            "title": self.title,
            "url": self.url,
            "outlet": self.outlet,
            "outlet_key": self.outlet_key,
            "published": self.published,
            "summary": self.summary,
            "image_url": self.image_url,
            "category": self.category,
            "recency_score": self.recency_score,
            "importance_score": self.importance_score,
            "source_score": self.source_score,
            "final_score": self.final_score,
            "priority": self.priority,
            "why_matters": self.why_matters,
            "related_articles": self.related_articles,
            "cluster_id": self.cluster_id,
            "is_cluster_primary": self.is_cluster_primary,
            "reading_time_min": self.reading_time_min,
        }
