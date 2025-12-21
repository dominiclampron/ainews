"""
core/fetcher.py - Feed fetching, article collection, parsing, and scoring logic.

This module contains all HTTP/network operations and feed processing:
- HTTP session management with connection pooling
- RSS/Atom feed discovery and parsing
- Article collection from feeds
- Image enrichment from OpenGraph
- Scoring calculations
- Classification
"""
from __future__ import annotations

import datetime as dt
import hashlib
import re
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from difflib import SequenceMatcher
from threading import Lock
from typing import Optional
from urllib.parse import urlparse, urljoin, urlunparse, parse_qsl, urlencode

import feedparser
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from dateutil import parser as dateparser, tz

from core.article import Article
from core.config import (
    HEADERS,
    SOURCE_TIERS,
    CATEGORIES,
    IMPORTANCE_KEYWORDS,
    KNOWN_FEEDS_BY_DOMAIN,
)

# Timezone mappings for EDT/EST parsing (fixes UnknownTimezoneWarning)
TZINFOS = {
    "EST": tz.tzoffset("EST", -5 * 3600),
    "EDT": tz.tzoffset("EDT", -4 * 3600),
    "UTC": tz.UTC,
    "GMT": tz.UTC,
    "PST": tz.tzoffset("PST", -8 * 3600),
    "PDT": tz.tzoffset("PDT", -7 * 3600),
    "CST": tz.tzoffset("CST", -6 * 3600),
    "CDT": tz.tzoffset("CDT", -5 * 3600),
}

# Thread-safe locks for caching
resolve_lock = Lock()
og_lock = Lock()

# Global session (created on first import)
_SESSION: Optional[requests.Session] = None


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def now_utc() -> dt.datetime:
    """Get current UTC datetime."""
    return dt.datetime.now(dt.timezone.utc)


def parse_dt(value) -> Optional[dt.datetime]:
    """Parse datetime from various formats."""
    if not value:
        return None
    try:
        d = dateparser.parse(str(value), tzinfos=TZINFOS)
        if d and d.tzinfo is None:
            d = d.replace(tzinfo=dt.timezone.utc)
        return d
    except Exception:
        return None


def strip_html(s: str) -> str:
    """Remove HTML tags from string."""
    if not s:
        return ""
    soup = BeautifulSoup(s, "html.parser")
    txt = soup.get_text(" ", strip=True)
    return re.sub(r"\s+", " ", txt).strip()


def normalize_url(url: str) -> str:
    """Normalize URL by removing tracking parameters."""
    try:
        u = urlparse(url)
        q = [(k, v) for k, v in parse_qsl(u.query, keep_blank_values=True)
             if not re.match(r"^(utm_|fbclid|gclid|mc_cid|mc_eid|ref|src)$", k, re.I)]
        u2 = u._replace(query=urlencode(q), fragment="")
        return urlunparse(u2)
    except Exception:
        return url


def domain_key(url: str) -> str:
    """Extract domain key from URL."""
    try:
        host = urlparse(url).netloc.lower()
        host = host[4:] if host.startswith("www.") else host
        return host
    except Exception:
        return url


def sha1(s: str) -> str:
    """Calculate SHA1 hash of string."""
    return hashlib.sha1(s.encode("utf-8", errors="ignore")).hexdigest()


