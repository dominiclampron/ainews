"""
curation/precision.py - Optional spaCy-based precision mode for enhanced NER.

This module provides optional spaCy integration for higher-precision
entity recognition. It's disabled by default and only activates when:
1. The "precision" preset is selected
2. spaCy is installed (prompt to install if missing)

Features:
- Named Entity Recognition (NER) for company/product/person detection
- Enhanced boost patterns based on recognized entities
- Automatic spaCy model download if needed
"""
from __future__ import annotations

import sys
import subprocess
from typing import Optional, TYPE_CHECKING

# Type hints without importing spacy at module level
if TYPE_CHECKING:
    import spacy
    from spacy.language import Language


# =============================================================================
# SPACY AVAILABILITY CHECK
# =============================================================================

_SPACY_AVAILABLE: Optional[bool] = None
_SPACY_NLP: Optional["Language"] = None


def is_spacy_available() -> bool:
    """Check if spaCy is installed."""
    global _SPACY_AVAILABLE
    if _SPACY_AVAILABLE is None:
        try:
            import spacy
            _SPACY_AVAILABLE = True
        except ImportError:
            _SPACY_AVAILABLE = False
    return _SPACY_AVAILABLE


def prompt_install_spacy() -> bool:
    """
    Prompt user to install spaCy if not available.
    
    Returns:
        True if user wants to install, False otherwise
    """
    print("\n" + "=" * 60)
    print("🧠 PRECISION MODE requires spaCy (not installed)")
    print("=" * 60)
    print()
    print("spaCy provides advanced entity recognition for better accuracy.")
    print("This will install:")
    print("  • spacy (~50MB)")
    print("  • en_core_web_sm model (~15MB)")
    print()
    
    try:
        response = input("Install spaCy now? [Y/n]: ").strip().lower()
        return response in ("", "y", "yes")
    except (EOFError, KeyboardInterrupt):
        return False


def install_spacy() -> bool:
    """
    Install spaCy and download the English model.
    
    Returns:
        True if successful, False otherwise
    """
    print("\n📦 Installing spaCy...")
    
    try:
        # Install spacy
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "spacy", "-q"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print("✓ spaCy installed")
        
        # Download model
        print("📦 Downloading en_core_web_sm model...")
        subprocess.check_call(
            [sys.executable, "-m", "spacy", "download", "en_core_web_sm", "-q"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print("✓ Model downloaded")
        
        # Update availability flag
        global _SPACY_AVAILABLE
        _SPACY_AVAILABLE = True
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Installation failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def get_spacy_nlp() -> Optional["Language"]:
    """
    Get or create the spaCy NLP pipeline.
    
    Returns:
        spaCy Language object or None if unavailable
    """
    global _SPACY_NLP
    
    if not is_spacy_available():
        return None
    
    if _SPACY_NLP is None:
        try:
            import spacy
            _SPACY_NLP = spacy.load("en_core_web_sm", disable=["parser"])
        except OSError:
            # Model not installed
            print("⚠️ spaCy model not found. Downloading...")
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "spacy", "download", "en_core_web_sm", "-q"],
                    stdout=subprocess.DEVNULL,
                )
                import spacy
                _SPACY_NLP = spacy.load("en_core_web_sm", disable=["parser"])
            except Exception:
                return None
    
    return _SPACY_NLP


# =============================================================================
# ENTITY EXTRACTION
# =============================================================================

# Known AI/Tech companies for boosting
AI_COMPANIES = {
    "openai", "anthropic", "deepmind", "google", "microsoft", "meta",
    "nvidia", "apple", "amazon", "tesla", "hugging face", "mistral",
    "cohere", "stability ai", "midjourney", "runway", "databricks",
}

FINANCE_ENTITIES = {
    "federal reserve", "fed", "s&p", "nasdaq", "dow jones",
    "wall street", "sec", "treasury", "imf", "world bank",
}

CRYPTO_ENTITIES = {
    "bitcoin", "ethereum", "binance", "coinbase", "ftx", "tether",
    "solana", "cardano", "ripple", "dogecoin",
}


def extract_entities(text: str) -> dict:
    """
    Extract named entities from text using spaCy.
    
    Args:
        text: Input text to analyze
        
    Returns:
        Dict with entity types as keys and lists of entities as values
    """
    nlp = get_spacy_nlp()
    if nlp is None:
        return {}
    
    doc = nlp(text)
    
    entities = {
        "ORG": [],      # Organizations
        "PERSON": [],   # People
        "GPE": [],      # Geopolitical entities (countries, cities)
        "PRODUCT": [],  # Products
        "MONEY": [],    # Monetary values
        "DATE": [],     # Dates
        "EVENT": [],    # Events
    }
    
    for ent in doc.ents:
        if ent.label_ in entities:
            entities[ent.label_].append(ent.text.lower())
    
    return entities


