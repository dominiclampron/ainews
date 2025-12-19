#!/usr/bin/env python3
"""
News Aggregator v0.2 - Intelligent News Curation
Features:
- 10-category classification system (AI, Finance, Crypto, etc.)
- Preset-based configuration system
- Multi-factor intelligent scoring
- Source diversity enforcement
- Top 30 + 10-20 "Other Interesting" articles
- Dark mode UI
- Auto-opens in browser (WSL/Mac/Windows)
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import warnings
from collections import defaultdict
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
from typing import Optional, Any
from urllib.parse import urlparse, urljoin, urlunparse, parse_qsl, urlencode
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

import feedparser
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from dateutil import parser as dateparser
from jinja2 import Template
from tqdm import tqdm

# Suppress XML parsing warning
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# =============================================================================
# CONFIGURATION & CONSTANTS
# =============================================================================

VERSION = "0.2"
UA = "Mozilla/5.0 (X11; Linux x86_64) NewsAggregator/0.2"
PRESETS_FILE = "presets.json"
HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Source Reputation Tiers (score multiplier)
SOURCE_TIERS = {
    # Tier 1: Highest credibility (1.0)
    "tier_1": {
        "reuters.com": 1.0, "apnews.com": 1.0, "bloomberg.com": 0.98,
        "ft.com": 0.98, "wsj.com": 0.97, "nytimes.com": 0.96,
        "nature.com": 0.99, "arxiv.org": 0.95, "sciencedaily.com": 0.92,
    },
    # Tier 2: Major tech news (0.80-0.94)
    "tier_2": {
        "techcrunch.com": 0.90, "theverge.com": 0.88, "arstechnica.com": 0.89,
        "wired.com": 0.87, "technologyreview.com": 0.91, "spectrum.ieee.org": 0.90,
        "venturebeat.com": 0.85, "zdnet.com": 0.82, "engadget.com": 0.80,
    },
    # Tier 3: Specialized/Quality (0.65-0.79)
    "tier_3": {
        "huggingface.co": 0.78, "openai.com": 0.79, "deepmind.google": 0.79,
        "nvidia.com": 0.77, "marktechpost.com": 0.72, "infoq.com": 0.75,
        "hackernoon.com": 0.68, "analyticsindiamag.com": 0.70,
        "krebsonsecurity.com": 0.85, "bleepingcomputer.com": 0.78,
        "thehackernews.com": 0.75, "schneier.com": 0.82,
        # Finance sources
        "cnbc.com": 0.88, "marketwatch.com": 0.85, "seekingalpha.com": 0.75,
        # Crypto sources
        "coindesk.com": 0.80, "cointelegraph.com": 0.78, "decrypt.co": 0.75,
    },
    # Tier 4: Community/Aggregators (0.50-0.64)
    "tier_4": {
        "reddit.com": 0.55, "dev.to": 0.58, "medium.com": 0.52,
        "substack.com": 0.56, "news.ycombinator.com": 0.62,
    },
}

# 10 Category System with Keywords (v0.2: added Finance & Crypto)
CATEGORIES = {
    "ai_headlines": {
        "icon": "📰",
        "title": "AI/ML Headlines",
        "keywords_high": ["openai", "anthropic", "deepmind", "gemini", "gpt-5", "claude", "mistral", "llama", "agi", "chatgpt"],
        "keywords_medium": ["artificial intelligence", "machine learning", "llm", "large language model", "neural network", "transformer", "foundation model"],
        "keywords_low": ["ai", "ml", "model", "training", "inference", "benchmark", "reasoning"],
    },
    "tools_platforms": {
        "icon": "🛠️",
        "title": "Tools, Models & Platforms",
        "keywords_high": ["api release", "open source", "github release", "framework launch", "sdk release", "new model"],
        "keywords_medium": ["developer tool", "library", "platform", "hugging face", "pytorch", "tensorflow", "langchain"],
        "keywords_low": ["tool", "code", "programming", "release", "launch", "checkpoint"],
    },
    "governance_safety": {
        "icon": "⚖️",
        "title": "Governance, Safety & Ethics",
        "keywords_high": ["ai act", "regulation", "alignment", "safety research", "ai policy", "ethics board"],
        "keywords_medium": ["ethical ai", "responsible ai", "bias", "fairness", "transparency", "audit", "compliance"],
        "keywords_low": ["policy", "governance", "safety", "ethics", "nist", "oecd", "watermark"],
    },
    "finance_markets": {
        "icon": "💹",
        "title": "Finance & Markets",
        "keywords_high": ["stock market", "wall street", "fed rate", "interest rate", "earnings report", "market crash", "bull market", "bear market"],
        "keywords_medium": ["nasdaq", "s&p 500", "dow jones", "stock price", "trading", "investors", "hedge fund", "etf"],
        "keywords_low": ["market", "stocks", "shares", "portfolio", "dividend", "bonds", "yield"],
    },
    "crypto_blockchain": {
        "icon": "₿",
        "title": "Crypto & Blockchain",
        "keywords_high": ["bitcoin", "ethereum", "crypto crash", "btc", "eth", "sec crypto", "defi", "nft"],
        "keywords_medium": ["blockchain", "cryptocurrency", "altcoin", "binance", "coinbase", "stablecoin", "web3"],
        "keywords_low": ["crypto", "token", "wallet", "mining", "halving", "memecoin"],
    },
    "cybersecurity": {
        "icon": "🔐",
        "title": "Cybersecurity",
        "keywords_high": ["data breach", "ransomware", "zero-day", "cve-", "critical vulnerability", "nation-state"],
        "keywords_medium": ["hacker", "exploit", "malware", "phishing", "ddos", "cyber attack", "security flaw"],
        "keywords_low": ["security", "vulnerability", "patch", "encryption", "authentication", "firewall"],
    },
    "tech_industry": {
        "icon": "💻",
        "title": "Tech Industry",
        "keywords_high": ["ipo", "acquisition", "billion dollar", "major funding", "layoffs", "ceo"],
        "keywords_medium": ["startup", "funding round", "series a", "series b", "valuation", "merger"],
        "keywords_low": ["tech company", "earnings", "revenue", "hiring", "expansion", "partnership"],
    },
    "politics_policy": {
        "icon": "🏛️",
        "title": "Politics & Policy",
        "keywords_high": ["executive order", "legislation", "congress", "senate", "biden", "trump", "eu commission"],
        "keywords_medium": ["government", "administration", "federal", "regulatory", "antitrust", "investigation"],
        "keywords_low": ["policy", "political", "law", "legal", "court", "ruling", "ban"],
    },
    "world_news": {
        "icon": "🌍",
        "title": "World News",
        "keywords_high": ["china", "russia", "ukraine", "europe", "asia", "middle east", "global"],
        "keywords_medium": ["international", "country", "nation", "foreign", "trade war", "sanctions"],
        "keywords_low": ["world", "global", "abroad", "overseas", "export", "import"],
    },
    "viral_trending": {
        "icon": "🔥",
        "title": "Viral & Trending",
        "keywords_high": ["viral", "breaking", "trending", "just announced", "exclusive", "leaked"],
        "keywords_medium": ["meme", "social media", "twitter", "x.com", "went viral", "internet"],
        "keywords_low": ["popular", "buzz", "hype", "everyone", "massive"],
    },
}

# Importance Keywords for Scoring
IMPORTANCE_KEYWORDS = {
    "breaking": 0.25, "exclusive": 0.22, "just announced": 0.20, "major": 0.15,
    "billion": 0.18, "million": 0.12, "unprecedented": 0.15, "groundbreaking": 0.14,
    "first ever": 0.16, "world first": 0.18, "breakthrough": 0.17,
    "openai": 0.12, "google": 0.10, "microsoft": 0.10, "meta": 0.09, "nvidia": 0.11,
    "anthropic": 0.11, "deepmind": 0.10, "apple": 0.09, "amazon": 0.08,
    "breach": 0.14, "hack": 0.13, "vulnerability": 0.12, "ransomware": 0.15,
    "lawsuit": 0.13, "acquisition": 0.14, "ipo": 0.15, "layoffs": 0.12,
    # Finance & Crypto keywords
    "bitcoin": 0.12, "ethereum": 0.11, "crypto crash": 0.16, "fed rate": 0.14,
    "market crash": 0.18, "all-time high": 0.15, "record high": 0.14,
}

# Thread-safe locks
resolve_lock = Lock()
og_lock = Lock()

# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class Article:
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

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def now_utc() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)

def parse_dt(value) -> Optional[dt.datetime]:
    if not value:
        return None
    try:
        d = dateparser.parse(str(value))
        if d and d.tzinfo is None:
            d = d.replace(tzinfo=dt.timezone.utc)
        return d
    except Exception:
        return None

def strip_html(s: str) -> str:
    if not s:
        return ""
    soup = BeautifulSoup(s, "html.parser")
    txt = soup.get_text(" ", strip=True)
    return re.sub(r"\s+", " ", txt).strip()

def normalize_url(url: str) -> str:
    try:
        u = urlparse(url)
        q = [(k, v) for k, v in parse_qsl(u.query, keep_blank_values=True)
             if not re.match(r"^(utm_|fbclid|gclid|mc_cid|mc_eid|ref|src)$", k, re.I)]
        u2 = u._replace(query=urlencode(q), fragment="")
        return urlunparse(u2)
    except Exception:
        return url

def domain_key(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower()
        host = host[4:] if host.startswith("www.") else host
        return host
    except Exception:
        return url

def sha1(s: str) -> str:
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
# HTTP SESSION WITH CONNECTION POOLING
# =============================================================================

def create_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=0.3, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(pool_connections=50, pool_maxsize=50, max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update(HEADERS)
    return session

SESSION = create_session()

def safe_get(url: str, timeout=12, referer: Optional[str] = None) -> Optional[requests.Response]:
    try:
        headers = dict(HEADERS)
        if referer:
            headers["Referer"] = referer
        r = SESSION.get(url, headers=headers, timeout=timeout, allow_redirects=True)
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

def calculate_final_score(article: Article) -> float:
    """Calculate composite final score."""
    return (
        article.recency_score * 0.25 +
        article.importance_score * 0.35 +
        article.source_score * 0.25 +
        0.15  # Base score
    )

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
    """Classify article into one of 8 categories."""
    text = (title + " " + summary).lower()
    scores = {}
    
    for cat_key, cat_data in CATEGORIES.items():
        score = 0.0
        
        for kw in cat_data["keywords_high"]:
            if kw in text:
                score += 3.0
        
        for kw in cat_data["keywords_medium"]:
            if kw in text:
                score += 1.5
        
        for kw in cat_data["keywords_low"]:
            if kw in text:
                score += 0.5
        
        scores[cat_key] = score
    
    # Return category with highest score, default to ai_headlines
    if max(scores.values()) == 0:
        return "ai_headlines"
    
    return max(scores, key=scores.get)

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
    }
    return reasons.get(category, "High-signal development with downstream impact.")

# =============================================================================
# FEED DISCOVERY & FETCHING (Reused from ainews4 with enhancements)
# =============================================================================

KNOWN_FEEDS_BY_DOMAIN = {
    "techcrunch.com": ["https://techcrunch.com/category/artificial-intelligence/feed/"],
    "theverge.com": ["https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"],
    "arstechnica.com": ["https://arstechnica.com/feed/"],
    "venturebeat.com": ["https://venturebeat.com/category/ai/feed/"],
    "huggingface.co": ["https://huggingface.co/blog/feed.xml"],
    "marktechpost.com": ["https://www.marktechpost.com/feed/"],
}

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
        r = SESSION.get(url, timeout=10, allow_redirects=True)
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
        
        # Calculate scores
        article.recency_score = calculate_recency_score(published)
        article.importance_score = calculate_importance_score(title, summary)
        article.source_score = get_source_reputation(outlet_key)
        article.final_score = calculate_final_score(article)
        
        # Classify
        article.category = classify_article(title, summary)
        article.priority = determine_priority(article.importance_score, article.recency_score)
        article.why_matters = generate_why_matters(article.category, title)
        
        articles.append(article)
    
    return articles

def process_feed(args: tuple) -> list[Article]:
    """Wrapper for parallel processing."""
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

# =============================================================================
# DIVERSITY SELECTION
# =============================================================================

def deduplicate_articles(articles: list[Article]) -> list[Article]:
    """Remove duplicate articles by URL and similar titles."""
    seen_urls = set()
    seen_titles = []
    unique = []
    
    for article in sorted(articles, key=lambda x: x.final_score, reverse=True):
        url_key = normalize_url(article.url)
        if url_key in seen_urls:
            continue
        
        # Check title similarity
        is_dup = False
        for seen_title in seen_titles:
            if is_duplicate_story(article.title, seen_title):
                is_dup = True
                break
        
        if not is_dup:
            seen_urls.add(url_key)
            seen_titles.append(article.title)
            unique.append(article)
    
    return unique

def select_top_articles(articles: list[Article], top_n: int = 30, 
                        max_per_source: int = 3, min_categories: int = 5) -> list[Article]:
    """Select top N diverse articles."""
    selected = []
    source_counts = defaultdict(int)
    category_counts = defaultdict(int)
    
    # Sort by score
    ranked = sorted(articles, key=lambda x: x.final_score, reverse=True)
    
    # Pass 1: Ensure category diversity (1 per category first)
    for cat in CATEGORIES.keys():
        for article in ranked:
            if article.category == cat and article not in selected:
                if source_counts[article.outlet_key] < max_per_source:
                    selected.append(article)
                    source_counts[article.outlet_key] += 1
                    category_counts[cat] += 1
                    break
    
    # Pass 2: Fill remaining by score
    for article in ranked:
        if len(selected) >= top_n:
            break
        if article in selected:
            continue
        if source_counts[article.outlet_key] >= max_per_source:
            continue
        
        selected.append(article)
        source_counts[article.outlet_key] += 1
        category_counts[article.category] += 1
    
    return selected

def select_other_interesting(articles: list[Article], top_articles: list[Article],
                             min_count: int = 10, max_count: int = 20) -> list[Article]:
    """Select 'Other Interesting' articles not in top selection."""
    top_urls = {a.url for a in top_articles}
    candidates = [a for a in articles if a.url not in top_urls]
    
    # Sort by score
    ranked = sorted(candidates, key=lambda x: x.final_score, reverse=True)
    
    # Select diverse
    selected = []
    source_counts = defaultdict(int)
    
    for article in ranked:
        if len(selected) >= max_count:
            break
        if source_counts[article.outlet_key] >= 2:  # Max 2 per source
            continue
        
        selected.append(article)
        source_counts[article.outlet_key] += 1
    
    return selected[:max(min_count, len(selected))]

# =============================================================================
# HTML TEMPLATE
# =============================================================================

HTML_TEMPLATE = Template('''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>News Aggregator — {{ today }}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #0a0a0f;
      --bg-elevated: #12121a;
      --bg-card: #1a1a24;
      --bg-card-hover: #22222e;
      --border: #2a2a3a;
      --text: #f0f0f5;
      --text-secondary: #a0a0b0;
      --text-muted: #707080;
      --accent: #6366f1;
      --accent-light: #818cf8;
      --accent-glow: rgba(99, 102, 241, 0.3);
      --breaking: #ef4444;
      --important: #f59e0b;
      --gradient: linear-gradient(135deg, #6366f1, #8b5cf6, #a855f7);
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Inter', system-ui, sans-serif; background: var(--bg); color: var(--text); line-height: 1.6; }
    .wrap { max-width: 1280px; margin: 0 auto; padding: 0 1.5rem; }
    
    header { background: linear-gradient(135deg, #0a0a0f, #1a1a2e); border-bottom: 1px solid var(--border); padding: 2rem 0; position: relative; }
    header::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: var(--gradient); }
    h1 { font-size: 2rem; font-weight: 700; background: var(--gradient); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0.75rem; }
    .meta-bar { display: flex; gap: 0.75rem; flex-wrap: wrap; margin-bottom: 1rem; }
    .pill { display: inline-flex; align-items: center; gap: 0.5rem; padding: 0.4rem 0.9rem; background: var(--bg-card); border: 1px solid var(--border); border-radius: 999px; font-size: 0.8rem; color: var(--text-secondary); }
    nav { display: flex; gap: 0.5rem; flex-wrap: wrap; }
    nav a { color: var(--text-secondary); text-decoration: none; font-size: 0.85rem; font-weight: 500; padding: 0.5rem 1rem; border-radius: 0.5rem; background: var(--bg-card); border: 1px solid var(--border); transition: all 0.2s; }
    nav a:hover { background: var(--bg-card-hover); border-color: var(--accent); color: var(--text); }
    
    main { padding: 2rem 0; }
    section { margin-bottom: 2.5rem; }
    h2 { font-size: 1.25rem; font-weight: 600; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.75rem; }
    h2::before { content: ''; width: 4px; height: 1.5rem; background: var(--gradient); border-radius: 2px; }
    
    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 1.25rem; }
    article { background: var(--bg-card); border: 1px solid var(--border); border-radius: 1rem; overflow: hidden; transition: all 0.3s; display: flex; flex-direction: column; }
    article:hover { border-color: var(--accent); box-shadow: 0 0 30px var(--accent-glow); transform: translateY(-2px); }
    article img { width: 100%; height: 160px; object-fit: cover; }
    .no-img { height: 160px; background: var(--bg-elevated); display: flex; align-items: center; justify-content: center; font-size: 2rem; opacity: 0.3; }
    .card-body { padding: 1rem; flex: 1; display: flex; flex-direction: column; }
    .card-meta { display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 0.5rem; }
    .chip { font-size: 0.65rem; font-weight: 600; padding: 0.2rem 0.5rem; border-radius: 999px; text-transform: uppercase; }
    .chip-date { background: rgba(99,102,241,0.15); color: var(--accent-light); }
    .chip-source { background: var(--bg-elevated); color: var(--text-secondary); }
    .chip-breaking { background: rgba(239,68,68,0.2); color: #f87171; }
    .chip-important { background: rgba(245,158,11,0.2); color: #fbbf24; }
    .card-title { font-size: 0.95rem; font-weight: 600; line-height: 1.4; margin-bottom: 0.5rem; }
    .card-title a { color: inherit; text-decoration: none; }
    .card-title a:hover { color: var(--accent-light); }
    .card-summary { font-size: 0.8rem; color: var(--text-secondary); line-height: 1.6; margin-bottom: 0.75rem; flex: 1; display: -webkit-box; -webkit-line-clamp: 5; -webkit-box-orient: vertical; overflow: hidden; }
    .card-link { display: inline-flex; align-items: center; gap: 0.25rem; margin-top: 0.75rem; padding: 0.4rem 0.8rem; background: var(--accent); color: white; text-decoration: none; border-radius: 0.4rem; font-size: 0.75rem; font-weight: 500; transition: all 0.2s; }
    .card-link:hover { background: var(--accent-light); }
    
    /* Compact section for small categories */
    .compact-section { margin-bottom: 2.5rem; }
    .compact-grid { display: flex; flex-direction: column; gap: 1rem; }
    .compact-card { display: flex; gap: 1rem; padding: 1rem; background: var(--bg-card); border: 1px solid var(--border); border-radius: 1rem; transition: all 0.2s; }
    .compact-card:hover { border-color: var(--accent); box-shadow: 0 0 20px var(--accent-glow); }
    .compact-cat { font-size: 1.5rem; padding: 0.5rem; background: var(--bg-elevated); border-radius: 0.5rem; height: fit-content; }
    .compact-body { flex: 1; min-width: 0; }
    .compact-meta { display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 0.5rem; }
    .compact-title { font-size: 1rem; font-weight: 600; line-height: 1.4; margin-bottom: 0.5rem; }
    .compact-title a { color: var(--text); text-decoration: none; }
    .compact-title a:hover { color: var(--accent-light); }
    .compact-summary { font-size: 0.85rem; color: var(--text-secondary); line-height: 1.5; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
    .compact-img { width: 120px; height: 90px; object-fit: cover; border-radius: 0.5rem; flex-shrink: 0; }
    @media (max-width: 600px) { .compact-img { display: none; } }
    
    .other-section { background: var(--bg-card); border: 1px solid var(--border); border-radius: 1rem; padding: 1.5rem; }
    .other-section h2 { margin-bottom: 1.5rem; }
    .other-list { list-style: none; display: flex; flex-direction: column; gap: 0.75rem; }
    .other-item { display: flex; gap: 1rem; padding: 1rem; background: var(--bg-elevated); border: 1px solid var(--border); border-radius: 0.75rem; transition: all 0.2s; }
    .other-item:hover { border-color: var(--accent); }
    .other-num { display: flex; align-items: center; justify-content: center; width: 2rem; height: 2rem; background: var(--gradient); border-radius: 50%; font-size: 0.8rem; font-weight: 600; flex-shrink: 0; }
    .other-content { flex: 1; min-width: 0; }
    .other-title { font-weight: 500; margin-bottom: 0.25rem; }
    .other-title a { color: var(--text); text-decoration: none; }
    .other-title a:hover { color: var(--accent-light); }
    .other-meta { font-size: 0.75rem; color: var(--text-muted); }
    
    footer { padding: 2rem 0; border-top: 1px solid var(--border); margin-top: 2rem; }
    .footer-text { font-size: 0.75rem; color: var(--text-muted); }
    .footer-text strong { color: var(--text-secondary); }
    
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: var(--bg); }
    ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }
  </style>
</head>
<body>
<header>
  <div class="wrap">
    <h1>📰 News Aggregator — {{ today }}</h1>
    <div class="meta-bar">
      <span class="pill">📅 {{ start }} → {{ today }}</span>
      <span class="pill">📰 {{ total_main }} main stories</span>
      <span class="pill">📋 {{ total_other }} other stories</span>
      <span class="pill">🌐 {{ unique_sources }} sources</span>
    </div>
    <nav>
      {% for cat_key, cat_data in categories.items() %}
      {% if sections[cat_key] %}
      <a href="#{{ cat_key }}">{{ cat_data.icon }} {{ cat_data.title }}</a>
      {% endif %}
      {% endfor %}
      <a href="#other">📋 Other Interesting</a>
    </nav>
  </div>
</header>

<main class="wrap">
  {# Large categories (3+ items) get full grid sections #}
  {% for cat_key, cat_data in categories.items() %}
  {% if sections[cat_key]|length >= 3 %}
  <section id="{{ cat_key }}">
    <h2>{{ cat_data.icon }} {{ cat_data.title }}</h2>
    <div class="grid">
      {% for article in sections[cat_key] %}
      <article>
        {% if article.image_url %}
        <img src="{{ article.image_url }}" alt="" loading="lazy" onerror="this.outerHTML='<div class=no-img>📰</div>'">
        {% else %}
        <div class="no-img">📰</div>
        {% endif %}
        <div class="card-body">
          <div class="card-meta">
            <span class="chip chip-date">{{ article.date_str }}</span>
            <span class="chip chip-source">{{ article.outlet }}</span>
            {% if article.priority == 'breaking' %}
            <span class="chip chip-breaking">🔴 Breaking</span>
            {% elif article.priority == 'important' %}
            <span class="chip chip-important">🟠 Important</span>
            {% endif %}
          </div>
          <h3 class="card-title"><a href="{{ article.url }}" target="_blank" rel="noopener">{{ article.title }}</a></h3>
          <p class="card-summary">{{ article.summary }}</p>
          <a href="{{ article.url }}" class="card-link" target="_blank" rel="noopener">Read more →</a>
        </div>
      </article>
      {% endfor %}
    </div>
  </section>
  {% endif %}
  {% endfor %}

  {# Small categories (1-2 items) grouped together in compact section #}
  {% set small_cats = [] %}
  {% for cat_key, cat_data in categories.items() %}
  {% if sections[cat_key]|length >= 1 and sections[cat_key]|length < 3 %}
  {% set _ = small_cats.append(cat_key) %}
  {% endif %}
  {% endfor %}
  
  {% if small_cats %}
  <section id="more-news" class="compact-section">
    <h2>📌 More Top Stories</h2>
    <div class="compact-grid">
      {% for cat_key in small_cats %}
      {% for article in sections[cat_key] %}
      <div class="compact-card">
        <div class="compact-cat">{{ categories[cat_key].icon }}</div>
        <div class="compact-body">
          <div class="compact-meta">
            <span class="chip chip-date">{{ article.date_str }}</span>
            <span class="chip chip-source">{{ article.outlet }}</span>
            {% if article.priority == 'breaking' %}
            <span class="chip chip-breaking">🔴</span>
            {% elif article.priority == 'important' %}
            <span class="chip chip-important">🟠</span>
            {% endif %}
          </div>
          <h3 class="compact-title"><a href="{{ article.url }}" target="_blank" rel="noopener">{{ article.title }}</a></h3>
          <p class="compact-summary">{{ article.summary }}</p>
        </div>
        {% if article.image_url %}
        <img src="{{ article.image_url }}" alt="" class="compact-img" loading="lazy" onerror="this.style.display='none'">
        {% endif %}
      </div>
      {% endfor %}
      {% endfor %}
    </div>
  </section>
  {% endif %}

  <section id="other" class="other-section">
    <h2>📋 Other Interesting News</h2>
    <ul class="other-list">
      {% for article in other_articles %}
      <li class="other-item">
        <span class="other-num">{{ loop.index }}</span>
        <div class="other-content">
          <div class="other-title"><a href="{{ article.url }}" target="_blank" rel="noopener">{{ article.title }}</a></div>
          <div class="other-meta">{{ article.date_str }} • {{ article.outlet }} • {{ categories[article.category].icon }} {{ categories[article.category].title }}</div>
        </div>
      </li>
      {% endfor %}
    </ul>
  </section>
</main>

<footer>
  <div class="wrap">
    <p class="footer-text"><strong>Method:</strong> Intelligent multi-factor scoring, NLP classification, source diversity enforcement.<br>
    <strong>Generated:</strong> {{ generated_at }}</p>
  </div>
</footer>
</body>
</html>''')

# =============================================================================
# MAIN
# =============================================================================

def is_wsl() -> bool:
    """Check if running under WSL."""
    try:
        with open("/proc/version", "r") as f:
            return "microsoft" in f.read().lower()
    except:
        return False

def open_in_browser(filepath: str):
    """Open the generated HTML file in system browser."""
    abs_path = os.path.abspath(filepath)
    system = platform.system().lower()
    
    try:
        if is_wsl():
            # WSL: Try Chrome, then Edge, then default
            chrome_path = "/mnt/c/Program Files/Google/Chrome/Application/chrome.exe"
            edge_path = "/mnt/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
            
            # Convert to Windows path
            win_path = subprocess.run(
                ["wslpath", "-w", abs_path],
                capture_output=True, text=True
            ).stdout.strip()
            
            if os.path.exists(chrome_path):
                subprocess.Popen([chrome_path, "--new-tab", f"file:///{win_path}"])
                print(f"🌐 Opened in Chrome")
            elif os.path.exists(edge_path):
                subprocess.Popen([edge_path, "--new-tab", f"file:///{win_path}"])
                print(f"🌐 Opened in Edge")
            else:
                # Try explorer as fallback
                subprocess.run(["explorer.exe", win_path])
                print(f"🌐 Opened with Windows default")
                
        elif system == "darwin":
            # macOS: Open with Safari or default browser
            subprocess.run(["open", abs_path])
            print(f"🌐 Opened in browser")
            
        elif system == "windows":
            # Native Windows
            os.startfile(abs_path)
            print(f"🌐 Opened in browser")
            
        elif system == "linux":
            # Linux: Try xdg-open
            if shutil.which("xdg-open"):
                subprocess.run(["xdg-open", abs_path])
                print(f"🌐 Opened in browser")
            else:
                print(f"📁 Open manually: {abs_path}")
        else:
            print(f"📁 Open manually: {abs_path}")
            
    except Exception as e:
        print(f"📁 Could not auto-open. Open manually: {abs_path}")

LAST_RAN_FILE = "last_ran_date.txt"
MIN_HOURS = 24
MAX_DAYS = 30

def read_last_ran_date() -> Optional[dt.datetime]:
    """Read the last run date from file."""
    if not os.path.exists(LAST_RAN_FILE):
        return None
    try:
        with open(LAST_RAN_FILE, "r") as f:
            date_str = f.read().strip()
            return dateparser.parse(date_str)
    except Exception:
        return None

def save_last_ran_date():
    """Save current datetime to last ran file."""
    with open(LAST_RAN_FILE, "w") as f:
        f.write(now_utc().isoformat())

def calculate_lookback_period() -> tuple[dt.datetime, dt.datetime]:
    """
    Calculate the lookback period based on last run date.
    - Minimum: 24 hours
    - Maximum: 30 days
    - If last run exists and is between 24h and 30d ago, use that as start
    """
    end = now_utc()
    last_ran = read_last_ran_date()
    
    if last_ran:
        # Ensure timezone aware
        if last_ran.tzinfo is None:
            last_ran = last_ran.replace(tzinfo=dt.timezone.utc)
        
        hours_since = (end - last_ran).total_seconds() / 3600
        
        if hours_since < MIN_HOURS:
            # Less than 24h ago - use minimum 24 hours
            start = end - dt.timedelta(hours=MIN_HOURS)
            print(f"⏰ Last run was {hours_since:.1f}h ago, using minimum {MIN_HOURS}h lookback")
        elif hours_since > MAX_DAYS * 24:
            # More than 30 days ago - cap at 30 days
            start = end - dt.timedelta(days=MAX_DAYS)
            print(f"⏰ Last run was {hours_since/24:.1f}d ago, capping at {MAX_DAYS}d lookback")
        else:
            # Use last run date
            start = last_ran
            print(f"⏰ Continuing from last run: {last_ran.strftime('%Y-%m-%d %H:%M')} UTC")
    else:
        # No last run file - default to 48 hours
        start = end - dt.timedelta(hours=48)
        print("⏰ First run - using default 48h lookback")
    
    return start, end

# =============================================================================
# PRESET LOADING
# =============================================================================

def load_presets() -> dict[str, Any]:
    """Load presets from presets.json file."""
    presets_path = Path(__file__).parent / PRESETS_FILE
    if presets_path.exists():
        try:
            with open(presets_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Remove comment keys
            return {k: v for k, v in data.items() if not k.startswith("_")}
        except Exception as e:
            print(f"⚠️ Could not load presets: {e}")
    return {}

def get_preset(name: str) -> Optional[dict[str, Any]]:
    """Get a specific preset by name."""
    presets = load_presets()
    return presets.get(name)

def list_presets() -> list[str]:
    """List available preset names."""
    return list(load_presets().keys())

def main():
    ap = argparse.ArgumentParser(
        description="News Aggregator v0.2 - Intelligent Curation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python ainews.py                     # Use smart lookback from last run
  python ainews.py --preset ai_focus   # Use AI/ML preset
  python ainews.py --hours 24 --top 15 # Quick 24h summary
  python ainews.py --list-presets      # Show available presets
        """
    )
    ap.add_argument("--sources", default="sources.txt")
    ap.add_argument("--preset", type=str, default=None, 
                    help="Use a preset configuration (e.g., ai_focus, finance, quick_update)")
    ap.add_argument("--list-presets", action="store_true", help="List available presets and exit")
    ap.add_argument("--hours", type=int, default=None, 
                    help="Override lookback hours (ignores last_ran_date.txt)")
    ap.add_argument("--top", type=int, default=None, help="Top articles count")
    ap.add_argument("--other-min", type=int, default=None)
    ap.add_argument("--other-max", type=int, default=None)
    ap.add_argument("--workers", type=int, default=None)
    ap.add_argument("--categories", type=str, default=None,
                    help="Comma-separated list of categories to include (e.g., ai_headlines,finance_markets)")
    
    timestamp = dt.datetime.now().strftime("%Y-%m-%d_%H%M")
    ap.add_argument("--out", default=f"ainews_{timestamp}.html")
    args = ap.parse_args()
    
    # Handle --list-presets
    if args.list_presets:
        presets = load_presets()
        print("📋 Available Presets:")
        print("=" * 50)
        for name, config in presets.items():
            desc = config.get("description", config.get("name", ""))
            hours = config.get("hours")
            hours_str = "smart" if hours is None else f"{hours}"
            top = config.get("top_articles", 30)
            print(f"  {name:15} | {hours_str:>5}h | {top} articles | {desc}")
        print()
        print("Usage: python ainews.py --preset <name>")
        sys.exit(0)
    
    print(f"📰 News Aggregator v{VERSION}")
    print()
    
    # Load preset if specified
    preset_config = {}
    if args.preset:
        preset_config = get_preset(args.preset)
        if not preset_config:
            print(f"❌ Unknown preset: {args.preset}")
            print(f"   Available: {', '.join(list_presets())}")
            sys.exit(1)
        print(f"📋 Using preset: {preset_config.get('name', args.preset)}")
    
    # Apply preset values, CLI args override preset
    top_n = args.top or preset_config.get("top_articles", 30)
    other_min = args.other_min if args.other_min is not None else preset_config.get("other_min", 10)
    other_max = args.other_max if args.other_max is not None else preset_config.get("other_max", 20)
    workers = args.workers or preset_config.get("workers", 25)
    hours_override = args.hours or preset_config.get("hours")  # None means use smart lookback
    
    # Category filtering
    active_categories = None  # None means all
    if args.categories:
        active_categories = [c.strip() for c in args.categories.split(",")]
    elif preset_config.get("categories") and preset_config["categories"] != ["all"]:
        active_categories = preset_config["categories"]
    
    if active_categories:
        valid_cats = [c for c in active_categories if c in CATEGORIES]
        if valid_cats:
            print(f"🏷️ Categories: {', '.join(valid_cats)}")
            active_categories = valid_cats
        else:
            active_categories = None  # Fall back to all
    
    # Calculate lookback period
    if hours_override:
        # Manual override or preset hours
        start = now_utc() - dt.timedelta(hours=hours_override)
        end = now_utc()
        print(f"⏰ Lookback: {hours_override}h")
    else:
        # Use smart lookback based on last run (only for default preset)
        start, end = calculate_lookback_period()
    
    print(f"📅 {start.strftime('%Y-%m-%d %H:%M')} → {end.strftime('%Y-%m-%d %H:%M')} UTC")
    print()
    
    # Caches
    os.makedirs("cache", exist_ok=True)
    resolve_cache = {}
    og_cache = {}
    
    if not os.path.exists(args.sources):
        print(f"❌ Missing {args.sources}")
        sys.exit(1)
    
    # Load sources
    source_urls = load_sources(args.sources)
    print(f"✓ Loaded {len(source_urls)} sources")
    
    # Calculate days for feed building
    hours_lookback = (end - start).total_seconds() / 3600
    days_lookback = max(1, int(hours_lookback // 24) + 1)
    
    # Build feeds
    print("🔍 Discovering feeds...")
    feed_list = build_feed_list(source_urls, days=days_lookback)
    print(f"✓ Found {len(feed_list)} feeds")
    
    # Collect articles
    print(f"\n📥 Fetching articles ({workers} workers)...")
    all_articles = []
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        tasks = [(url, dom, start, end, resolve_cache) for url, dom in feed_list]
        futures = {executor.submit(process_feed, t): t for t in tasks}
        
        with tqdm(total=len(futures), desc="Processing", unit="feed") as pbar:
            for future in as_completed(futures):
                try:
                    articles = future.result()
                    all_articles.extend(articles)
                except:
                    pass
                pbar.update(1)
    
    print(f"✓ Collected {len(all_articles)} articles")
    
    # Deduplicate
    print("🔄 Deduplicating...")
    all_articles = deduplicate_articles(all_articles)
    print(f"✓ {len(all_articles)} unique articles")
    
    # Enrich images for top candidates
    top_candidates = sorted(all_articles, key=lambda x: x.final_score, reverse=True)[:80]
    print(f"\n🖼️ Enriching images...")
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(enrich_image, a, og_cache): a for a in top_candidates}
        with tqdm(total=len(futures), desc="Images", unit="article") as pbar:
            for future in as_completed(futures):
                try:
                    future.result()
                except:
                    pass
                pbar.update(1)
    
    # Filter by active categories if specified
    if active_categories:
        all_articles = [a for a in all_articles if a.category in active_categories]
        print(f"✓ {len(all_articles)} articles in selected categories")
    
    # Select articles
    print("\n📊 Selecting articles...")
    top_articles = select_top_articles(all_articles, top_n=top_n)
    other_articles = select_other_interesting(all_articles, top_articles, other_min, other_max)
    
    print(f"✓ Selected {len(top_articles)} main + {len(other_articles)} other")
    
    # Determine which categories to show (only those with articles or all if no filter)
    display_categories = CATEGORIES if not active_categories else {k: v for k, v in CATEGORIES.items() if k in active_categories}
    
    # Build sections
    sections = {cat: [] for cat in display_categories}
    for article in top_articles:
        sections[article.category].append({
            "title": article.title,
            "url": article.url,
            "outlet": article.outlet,
            "date_str": article.published.strftime("%Y-%m-%d") if article.published else "Unknown",
            "summary": article.summary,
            "image_url": article.image_url,
            "priority": article.priority,
            "why_matters": article.why_matters,
            "category": article.category,
        })
    
    other_list = [{
        "title": a.title,
        "url": a.url,
        "outlet": a.outlet,
        "date_str": a.published.strftime("%Y-%m-%d") if a.published else "Unknown",
        "category": a.category,
    } for a in other_articles]
    
    # Count stats
    unique_sources = len(set(a.outlet_key for a in top_articles + other_articles))
    
    # Generate HTML
    print("\n📝 Generating HTML...")
    html = HTML_TEMPLATE.render(
        today=end.strftime("%Y-%m-%d"),
        start=start.strftime("%Y-%m-%d"),
        total_main=len(top_articles),
        total_other=len(other_articles),
        unique_sources=unique_sources,
        categories=display_categories,
        sections=sections,
        other_articles=other_list,
        generated_at=now_utc().strftime("%Y-%m-%d %H:%M UTC"),
    )
    
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"\n✅ Done! Saved to: {args.out}")
    
    # Save last run date for next time
    save_last_ran_date()
    print(f"📌 Updated {LAST_RAN_FILE} for next run")
    
    print(f"\n📈 Category breakdown:")
    for cat, data in display_categories.items():
        count = len(sections.get(cat, []))
        if count:
            print(f"   {data['icon']} {data['title']}: {count}")
    
    # Auto-open in browser
    open_in_browser(args.out)

if __name__ == "__main__":
    main()