def normalize_title(title: str) -> str:
    """Normalize title for comparison."""
    t = title.lower()
    t = re.sub(r"[^\w\s]", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    # Remove common suffixes
    for suffix in [" reuters", " bloomberg", " ap", " wsj", " ft"]:
        if t.endswith(suffix):
            t = t[:-len(suffix)]
    return t


def is_duplicate_story(title1: str, title2: str, threshold: float = 0.70) -> bool:
    """Check if two titles represent the same story."""
    t1 = normalize_title(title1)
    t2 = normalize_title(title2)
    return SequenceMatcher(None, t1, t2).ratio() > threshold


# =============================================================================
# HTTP SESSION
# =============================================================================

def create_session() -> requests.Session:
    """Create HTTP session with connection pooling and retries."""
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=0.3, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(pool_connections=50, pool_maxsize=50, max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update(HEADERS)
    return session


def get_session() -> requests.Session:
    """Get or create the global HTTP session."""
    global _SESSION
    if _SESSION is None:
        _SESSION = create_session()
    return _SESSION


def safe_get(url: str, timeout=12, referer: Optional[str] = None) -> Optional[requests.Response]:
    """Make a safe HTTP GET request."""
    try:
        headers = dict(HEADERS)
        if referer:
            headers["Referer"] = referer
        r = get_session().get(url, headers=headers, timeout=timeout, allow_redirects=True)
        if r.status_code >= 400:
            return None
        return r
    except Exception:
        return None


# =============================================================================
# SCORING ENGINE
# =============================================================================

def calculate_recency_score(published: Optional[dt.datetime]) -> float:
    """
    Calculate recency score with exponential decay.
    - 0-6 hours: ~1.0
    - 6-12 hours: ~0.85
    - 12-24 hours: ~0.65
    - 24-48 hours: ~0.40
    """
    if not published:
        return 0.3  # Unknown date gets low score
    
    now = now_utc()
    age_hours = max(0.1, (now - published).total_seconds() / 3600)
    return max(0.1, 1.0 / (1 + (age_hours / 8) ** 1.2))


def calculate_importance_score(title: str, summary: str) -> float:
    """Calculate importance based on keywords."""
    text = (title + " " + summary).lower()
    score = 0.0
    
    for keyword, weight in IMPORTANCE_KEYWORDS.items():
        if keyword in text:
            score += weight
    
    return min(1.0, score)


def get_source_reputation(domain: str) -> float:
    """Get source reputation score from tiers."""
    domain = domain.lower()
    
    for tier_name, sources in SOURCE_TIERS.items():
        if domain in sources:
            return sources[domain]
        # Check partial match
        for src, score in sources.items():
            if src in domain or domain in src:
                return score
    
    return 0.45  # Default for unknown sources


def calculate_final_score(article: Article, category: str = None, preset: str = "default") -> float:
    """
    Calculate composite final score.
    
    Args:
        article: Article with recency, importance, source scores
        category: Optional category for weight adjustment
        preset: Preset name for category weights (default, ai_focus, etc.)
        
    Returns:
        Final composite score (0.0 - 1.0+)
    """
    base_score = (
        article.recency_score * 0.25 +
        article.importance_score * 0.35 +
        article.source_score * 0.25 +
        0.15  # Base score
    )
    
    # Apply category weight if category provided
    if category:
        from config.loader import load_category_weights
        weights = load_category_weights(preset)
        cat_weight = weights.get(category, 1.0)
        base_score *= cat_weight
    
    return base_score


def determine_priority(importance_score: float, recency_score: float) -> str:
    """Determine article priority badge."""
    if importance_score > 0.5 and recency_score > 0.8:
        return "breaking"
    elif importance_score > 0.3 or recency_score > 0.7:
        return "important"
    return "normal"


# =============================================================================
# CATEGORY CLASSIFICATION
# =============================================================================

def classify_article(title: str, summary: str) -> str:
    """
    Classify article into one of the 12 categories.
    
    Uses the enhanced SemanticClassifier with:
    - Weighted keyword matching (high/medium/low tiers)
    - Exclusion rules to prevent false positives
    - Boost patterns for high-confidence signals
    - Category weights for prioritization
    
    This is a wrapper around curation.classifier.classify_article_enhanced()
    for backwards compatibility.
    """
    # Import here to avoid circular import
    from curation.classifier import classify_article_enhanced
    return classify_article_enhanced(title, summary)


def generate_why_matters(category: str, title: str) -> str:
    """Generate contextual 'why it matters' text."""
    reasons = {
        "ai_headlines": "Signals shifts in AI capabilities, competitive landscape, or adoption patterns.",
        "tools_platforms": "New tools can reduce cost, raise capability, or unlock new product patterns.",
        "governance_safety": "Policy changes can alter what models/hardware can be built, shipped, or deployed.",
        "finance_markets": "Market movements affect investment, funding, and tech valuations.",
        "crypto_blockchain": "Crypto trends impact fintech, regulation, and decentralized technology adoption.",
        "cybersecurity": "Security incidents affect trust, compliance posture, and vendor choices.",
        "tech_industry": "Market signals affect funding, compute availability, and deployment timelines.",
        "politics_policy": "Political decisions shape regulatory environment and innovation landscape.",
        "world_news": "Global events create new constraints or opportunities for tech deployment.",
        "viral_trending": "Viral stories indicate shifting public sentiment and adoption trends.",
        "science_research": "New research findings can unlock breakthrough capabilities and applications.",
        "health_biotech": "Medical advances impact healthcare, regulation, and life sciences innovation.",
    }
    return reasons.get(category, "High-signal development with downstream impact.")


# =============================================================================
# FEED DISCOVERY & FETCHING
# =============================================================================

def discover_feeds(home_url: str, max_found: int = 3) -> list[str]:
    """Discover RSS/Atom feeds from a URL."""
    if re.search(r"\.(xml|rss|atom)$", home_url, re.I) or "/feed" in home_url:
        return [home_url]
    
    feeds = []
    r = safe_get(home_url, timeout=10)
    if r and r.text:
        soup = BeautifulSoup(r.text, "html.parser")
        for link in soup.find_all("link"):
            rel = " ".join(link.get("rel", [])).lower()
            typ = (link.get("type") or "").lower()
            href = link.get("href")
            if href and "alternate" in rel and ("rss" in typ or "atom" in typ):
                feeds.append(urljoin(home_url, href))
    
    # Try common suffixes
    base = home_url.rstrip("/")
    for suf in ["/feed", "/rss", "/feed.xml", "/rss.xml"]:
        feeds.append(base + suf)
    
    return list(set(feeds))[:max_found]


def google_news_rss_url(query: str, lang="en-US", region="US") -> str:
    """Build Google News RSS URL for a query."""
    ceid = f"{region}:{lang.split('-')[-1].lower()}"
    q = requests.utils.quote(query)
    return f"https://news.google.com/rss/search?q={q}&hl={lang}&gl={region}&ceid={ceid}"


def load_sources(path: str) -> list[str]:
    """Load source URLs from file."""
    urls = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            urls.append(s)
    return list(dict.fromkeys(urls))  # Dedupe preserving order


def build_feed_list(source_urls: list[str], days: int) -> list[tuple[str, str]]:
    """Build list of (feed_url, domain) tuples."""
    by_dom = defaultdict(list)
    for u in source_urls:
        by_dom[domain_key(u)].append(u)
    
    feeds = []
    for dom, urls in by_dom.items():
        # Reddit special handling
        for u in urls:
            m = re.search(r"reddit\.com/r/([A-Za-z0-9_]+)/?", u)
            if m:
                feeds.append((f"https://www.reddit.com/r/{m.group(1)}/.rss", dom))
        
        # Known feeds
        if dom in KNOWN_FEEDS_BY_DOMAIN:
            for f in KNOWN_FEEDS_BY_DOMAIN[dom][:2]:
                feeds.append((f, dom))
        
        # Discover feeds
        discovered = discover_feeds(urls[0], max_found=2)
        for f in discovered:
            feeds.append((f, dom))
        
        # Google News fallback
        q = f'site:{dom} (AI OR "artificial intelligence" OR cybersecurity OR tech) when:{days}d'
        feeds.append((google_news_rss_url(q), dom))
    
    # Dedupe
    seen = set()
    uniq = []
    for f, dom in feeds:
        f = normalize_url(f)
        if f not in seen:
            seen.add(f)
            uniq.append((f, dom))
    
    return uniq


# =============================================================================
# ARTICLE COLLECTION
# =============================================================================

def extract_outlet_from_entry(entry) -> str:
    """Extract outlet name from feed entry."""
    try:
        src = entry.get("source")
        if src and isinstance(src, dict) and src.get("title"):
            return str(src["title"])
    except Exception:
        pass
    return ""


def resolve_google_url(url: str, cache: dict) -> str:
    """Resolve Google News redirect URLs."""
    if "news.google.com" not in url:
        return url
    
    with resolve_lock:
        if url in cache:
            return cache[url]
    
    try:
        r = get_session().get(url, timeout=10, allow_redirects=True)
        final = normalize_url(r.url) if r.status_code < 400 else url
    except Exception:
        final = url
    
    with resolve_lock:
        cache[url] = final
    
    return final


def collect_articles(feed_url: str, seed_dom: str, start: dt.datetime, 
                     end: dt.datetime, resolve_cache: dict) -> list[Article]:
    """Collect articles from a single feed."""
    try:
        fp = feedparser.parse(feed_url)
    except Exception:
        return []
    
    feed_title = fp.feed.get("title", "") if hasattr(fp, "feed") else ""
    articles = []
    
    for e in getattr(fp, "entries", [])[:50]:
        raw_link = normalize_url(getattr(e, "link", "") or "")
        if not raw_link:
            continue
        
        # Resolve Google News URLs
        if "news.google.com" in raw_link:
            final_link = resolve_google_url(raw_link, resolve_cache)
            if "news.google.com" in final_link:
                continue  # Skip if couldn't resolve
        else:
            final_link = raw_link
        
        # Parse date
        published = parse_dt(getattr(e, "published", None) or getattr(e, "updated", None))
        if published and not (start <= published <= end):
            continue
        
        # Extract metadata
        outlet = extract_outlet_from_entry(e) or feed_title or seed_dom
        outlet_key = domain_key(final_link) or seed_dom
        
        title = (getattr(e, "title", "") or "Untitled").strip()
        # Clean title
        if " - " in title:
            parts = title.rsplit(" - ", 1)
            if len(parts) == 2 and len(parts[1]) < 50:
                title = parts[0].strip()
        
        summary = strip_html(getattr(e, "summary", "") or "")
        if len(summary) > 500:
            summary = summary[:500] + "…"
        if not summary:
            summary = "Summary unavailable."
        
        # Extract image
        image_url = None
        try:
            media = getattr(e, "media_content", None)
            if media and isinstance(media, list) and media[0].get("url"):
                image_url = media[0]["url"]
        except Exception:
            pass
        
        if not image_url:
            try:
                thumbs = getattr(e, "media_thumbnail", None)
                if thumbs and isinstance(thumbs, list) and thumbs[0].get("url"):
                    image_url = thumbs[0]["url"]
            except Exception:
                pass
        
        # Skip google news images
        if image_url and "news.google.com" in image_url:
            image_url = None
        
        # Create article
        article = Article(
            title=title,
            url=final_link,
            outlet=outlet.strip() or seed_dom,
            outlet_key=outlet_key,
            published=published,
            summary=summary,
            image_url=image_url,
        )
        
        # Calculate initial scores
        article.recency_score = calculate_recency_score(published)
        article.importance_score = calculate_importance_score(title, summary)
        article.source_score = get_source_reputation(outlet_key)
        
        # Classify first (needed for category weight)
        article.category = classify_article(title, summary)
        
        # Calculate final score WITH category weight
        article.final_score = calculate_final_score(article, category=article.category)
        
        article.priority = determine_priority(article.importance_score, article.recency_score)
        article.why_matters = generate_why_matters(article.category, title)
        
        articles.append(article)
    
    return articles


def process_feed(args: tuple) -> list[Article]:
    """Wrapper for parallel feed processing."""
    feed_url, seed_dom, start, end, resolve_cache = args
    try:
        return collect_articles(feed_url, seed_dom, start, end, resolve_cache)
    except Exception:
        return []


# =============================================================================
# IMAGE ENRICHMENT
# =============================================================================

def extract_og_image(url: str) -> Optional[str]:
    """Extract OpenGraph image from URL."""
    try:
        r = safe_get(url, timeout=10)
        if not r or not r.text:
            return None
        
        soup = BeautifulSoup(r.text, "html.parser")
        
        for prop in ["og:image", "twitter:image"]:
            meta = soup.find("meta", attrs={"property": prop}) or soup.find("meta", attrs={"name": prop})
            if meta and meta.get("content"):
                img = meta["content"]
                if img.startswith("http") and "logo" not in img.lower():
                    return img
        
        return None
    except Exception:
        return None


def enrich_image(article: Article, og_cache: dict) -> Article:
    """Enrich article with OG image if missing."""
    if article.image_url:
        return article
    
    with og_lock:
        if article.url in og_cache:
            article.image_url = og_cache[article.url]
            return article
    
    img = extract_og_image(article.url)
    
    with og_lock:
        og_cache[article.url] = img
    
    article.image_url = img
    return article
