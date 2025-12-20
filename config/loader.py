"""
config/loader.py - Load JSON config files with caching.

Provides centralized loading of:
- entity_map.json (for precision mode entity boosts)
- exclusions.json (for classifier exclusion patterns)
- category_weights.json (for preset-based category weighting)

All loaders use LRU cache to avoid repeated file reads.
"""
import json
from pathlib import Path
from functools import lru_cache
from typing import Dict, Any, List

CONFIG_DIR = Path(__file__).parent


@lru_cache(maxsize=1)
def load_entity_map() -> Dict[str, Any]:
    """
    Load entity_map.json for precision mode.
    
    Returns:
        Dict with entity types (ORG, PRODUCT, GPE, MONEY) as keys,
        each containing entity names mapped to {category, boost, aliases}.
    """
    path = CONFIG_DIR / "entity_map.json"
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Remove comment keys (starting with _)
            return {k: v for k, v in data.items() if not k.startswith("_")}
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️ Could not load entity_map.json: {e}")
    return {}


@lru_cache(maxsize=1)
def load_exclusions() -> Dict[str, List[str]]:
    """
    Load exclusions.json for classifier.
    
    Returns:
        Dict with category keys mapped to lists of exclusion patterns.
        Includes "global" key for patterns that apply to all categories.
    """
    path = CONFIG_DIR / "exclusions.json"
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Remove comment keys (starting with _)
            return {k: v for k, v in data.items() if not k.startswith("_")}
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️ Could not load exclusions.json: {e}")
    return {}


@lru_cache(maxsize=8)
def load_category_weights(preset: str = "default") -> Dict[str, float]:
    """
    Load category_weights.json for scorer.
    
    Args:
        preset: Preset name (default, ai_focus, finance, etc.)
        
    Returns:
        Dict mapping category keys to weight multipliers (1.0 = default).
    """
    path = CONFIG_DIR / "category_weights.json"
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Remove comment keys
            data = {k: v for k, v in data.items() if not k.startswith("_")}
            # Return preset weights, fallback to default
            return data.get(preset, data.get("default", {}))
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️ Could not load category_weights.json: {e}")
    return {}


def clear_config_cache():
    """Clear all cached configs (useful for testing or hot-reload)."""
    load_entity_map.cache_clear()
    load_exclusions.cache_clear()
    load_category_weights.cache_clear()


# Convenience exports
__all__ = [
    "load_entity_map",
    "load_exclusions", 
    "load_category_weights",
    "clear_config_cache",
]