def get_entity_boost(entities: dict) -> dict:
    """
    Calculate category boosts based on extracted entities.
    
    Uses entity_map.json for entity-to-category mappings.
    Falls back to hardcoded sets if JSON not available.
    
    Args:
        entities: Dict from extract_entities()
        
    Returns:
        Dict of category_key -> boost_score
    """
    from config.loader import load_entity_map
    
    entity_map = load_entity_map()
    boosts = {}
    
    # If entity_map loaded successfully, use it
    if entity_map:
        for ent_type, ent_list in entities.items():
            type_map = entity_map.get(ent_type, {})
            
            for entity_text in ent_list:
                entity_lower = entity_text.lower()
                matched = False
                
                # Check each mapping in this entity type
                for name, config in type_map.items():
                    if name.startswith("_"):
                        continue  # Skip meta keys like _default
                    
                    name_lower = name.lower()
                    aliases = [a.lower() for a in config.get("aliases", [])]
                    
                    # Check exact match or alias match
                    if entity_lower == name_lower or entity_lower in aliases:
                        cat = config["category"]
                        boost = config.get("boost", 0.5) * 5.0  # Scale to match existing
                        boosts[cat] = boosts.get(cat, 0) + boost
                        matched = True
                        break
                
                # Check _default for this type if no specific match
                if not matched and "_default" in type_map:
                    cat = type_map["_default"]["category"]
                    boost = type_map["_default"].get("boost", 0.3) * 5.0
                    boosts[cat] = boosts.get(cat, 0) + boost
    else:
        # Fallback to hardcoded sets
        orgs = set(entities.get("ORG", []))
        
        # Check for AI companies
        ai_matches = orgs & AI_COMPANIES
        if ai_matches:
            boosts["ai_headlines"] = len(ai_matches) * 3.0
        
        # Check for finance entities
        finance_matches = orgs & FINANCE_ENTITIES
        if finance_matches:
            boosts["finance_markets"] = len(finance_matches) * 3.0
        
        # Check for crypto entities
        crypto_matches = orgs & CRYPTO_ENTITIES
        if crypto_matches:
            boosts["crypto_blockchain"] = len(crypto_matches) * 3.0
        
        # GPE (countries) boost world_news
        if entities.get("GPE"):
            boosts["world_news"] = len(entities["GPE"]) * 1.5
        
        # MONEY mentions boost finance
        if entities.get("MONEY"):
            boosts["finance_markets"] = boosts.get("finance_markets", 0) + len(entities["MONEY"]) * 2.0
    
    return boosts


# =============================================================================
# PRECISION CLASSIFIER
# =============================================================================

class PrecisionClassifier:
    """
    Enhanced classifier that uses spaCy NER for better accuracy.
    
    This extends SemanticClassifier by:
    1. Extracting named entities with spaCy
    2. Applying entity-based boosts to category scores
    3. Providing higher confidence for entity-rich articles
    
    Example:
        >>> classifier = PrecisionClassifier()
        >>> if classifier.is_available():
        ...     result = classifier.classify("OpenAI CEO Sam Altman announces...")
        ...     print(result.entities)
        {'ORG': ['openai'], 'PERSON': ['sam altman']}
    """
    
    def __init__(self):
        self._nlp = None
    
    def is_available(self) -> bool:
        """Check if precision mode is available (spaCy installed)."""
        return is_spacy_available()
    
    def ensure_available(self) -> bool:
        """
        Ensure spaCy is available, prompting for install if needed.
        
        Returns:
            True if available, False if user declined or install failed
        """
        if is_spacy_available():
            return True
        
        if prompt_install_spacy():
            return install_spacy()
        
        return False
    
    def classify(self, title: str, summary: str) -> dict:
        """
        Classify article with entity extraction.
        
        Args:
            title: Article headline
            summary: Article description
            
        Returns:
            Dict with 'category', 'confidence', 'entities', 'entity_boosts'
        """
        # Import here to avoid circular dependency
        from curation.classifier import SemanticClassifier
        
        # Get base classification
        base_classifier = SemanticClassifier()
        base_result = base_classifier.classify(title, summary)
        
        # Extract entities
        text = f"{title} {summary}"
        entities = extract_entities(text)
        entity_boosts = get_entity_boost(entities)
        
        # Apply entity boosts to scores
        enhanced_scores = dict(base_result.scores)
        for cat, boost in entity_boosts.items():
            enhanced_scores[cat] = enhanced_scores.get(cat, 0) + boost
        
        # Find new best category
        sorted_cats = sorted(enhanced_scores.items(), key=lambda x: x[1], reverse=True)
        best_cat, best_score = sorted_cats[0]
        
        # Calculate enhanced confidence
        max_possible = 40.0  # Higher due to entity boosts
        confidence = min(1.0, max(0.0, best_score / max_possible))
        
        if best_score <= 0:
            best_cat = "ai_headlines"
            confidence = 0.3
        
        return {
            "category": best_cat,
            "confidence": confidence,
            "entities": entities,
            "entity_boosts": entity_boosts,
            "base_category": base_result.category,
            "scores": enhanced_scores,
        }


def classify_with_precision(title: str, summary: str) -> str:
    """
    Classify article using precision mode if available, fallback otherwise.
    
    Args:
        title: Article headline
        summary: Article description
        
    Returns:
        Category key string
    """
    if is_spacy_available():
        classifier = PrecisionClassifier()
        result = classifier.classify(title, summary)
        return result["category"]
    else:
        # Fallback to standard classifier
        from curation.classifier import classify_article_enhanced
        return classify_article_enhanced(title, summary)
