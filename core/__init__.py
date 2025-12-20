# core/__init__.py
"""
Core module - Contains fundamental data structures, configuration, and fetching logic.
"""

from core.article import Article
from core.config import (
    VERSION,
    UA,
    PRESETS_FILE,
    HEADERS,
    SOURCE_TIERS,
    CATEGORIES,
    IMPORTANCE_KEYWORDS,
    KNOWN_FEEDS_BY_DOMAIN,
)
from core.fetcher import (
    now_utc,
    parse_dt,
    strip_html,
    normalize_url,
    domain_key,
    sha1,
    normalize_title,
    is_duplicate_story,
    get_session,
    safe_get,
    calculate_recency_score,
    calculate_importance_score,
    get_source_reputation,
    calculate_final_score,
    determine_priority,
    classify_article,
    generate_why_matters,
    discover_feeds,
    google_news_rss_url,
    load_sources,
    build_feed_list,
    collect_articles,
    process_feed,
    extract_og_image,
    enrich_image,
)

__all__ = [
    # Article
    "Article",
    # Config
    "VERSION",
    "UA",
    "PRESETS_FILE",
    "HEADERS",
    "SOURCE_TIERS",
    "CATEGORIES",
    "IMPORTANCE_KEYWORDS",
    "KNOWN_FEEDS_BY_DOMAIN",
    # Fetcher utilities
    "now_utc",
    "parse_dt",
    "strip_html",
    "normalize_url",
    "domain_key",
    "sha1",
    "normalize_title",
    "is_duplicate_story",
    "get_session",
    "safe_get",
    "calculate_recency_score",
    "calculate_importance_score",
    "get_source_reputation",
    "calculate_final_score",
    "determine_priority",
    "classify_article",
    "generate_why_matters",
    "discover_feeds",
    "google_news_rss_url",
    "load_sources",
    "build_feed_list",
    "collect_articles",
    "process_feed",
    "extract_og_image",
    "enrich_image",
]

