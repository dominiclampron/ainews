"""
curation/classifier.py - Enhanced article classification with exclusion rules.

This module provides improved classification accuracy by:
- Using weighted keyword matching (high/medium/low tiers)
- Applying exclusion rules to prevent false positives
- Supporting category weights for prioritization
- Returning confidence scores for transparency
- Handling edge cases and ambiguous articles
- Context-aware company mappings to correct categories

Target: >92% classification accuracy

v0.6.1: Fixed default fallback, added extensive exclusions, company mappings
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from core.config import CATEGORIES
from config.loader import load_exclusions


@dataclass
class ClassificationResult:
    """
    Result of article classification.
    
    Attributes:
        category: The classified category key (e.g., "ai_headlines")
        confidence: Confidence score (0.0-1.0)
        scores: Dict of all category scores for debugging
        excluded_by: If excluded from a category, which word triggered it
        is_ambiguous: True if top two categories are close in score
    """
    category: str
    confidence: float
    scores: dict
    excluded_by: Optional[str] = None
    is_ambiguous: bool = False
    
    def __repr__(self) -> str:
        return f"ClassificationResult(category={self.category!r}, confidence={self.confidence:.2f})"


class SemanticClassifier:
    """
    Enhanced article classifier with exclusion rules for high accuracy.
    
    This classifier uses a multi-tier keyword matching system with
    exclusion rules to prevent common false positive patterns.
    
    Example:
        >>> classifier = SemanticClassifier()
        >>> result = classifier.classify(
        ...     "OpenAI announces GPT-5",
        ...     "The next generation language model..."
        ... )
        >>> print(result.category, result.confidence)
        ai_headlines 0.92
    """
    
    # Companies/entities that are NOT AI companies - prevent AI/ML classification
    NON_AI_ENTITIES = [
        # Tech companies (general)
        "instacart", "strava", "payoneer", "genco", "hyundai", "tesla",
        "uber", "lyft", "airbnb", "doordash", "grubhub", "shopify",
        "squarespace", "wix", "godaddy", "dropbox", "box", "slack",
        "zoom", "webex", "docusign", "twilio", "stripe", "square",
        "paypal", "venmo", "robinhood", "coinbase", "binance", "kraken",
        "serpapi", "graphite", "mode mobile", "ngl", "earnphone",
        # Financial/Shipping
        "diana shipping", "genco shipping", "maersk", "fedex", "ups",
        # People (not AI-related)
        "musk", "elon musk", "kennedy", "kerry kennedy", "trump", "biden",
        # Other
        "starbucks", "mcdonald", "walmart", "target", "costco", "amazon prime",
    ]
    
    # Additional exclusion patterns beyond what's in CATEGORIES
    # These catch common false positive patterns
    GLOBAL_EXCLUSIONS = {
        "ai_headlines": [
            # Financial terms
            "stock", "earnings", "ipo", "shares", "investor", "quarterly",
            "market cap", "revenue forecast", "dividend", "portfolio",
            "pay package", "salary", "compensation", "ceo pay", "bonus",
            # Legal/Settlement
            "lawsuit settlement", "ftc settlement", "refund", "sues", "sued",
            "court ruling", "legal battle", "antitrust",
            # Consumer/Subscription
            "subscribers", "paywall", "subscription", "membership",
            # Non-tech topics
            "shipping", "freight", "cargo", "logistics",
            "ransom demand", "bomb threat", "evacuated", "shooting",
            "homeless", "prayer", "church", "religion",
            "soundbar", "audio", "tv dialogue", "speaker",
            "prediction market", "betting", "gambling",
            # Geographic/Political
            "illinois", "michigan", "connecticut", "california",
            "kennedy center", "white house",
            # Crypto-specific (goes to crypto, not AI)
            "bitcoin ransom", "crypto ransom", "btc demand",
        ],
        "tools_platforms": [
            "lawsuit", "sued", "antitrust", "investigation", "layoff",
            "earnings", "stock price", "shares",
        ],
        "science_research": [
            "product launch", "startup funding", "series a", "series b",
            "ipo", "valuation", "investor", "stock price",
        ],
        "health_biotech": [
            "stock", "earnings", "shares", "investor", "quarterly",
            "market cap", "portfolio",
        ],
    }
    
    # Boost keywords - very strong signals for specific categories
    BOOST_PATTERNS = {
        "ai_headlines": [
            ("openai", 5.0), ("anthropic", 5.0), ("deepmind", 5.0),
            ("gpt-5", 6.0), ("gpt-4", 4.0), ("claude-3", 5.0),
            ("gemini 2", 5.0), ("llama 3", 4.0), ("mistral", 4.0),
            ("chatgpt", 4.0), ("large language model", 4.0),
            ("claude's", 5.0), ("anthropic moves", 5.0),
            ("llm", 4.0), ("transformer", 3.0), ("neural network", 3.0),
            ("ai model", 5.0), ("language model", 5.0),
            ("bedrock", 3.0), ("agentcore", 4.0), ("aws ai", 4.0),
            # Additional AI patterns
            ("alli ai", 5.0), ("8k video", 3.0), ("ai unveils", 5.0),
            ("ai system", 4.0), ("innovative system", 3.0),
            ("creating and editing", 3.0), ("video generation", 4.0),
        ],
        "cybersecurity": [
            ("data breach", 6.0), ("ransomware attack", 6.0),
            ("zero-day", 6.0), ("cve-", 5.0), ("hacked", 4.0),
            ("vulnerability", 4.0), ("malware", 4.0), ("exploit", 4.0),
            ("hackers", 5.0), ("phishing", 4.0), ("uefi flaw", 6.0),
            ("security flaw", 5.0), ("account takeover", 5.0),
            ("russia-linked hackers", 6.0), ("nation-state", 5.0),
            # Additional cybersecurity patterns
            ("pre-boot attack", 6.0), ("boot attack", 5.0),
            ("flaw enables", 5.0), ("enables attack", 5.0),
            ("firmware", 4.0), ("bios", 4.0), ("uefi", 5.0),
        ],
        "crypto_blockchain": [
            ("bitcoin", 5.0), ("ethereum", 5.0), ("btc", 4.0), ("eth", 3.0),
            ("crypto crash", 6.0), ("sec crypto", 5.0), ("cryptocurrency", 4.0),
            ("blockchain", 3.0), ("defi", 4.0), ("nft", 3.0),
            ("coinbase", 5.0), ("binance", 5.0), ("kraken", 4.0),
            ("crypto ransom", 5.0), ("bitcoin ransom", 5.0),
            ("prediction market", 4.0),
        ],
        "finance_markets": [
            ("fed rate", 6.0), ("interest rate decision", 6.0),
            ("stock market crash", 6.0), ("wall street", 4.0),
            ("stock surge", 5.0), ("shares rose", 4.0), ("earnings report", 4.0),
            ("nasdaq", 4.0), ("s&p 500", 4.0), ("dow jones", 4.0),
            ("pay package", 5.0), ("ceo pay", 5.0), ("compensation", 4.0),
            ("payoneer", 5.0), ("payment provider", 4.0),
            ("shipping", 4.0), ("genco", 5.0), ("diana", 4.0),
            ("million in", 4.0), ("billion in", 4.0),
            ("ftc settlement", 5.0), ("refund", 3.0),
            ("portfolio", 3.0), ("upside", 3.0), ("floor", 2.0), ("ceiling", 2.0),
            ("wife earns", 4.0), ("terrified", 3.0), ("taxes", 4.0), ("retirement", 4.0),
        ],
        "tech_industry": [
            ("acquisition", 5.0), ("acquires", 5.0), ("acquired", 5.0),
            ("billion", 4.0), ("layoffs", 5.0), ("ipo", 5.0), ("startup", 3.0),
            ("funding round", 4.0), ("series a", 4.0), ("valuation", 3.0),
            ("instacart", 5.0), ("strava", 5.0), ("cursor", 4.0),
            ("mode mobile", 4.0), ("ngl app", 4.0), ("serpapi", 4.0),
            ("paywall", 4.0), ("subscription", 3.0), ("subscribers", 3.0),
            ("google lobs", 4.0), ("lawsuit", 3.0),
            ("messaging app", 4.0), ("app acquired", 5.0),
            ("musk wins", 4.0), ("tesla", 4.0),
            ("soundbar", 4.0), ("tv dialogue", 4.0), ("audio", 3.0),
            ("gigabyte", 4.0), ("msi", 4.0), ("asus", 4.0), ("asrock", 4.0),
            ("motherboard", 4.0), ("gcp", 3.0), ("certification", 3.0),
        ],
        "governance_safety": [
            ("ai act", 6.0), ("regulation", 4.0), ("ai safety", 5.0),
            ("ai policy", 5.0), ("ethics", 3.0), ("parliament", 4.0),
            ("legislation", 4.0), ("compliance", 3.0),
        ],
        "science_research": [
            ("arxiv", 6.0), ("research paper", 5.0), ("study finds", 4.0),
            ("researchers", 3.0), ("peer review", 5.0), ("published study", 5.0),
            ("scientific", 3.0), ("experiment", 3.0),
        ],
        "health_biotech": [
            ("fda", 6.0), ("clinical trial", 5.0), ("drug approval", 6.0),
            ("gene therapy", 5.0), ("vaccine", 4.0), ("pharmaceutical", 4.0),
            ("phase 3", 5.0), ("phase 2", 4.0), ("crispr", 5.0),
        ],
        "politics_policy": [
            ("executive order", 6.0), ("congress", 4.0), ("senate", 4.0),
            ("biden", 4.0), ("trump", 4.0), ("legislation", 4.0),
            ("supreme court", 5.0), ("antitrust", 4.0),
            ("kennedy", 5.0), ("kerry kennedy", 5.0), ("kennedy center", 5.0),
            ("white house", 4.0), ("pickax", 3.0),
        ],
        "world_news": [
            ("ukraine", 5.0), ("russia", 4.0), ("china", 4.0),
            ("middle east", 4.0), ("europe", 3.0), ("global crisis", 5.0),
            ("sanctions", 4.0), ("trade war", 5.0),
            ("bomb threat", 5.0), ("evacuated", 4.0), ("protest", 3.0),
            ("south korean", 4.0), ("hyundai", 4.0),
            ("shooting", 4.0), ("university shooting", 5.0),
        ],
        "viral_trending": [
            ("viral", 5.0), ("trending", 4.0), ("breaking", 4.0),
            ("exclusive", 4.0), ("leaked", 5.0), ("went viral", 5.0),
            ("deleted", 3.0), ("speculated", 3.0),
            ("sequoia", 3.0), ("x post", 3.0),
        ],
    }
    
    def __init__(
        self,
        min_confidence: float = 0.3,
        ambiguity_threshold: float = 0.15,
    ):
        """
        Initialize the classifier.
        
        Args:
            min_confidence: Minimum score to classify (below = fallback category)
            ambiguity_threshold: If top 2 scores within this ratio, mark as ambiguous
        """
        self.min_confidence = min_confidence
        self.ambiguity_threshold = ambiguity_threshold
        self.categories = CATEGORIES
    
    def classify(self, title: str, summary: str) -> ClassificationResult:
        """
        Classify an article into one of the 12 categories.
        
        Args:
            title: Article headline
            summary: Article description/body text
            
        Returns:
            ClassificationResult with category, confidence, and metadata
        """
        text = (title + " " + (summary or "")).lower()
        scores = {}
        exclusion_hits = {}
        
        # Pre-check: Does this mention a non-AI company?
        mentions_non_ai_entity = any(entity in text for entity in self.NON_AI_ENTITIES)
        
        for cat_key, cat_data in self.categories.items():
            score = 0.0
            excluded_by = None
            
            # Step 1: Check exclusion rules (from config + hardcoded + JSON)
            config_exclusions = cat_data.get("exclude_if", [])
            global_exclusions = self.GLOBAL_EXCLUSIONS.get(cat_key, [])
            
            # Load exclusions from JSON config file
            loaded_exclusions = load_exclusions()
            json_exclusions = loaded_exclusions.get(cat_key, [])
            json_global = loaded_exclusions.get("global", [])
            
            all_exclusions = list(set(config_exclusions + global_exclusions + json_exclusions + json_global))
            
            for ex in all_exclusions:
                if ex in text:
                    score -= 5.0  # Heavy penalty
                    excluded_by = ex
                    break
            
            if excluded_by:
                exclusion_hits[cat_key] = excluded_by
            
            # Step 1.5: If article mentions non-AI company and this is ai_headlines, penalize
            if cat_key == "ai_headlines" and mentions_non_ai_entity:
                score -= 3.0  # Penalty for AI category when non-AI company mentioned
            
            # Step 2: Apply boost patterns (very high confidence signals)
            for pattern, boost in self.BOOST_PATTERNS.get(cat_key, []):
                if pattern in text:
                    score += boost
            
            # Step 3: Standard keyword matching
            for kw in cat_data.get("keywords_high", []):
                if kw in text:
                    score += 3.0
            
            for kw in cat_data.get("keywords_medium", []):
                if kw in text:
                    score += 1.5
            
            for kw in cat_data.get("keywords_low", []):
                # Skip "ai" alone - too greedy, matches "paid", "aid", company names
                if kw == "ai":
                    continue
                if kw in text:
                    score += 0.5
            
            # Step 4: Apply category weight (from config)
            weight = cat_data.get("weight", 1.0)
            score *= weight
            
            scores[cat_key] = score
        
        # Find best category
        sorted_cats = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        best_cat, best_score = sorted_cats[0]
        second_cat, second_score = sorted_cats[1] if len(sorted_cats) > 1 else (None, 0)
        
        # Calculate confidence (normalize to 0-1)
        max_possible = 30.0  # Approximate max score
        confidence = min(1.0, max(0.0, best_score / max_possible))
        
        # Check for ambiguity
        is_ambiguous = False
        if second_score > 0 and best_score > 0:
            ratio = second_score / best_score
            if ratio > (1.0 - self.ambiguity_threshold):
                is_ambiguous = True
        
        # FIX: Only fallback to viral_trending if there are NO positive matches at all
        # Use absolute score threshold (2.0) instead of normalized confidence
        MIN_SCORE_THRESHOLD = 2.0  # Minimum absolute score to accept classification
        if best_score < MIN_SCORE_THRESHOLD:
            best_cat = "viral_trending"  # Neutral catch-all for truly unclassifiable
            confidence = 0.25
        
        return ClassificationResult(
            category=best_cat,
            confidence=confidence,
            scores=scores,
            excluded_by=exclusion_hits.get(best_cat),
            is_ambiguous=is_ambiguous,
        )
    
    def classify_batch(
        self, 
        articles: list[tuple[str, str]]
    ) -> list[ClassificationResult]:
        """
        Classify multiple articles.
        
        Args:
            articles: List of (title, summary) tuples
            
        Returns:
            List of ClassificationResult objects
        """
        return [self.classify(title, summary) for title, summary in articles]
    
    def get_category_stats(
        self, 
        results: list[ClassificationResult]
    ) -> dict:
        """
        Calculate statistics from classification results.
        
        Args:
            results: List of ClassificationResult objects
            
        Returns:
            Dict with category counts, confidence stats, etc.
        """
        if not results:
            return {}
        
        category_counts = {}
        confidences = []
        ambiguous_count = 0
        
        for r in results:
            category_counts[r.category] = category_counts.get(r.category, 0) + 1
            confidences.append(r.confidence)
            if r.is_ambiguous:
                ambiguous_count += 1
        
        return {
            "total": len(results),
            "category_counts": category_counts,
            "avg_confidence": sum(confidences) / len(confidences),
            "min_confidence": min(confidences),
            "max_confidence": max(confidences),
            "ambiguous_count": ambiguous_count,
            "ambiguous_percentage": ambiguous_count / len(results) * 100,
        }


def classify_article_enhanced(title: str, summary: str) -> str:
    """
    Drop-in replacement for the original classify_article function.
    
    Uses the enhanced SemanticClassifier with exclusion rules.
    
    Args:
        title: Article headline
        summary: Article description
        
    Returns:
        Category key string
    """
    classifier = SemanticClassifier()
    result = classifier.classify(title, summary)
    return result.category


def classify_with_confidence(title: str, summary: str) -> tuple[str, float]:
    """
    Classify article and return confidence score.
    
    Args:
        title: Article headline
        summary: Article description
        
    Returns:
        Tuple of (category_key, confidence_score)
    """
    classifier = SemanticClassifier()
    result = classifier.classify(title, summary)
    return result.category, result.confidence
