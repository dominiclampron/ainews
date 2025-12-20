"""
curation/metrics.py - v0.7 Metrics and transparency features.

Provides:
- Entity extraction statistics
- A/B comparison (Standard vs Precision)
- Classification confidence aggregation
- Scoring breakdown display

All features are opt-in via CLI flags (--metrics, --ab-precision, --debug-classify, --explain-score)
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from core.article import Article


@dataclass
class EntityStats:
    """Statistics about extracted entities."""
    total_count: int = 0
    unique_count: int = 0
    by_type: Dict[str, int] = field(default_factory=dict)
    avg_per_article: float = 0.0
    
    def to_summary(self) -> str:
        """Format as terminal summary."""
        lines = [
            f"   Total entities: {self.total_count:,} (avg {self.avg_per_article:.1f}/article)",
        ]
        if self.by_type:
            type_parts = [f"{t}: {c}" for t, c in sorted(self.by_type.items(), key=lambda x: -x[1])[:6]]
            lines.append(f"   {' | '.join(type_parts)}")
        return "\n".join(lines)


@dataclass
class ABComparisonResult:
    """Results of A/B comparison between Standard and Precision classification."""
    total_articles: int = 0
    agreement_count: int = 0
    agreement_rate: float = 0.0
    category_shifts: Dict[str, Dict[str, int]] = field(default_factory=dict)  # from -> to -> count
    high_disagreement: List[Tuple[str, str, str, str]] = field(default_factory=list)  # title, url, std, prec
    
    standard_confidence_avg: float = 0.0
    precision_confidence_avg: float = 0.0
    
    def to_summary(self) -> str:
        """Format as terminal summary."""
        lines = [
            f"   Agreement: {self.agreement_rate:.1f}% ({self.agreement_count}/{self.total_articles} same category)",
        ]
        
        if self.category_shifts:
            lines.append(f"   Category shifts: {self.total_articles - self.agreement_count} articles changed")
            shift_items = []
            for from_cat, to_dict in sorted(self.category_shifts.items()):
                for to_cat, count in sorted(to_dict.items(), key=lambda x: -x[1])[:3]:
                    shift_items.append(f"     {from_cat} → {to_cat}: {count}")
            lines.extend(shift_items[:5])
        
        if self.standard_confidence_avg > 0:
            lines.append(f"   Avg confidence: Standard {self.standard_confidence_avg:.2f} | Precision {self.precision_confidence_avg:.2f}")
        
        return "\n".join(lines)


@dataclass 
class ConfidenceStats:
    """Statistics about classification confidence."""
    min_confidence: float = 0.0
    max_confidence: float = 0.0
    avg_confidence: float = 0.0
    median_confidence: float = 0.0
    p95_confidence: float = 0.0
    low_confidence_count: int = 0  # Below 0.5
    high_confidence_count: int = 0  # Above 0.8


def calculate_entity_stats(articles: List[Article]) -> EntityStats:
    """Calculate entity statistics from articles."""
    stats = EntityStats()
    
    all_entities = []
    type_counter = Counter()
    
    for article in articles:
        if hasattr(article, 'entities_detected') and article.entities_detected:
            for entity_text, entity_type in article.entities_detected:
                all_entities.append((entity_text, entity_type))
                type_counter[entity_type] += 1
    
    if all_entities:
        stats.total_count = len(all_entities)
        stats.unique_count = len(set(e[0] for e in all_entities))
        stats.by_type = dict(type_counter)
        stats.avg_per_article = len(all_entities) / len(articles) if articles else 0
    
    return stats


def run_ab_comparison(articles: List[Article]) -> ABComparisonResult:
    """
    Run A/B comparison between Standard and Precision classification.
    
    Classifies each article with both methods and compares results.
    """
    from curation.classifier import SemanticClassifier, classify_article_enhanced
    from curation.precision import is_spacy_available, PrecisionClassifier
    
    result = ABComparisonResult()
    result.total_articles = len(articles)
    
    if not articles:
        return result
    
    # Standard classifier
    standard_classifier = SemanticClassifier()
    
    # Precision classifier (if available)
    precision_available = is_spacy_available()
    precision_classifier = PrecisionClassifier() if precision_available else None
    
    if not precision_available:
        print("⚠️  spaCy not available - A/B comparison requires precision mode")
        return result
    
    std_confidences = []
    prec_confidences = []
    
    for article in articles:
        # Standard classification
        std_result = standard_classifier.classify(article.title, article.summary)
        std_cat = std_result.category
        std_conf = std_result.confidence
        std_confidences.append(std_conf)
        
        # Precision classification
        prec_cat = precision_classifier.classify(article.title, article.summary)
        # Note: precision classifier returns just category string, not ClassificationResult
        prec_conf = 0.8  # Placeholder - precision doesn't return confidence yet
        prec_confidences.append(prec_conf)
        
        if std_cat == prec_cat:
            result.agreement_count += 1
        else:
            # Track category shift
            if std_cat not in result.category_shifts:
                result.category_shifts[std_cat] = {}
            if prec_cat not in result.category_shifts[std_cat]:
                result.category_shifts[std_cat][prec_cat] = 0
            result.category_shifts[std_cat][prec_cat] += 1
            
            # Track high disagreement
            result.high_disagreement.append((
                article.title[:60],
                article.url,
                std_cat,
                prec_cat
            ))
    
    result.agreement_rate = (result.agreement_count / result.total_articles) * 100 if result.total_articles else 0
    result.standard_confidence_avg = sum(std_confidences) / len(std_confidences) if std_confidences else 0
    result.precision_confidence_avg = sum(prec_confidences) / len(prec_confidences) if prec_confidences else 0
    
    # Sort high disagreement by most interesting
    result.high_disagreement = result.high_disagreement[:10]
    
    return result


def print_metrics_summary(
    articles: List[Article],
    entity_stats: Optional[EntityStats] = None,
    ab_result: Optional[ABComparisonResult] = None,
    precision_mode: bool = False
):
    """Print metrics summary to terminal."""
    print("\n" + "=" * 60)
    print("📊 METRICS SUMMARY")
    print("=" * 60)
    
    if precision_mode:
        print("\n🧠 Precision Mode: ON (spaCy NER)")
    else:
        print("\n🧠 Precision Mode: OFF (Standard)")
    
    print(f"   Articles analyzed: {len(articles)}")
    
    if entity_stats and entity_stats.total_count > 0:
        print("\n📊 Entity Statistics:")
        print(entity_stats.to_summary())
    
    if ab_result and ab_result.total_articles > 0:
        print("\n📈 A/B Comparison (Standard vs Precision):")
        print(ab_result.to_summary())
        
        if ab_result.high_disagreement:
            print("\n🔍 High Disagreement (first 5):")
            for title, url, std_cat, prec_cat in ab_result.high_disagreement[:5]:
                print(f"   {std_cat} → {prec_cat}: {title}...")
    
    print("\n" + "=" * 60)


def print_score_breakdown(articles: List[Article], top_n: int = 10):
    """Print scoring breakdown for top articles."""
    print("\n" + "=" * 60)
    print("📊 SCORING BREAKDOWN")
    print("=" * 60)
    
    # Sort by final score
    sorted_articles = sorted(articles, key=lambda x: x.final_score, reverse=True)[:top_n]
    
    for i, article in enumerate(sorted_articles, 1):
        print(f"\n{i}. \"{article.title[:50]}...\" (score: {article.final_score:.1f})")
        print(f"   recency: {article.recency_score:.2f} | importance: {article.importance_score:.2f} | source: {article.source_score:.2f}")
        if hasattr(article, 'classification_confidence') and article.classification_confidence > 0:
            print(f"   category: {article.category} (conf: {article.classification_confidence:.2f})")
    
    # Diversity summary
    sources = Counter(a.outlet_key for a in sorted_articles)
    categories = Counter(a.category for a in sorted_articles)
    
    print(f"\n📈 Diversity Summary (Top {top_n}):")
    print(f"   Unique sources: {len(sources)}")
    if sources:
        top_source = sources.most_common(1)[0]
        print(f"   Max per source: {top_source[1]} (from {top_source[0]})")
    print(f"   Categories: {len(categories)} represented")
    
    print("\n" + "=" * 60)


def print_classification_debug(article: Article):
    """Print detailed classification debug info for one article."""
    print(f"\n🔍 Classification Debug:")
    print(f"   Title: {article.title[:60]}...")
    
    if hasattr(article, 'classification_signals') and article.classification_signals:
        print(f"   Signals:")
        for signal, value in sorted(article.classification_signals.items(), key=lambda x: -x[1])[:5]:
            print(f"     {signal} = {value:.2f}")
    
    print(f"   Final: {article.category}")
    if hasattr(article, 'classification_confidence'):
        print(f"   Confidence: {article.classification_confidence:.2f}")
    if hasattr(article, 'classification_runner_up') and article.classification_runner_up:
        print(f"   Runner-up: {article.classification_runner_up}")
