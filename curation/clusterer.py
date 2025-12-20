"""
curation/clusterer.py - TF-IDF Semantic Clustering for article deduplication and grouping.

This module provides intelligent clustering of similar articles using TF-IDF vectorization
and cosine similarity, replacing the simpler SequenceMatcher approach.

Features:
- TF-IDF vectorization of article titles + summaries
- Cosine similarity matrix for finding related articles
- Configurable similarity threshold (default 0.75)
- Multi-source article grouping with score boosting
- Cluster statistics and metrics
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from core.article import Article


@dataclass
class ArticleCluster:
    """
    Represents a cluster of similar articles covering the same story.
    
    Attributes:
        cluster_id: Unique identifier for this cluster
        primary: The highest-scoring article (main display)
        variants: List of (article, similarity_score) tuples
        created_at: When cluster was created
    """
    cluster_id: str
    primary: Article
    variants: list = field(default_factory=list)  # List of (Article, float) tuples
    
    @property
    def num_sources(self) -> int:
        """Total number of sources in this cluster."""
        return 1 + len(self.variants)
    
    @property
    def is_multi_source(self) -> bool:
        """True if cluster has articles from multiple sources."""
        return len(self.variants) > 0
    
    def get_all_sources(self) -> list[str]:
        """Get list of all source domains in cluster."""
        sources = [self.primary.outlet_key]
        sources.extend(art.outlet_key for art, _ in self.variants)
        return sources
    
    def get_variant_links(self) -> list[tuple[str, str]]:
        """Get (outlet, url) tuples for template rendering."""
        return [(art.outlet, art.url) for art, _ in self.variants]


class SemanticClusterer:
    """
    Groups similar articles using TF-IDF vectorization and cosine similarity.
    
    This replaces the simpler SequenceMatcher approach with proper NLP-based
    text vectorization for more accurate similarity detection.
    
    Args:
        similarity_threshold: Minimum cosine similarity to consider articles related (0.0-1.0)
        max_variants: Maximum number of variant articles per cluster
        boost_per_source: Score boost percentage per additional source (0.0-1.0)
        max_boost: Maximum total boost from multi-source (0.0-1.0)
    
    Example:
        >>> clusterer = SemanticClusterer(similarity_threshold=0.75)
        >>> clusters = clusterer.cluster_articles(articles)
        >>> print(f"Created {len(clusters)} clusters")
        >>> stats = clusterer.get_cluster_stats(clusters)
        >>> print(f"Multi-source: {stats['multi_source_percentage']:.1f}%")
    """
    
    def __init__(
        self,
        similarity_threshold: float = 0.75,
        max_variants: int = 2,
        boost_per_source: float = 0.15,
        max_boost: float = 0.50,
    ):
        self.similarity_threshold = similarity_threshold
        self.max_variants = max_variants
        self.boost_per_source = boost_per_source
        self.max_boost = max_boost
        
        # TF-IDF vectorizer configuration
        self.vectorizer = TfidfVectorizer(
            max_features=500,          # Limit vocabulary size for performance
            stop_words='english',       # Remove common words
            ngram_range=(1, 2),         # Use unigrams and bigrams
            min_df=1,                   # Include rare terms
            max_df=0.95,                # Exclude very common terms
            lowercase=True,
            strip_accents='unicode',
        )
    
    def cluster_articles(self, articles: list[Article]) -> list[Article]:
        """
        Cluster similar articles and return primary articles with related_articles populated.
        
        This is the main entry point. It:
        1. Creates TF-IDF vectors from article text
        2. Calculates cosine similarity matrix
        3. Groups similar articles into clusters
        4. Returns primary articles with variants attached
        
        Args:
            articles: List of Article objects to cluster
            
        Returns:
            List of primary Article objects with related_articles populated
        """
        if not articles or len(articles) < 2:
            return articles
        
        # Sort by score descending - highest scored will be cluster primaries
        sorted_articles = sorted(articles, key=lambda x: x.final_score, reverse=True)
        
        # Step 1: Create text representations for TF-IDF
        texts = [self._get_article_text(a) for a in sorted_articles]
        
        # Step 2: Vectorize and calculate similarity matrix
        try:
            similarity_matrix = self._calculate_similarity_matrix(texts)
        except ValueError as e:
            # Fallback if vectorization fails (e.g., all empty texts)
            print(f"⚠️ TF-IDF vectorization failed: {e}, using fallback")
            return self._fallback_clustering(sorted_articles)
        
        # Step 3: Build clusters using greedy algorithm
        clusters = self._build_clusters(sorted_articles, similarity_matrix)
        
        # Step 4: Convert clusters to articles with related_articles
        return self._process_clusters(clusters)
    
    def _get_article_text(self, article: Article) -> str:
        """Extract text for TF-IDF vectorization."""
        # Combine title (weighted more) and summary
        title = article.title.lower().strip()
        summary = article.summary.lower().strip() if article.summary else ""
        
        # Weight title more by repeating it
        return f"{title} {title} {summary}"
    
    def _calculate_similarity_matrix(self, texts: list[str]) -> np.ndarray:
        """Calculate pairwise cosine similarity matrix."""
        # Fit and transform texts to TF-IDF vectors
        tfidf_matrix = self.vectorizer.fit_transform(texts)
        
        # Calculate cosine similarity
        similarity_matrix = cosine_similarity(tfidf_matrix)
        
        return similarity_matrix
    
    def _build_clusters(
        self, 
        articles: list[Article], 
        similarity_matrix: np.ndarray
    ) -> list[ArticleCluster]:
        """Build clusters using greedy algorithm."""
        n = len(articles)
        clustered = set()
        clusters = []
        
        for i in range(n):
            if i in clustered:
                continue
            
            # Start new cluster with this article as primary
            primary = articles[i]
            cluster_id = hashlib.md5(primary.title.lower().encode()).hexdigest()[:8]
            cluster = ArticleCluster(cluster_id=cluster_id, primary=primary)
            clustered.add(i)
            
            # Find similar articles from different sources
            similar_candidates = []
            for j in range(n):
                if j in clustered:
                    continue
                
                # Skip same source (we want different sources)
                if articles[j].outlet_key == primary.outlet_key:
                    continue
                
                similarity = similarity_matrix[i, j]
                if similarity >= self.similarity_threshold:
                    similar_candidates.append((j, articles[j], similarity))
            
            # Sort by similarity and take top max_variants
            similar_candidates.sort(key=lambda x: x[2], reverse=True)
            
            for j, article, similarity in similar_candidates[:self.max_variants]:
                cluster.variants.append((article, float(similarity)))
                clustered.add(j)
            
            clusters.append(cluster)
        
        return clusters
    
    def _process_clusters(self, clusters: list[ArticleCluster]) -> list[Article]:
        """Convert clusters to articles with related_articles populated."""
        result = []
        
        for cluster in clusters:
            primary = cluster.primary
            primary.is_cluster_primary = True
            primary.cluster_id = cluster.cluster_id
            
            # Add variant sources as related_articles
            if cluster.variants:
                primary.related_articles = cluster.get_variant_links()
                
                # Boost score for multi-source stories
                num_sources = cluster.num_sources
                boost = min(self.max_boost, num_sources * self.boost_per_source)
                primary.final_score = primary.final_score * (1 + boost)
            
            result.append(primary)
            
            # Mark non-primaries
            for variant_article, _ in cluster.variants:
                variant_article.is_cluster_primary = False
                variant_article.cluster_id = cluster.cluster_id
        
        return result
    
    def _fallback_clustering(self, articles: list[Article]) -> list[Article]:
        """Fallback to simple title-based clustering if TF-IDF fails."""
        from difflib import SequenceMatcher
        
        clustered = set()
        result = []
        
        for i, article in enumerate(articles):
            if i in clustered:
                continue
            
            article.is_cluster_primary = True
            article.cluster_id = hashlib.md5(article.title.lower().encode()).hexdigest()[:8]
            clustered.add(i)
            
            # Find similar by title
            variants = []
            for j, other in enumerate(articles):
                if j in clustered or other.outlet_key == article.outlet_key:
                    continue
                
                ratio = SequenceMatcher(None, article.title.lower(), other.title.lower()).ratio()
                if ratio >= 0.55 and len(variants) < self.max_variants:
                    variants.append((other.outlet, other.url))
                    clustered.add(j)
            
            if variants:
                article.related_articles = variants
                boost = min(self.max_boost, len(variants) * self.boost_per_source)
                article.final_score = article.final_score * (1 + boost)
            
            result.append(article)
        
        return result
    
    def get_cluster_stats(self, clusters: list[ArticleCluster]) -> dict:
        """
        Calculate statistics about clustering results.
        
        Args:
            clusters: List of ArticleCluster objects
            
        Returns:
            Dictionary with clustering metrics
        """
        if not clusters:
            return {
                'total_clusters': 0,
                'total_articles': 0,
                'multi_source_clusters': 0,
                'multi_source_percentage': 0.0,
                'avg_variants_per_cluster': 0.0,
                'reduction_ratio': 1.0,
            }
        
        total_articles = sum(1 + len(c.variants) for c in clusters)
        multi_source = sum(1 for c in clusters if c.is_multi_source)
        total_variants = sum(len(c.variants) for c in clusters)
        
        return {
            'total_clusters': len(clusters),
            'total_articles': total_articles,
            'multi_source_clusters': multi_source,
            'multi_source_percentage': (multi_source / len(clusters) * 100) if clusters else 0,
            'avg_variants_per_cluster': total_variants / len(clusters) if clusters else 0,
            'reduction_ratio': total_articles / len(clusters) if clusters else 1,
        }


def cluster_articles_tfidf(
    articles: list[Article],
    similarity_threshold: float = 0.75,
    max_variants: int = 2,
) -> list[Article]:
    """
    Convenience function for clustering articles with TF-IDF.
    
    This is a drop-in replacement for the old cluster_similar_articles function.
    
    Args:
        articles: List of articles to cluster
        similarity_threshold: Minimum similarity (0.0-1.0)
        max_variants: Maximum related articles per cluster
        
    Returns:
        List of primary articles with related_articles populated
    """
    clusterer = SemanticClusterer(
        similarity_threshold=similarity_threshold,
        max_variants=max_variants,
    )
    return clusterer.cluster_articles(articles)
