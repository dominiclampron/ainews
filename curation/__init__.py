# curation/__init__.py
"""
Curation module - Contains clustering, classification, scoring, and selection algorithms.
"""

from curation.clusterer import (
    ArticleCluster,
    SemanticClusterer,
    cluster_articles_tfidf,
)
from curation.classifier import (
    ClassificationResult,
    SemanticClassifier,
    classify_article_enhanced,
    classify_with_confidence,
)
from curation.precision import (
    is_spacy_available,
    PrecisionClassifier,
    classify_with_precision,
)

__all__ = [
    # Clustering
    "ArticleCluster",
    "SemanticClusterer",
    "cluster_articles_tfidf",
    # Classification
    "ClassificationResult",
    "SemanticClassifier",
    "classify_article_enhanced",
    "classify_with_confidence",
    # Precision Mode (optional spaCy)
    "is_spacy_available",
    "PrecisionClassifier",
    "classify_with_precision",
]
