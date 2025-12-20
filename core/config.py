"""
core/config.py - Configuration constants, source tiers, and category definitions.

This module contains all static configuration for the News Aggregator:
- Version and HTTP settings
- Source reputation tiers
- 12 category definitions with keywords and exclusion rules
- Importance keywords for scoring
"""
from __future__ import annotations

# =============================================================================
# VERSION & HTTP SETTINGS
# =============================================================================

VERSION = "0.7.2"
UA = f"Mozilla/5.0 (X11; Linux x86_64) NewsAggregator/{VERSION}"
PRESETS_FILE = "config/presets.json"

HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# =============================================================================
# SOURCE REPUTATION TIERS
# =============================================================================

SOURCE_TIERS = {
    # Tier 1: Highest credibility (0.95-1.0)
    "tier_1": {
        "reuters.com": 1.0,
        "apnews.com": 1.0,
        "bloomberg.com": 0.98,
        "ft.com": 0.98,
        "wsj.com": 0.97,
        "nytimes.com": 0.96,
        "nature.com": 0.99,
        "arxiv.org": 0.95,
        "sciencedaily.com": 0.92,
        "bbc.com": 0.95,
        "theguardian.com": 0.94,
    },
    # Tier 2: Major tech news (0.80-0.94)
    "tier_2": {
        "techcrunch.com": 0.90,
        "theverge.com": 0.88,
        "arstechnica.com": 0.89,
        "wired.com": 0.87,
        "technologyreview.com": 0.91,
        "spectrum.ieee.org": 0.90,
        "venturebeat.com": 0.85,
        "zdnet.com": 0.82,
        "engadget.com": 0.80,
        "cnbc.com": 0.88,
        "marketwatch.com": 0.85,
    },
    # Tier 3: Specialized/Quality (0.65-0.79)
    "tier_3": {
        "huggingface.co": 0.78,
        "openai.com": 0.79,
        "deepmind.google": 0.79,
        "nvidia.com": 0.77,
        "marktechpost.com": 0.72,
        "infoq.com": 0.75,
        "hackernoon.com": 0.68,
        "analyticsindiamag.com": 0.70,
        "krebsonsecurity.com": 0.85,
        "bleepingcomputer.com": 0.78,
        "thehackernews.com": 0.75,
        "schneier.com": 0.82,
        "seekingalpha.com": 0.75,
        "coindesk.com": 0.80,
        "cointelegraph.com": 0.78,
        "decrypt.co": 0.75,
        # Science & Health
        "medscape.com": 0.82,
        "statnews.com": 0.80,
        "sciencemag.org": 0.88,
        "newscientist.com": 0.78,
    },
    # Tier 4: Community/Aggregators (0.50-0.64)
    "tier_4": {
        "reddit.com": 0.55,
        "dev.to": 0.58,
        "medium.com": 0.52,
        "substack.com": 0.56,
        "news.ycombinator.com": 0.62,
        "twitter.com": 0.50,
        "x.com": 0.50,
    },
}

# =============================================================================
# 12 CATEGORY SYSTEM (v0.5: added Science & Research, Health & Biotech)
# =============================================================================

CATEGORIES = {
    # =========================================================================
    # CORE AI/TECH (4 categories)
    # =========================================================================
    "ai_headlines": {
        "icon": "📰",
        "title": "AI/ML Headlines",
        "keywords_high": [
            "openai", "anthropic", "deepmind", "gemini", "gpt-5", "claude",
            "mistral", "llama", "agi", "chatgpt", "gpt-4", "claude-3",
        ],
        "keywords_medium": [
            "artificial intelligence", "machine learning", "llm",
            "large language model", "neural network", "transformer",
            "foundation model", "generative ai", "genai",
        ],
        "keywords_low": [
            "ai", "ml", "model", "training", "inference", "benchmark",
            "reasoning", "embedding", "fine-tuning", "prompt",
        ],
        "exclude_if": [
            "stock", "earnings", "ipo", "shares", "investor", "quarterly",
        ],
        "weight": 1.0,
        "tier": 1,
    },
    "tools_platforms": {
        "icon": "🛠️",
        "title": "Tools, Models & Platforms",
        "keywords_high": [
            "api release", "open source", "github release", "framework launch",
            "sdk release", "new model", "model release", "open weights",
        ],
        "keywords_medium": [
            "developer tool", "library", "platform", "hugging face",
            "pytorch", "tensorflow", "langchain", "llamaindex", "vllm",
        ],
        "keywords_low": [
            "tool", "code", "programming", "release", "launch", "checkpoint",
            "repository", "package", "module",
        ],
        "exclude_if": [],
        "weight": 0.95,
        "tier": 1,
    },
    "governance_safety": {
        "icon": "⚖️",
        "title": "Governance, Safety & Ethics",
        "keywords_high": [
            "ai act", "regulation", "alignment", "safety research",
            "ai policy", "ethics board", "ai safety", "responsible ai",
        ],
        "keywords_medium": [
            "ethical ai", "bias", "fairness", "transparency", "audit",
            "compliance", "governance", "accountability",
        ],
        "keywords_low": [
            "policy", "safety", "ethics", "nist", "oecd", "watermark",
            "disclosure", "oversight",
        ],
        "exclude_if": [],
        "weight": 0.90,
        "tier": 2,
    },
    "cybersecurity": {
        "icon": "🔐",
        "title": "Cybersecurity",
        "keywords_high": [
            "data breach", "ransomware", "zero-day", "cve-",
            "critical vulnerability", "nation-state", "apt",
        ],
        "keywords_medium": [
            "hacker", "exploit", "malware", "phishing", "ddos",
            "cyber attack", "security flaw", "threat actor",
        ],
        "keywords_low": [
            "security", "vulnerability", "patch", "encryption",
            "authentication", "firewall", "infosec",
        ],
        "exclude_if": [],
        "weight": 0.95,
        "tier": 1,
    },
    
    # =========================================================================
    # FINANCE/CRYPTO (3 categories)
    # =========================================================================
    "finance_markets": {
        "icon": "💹",
        "title": "Finance & Markets",
        "keywords_high": [
            "stock market", "wall street", "fed rate", "interest rate",
            "earnings report", "market crash", "bull market", "bear market",
        ],
        "keywords_medium": [
            "nasdaq", "s&p 500", "dow jones", "stock price", "trading",
            "investors", "hedge fund", "etf", "federal reserve",
        ],
        "keywords_low": [
            "market", "stocks", "shares", "portfolio", "dividend",
            "bonds", "yield", "economy",
        ],
        "exclude_if": [],
        "weight": 0.85,
        "tier": 2,
    },
    "crypto_blockchain": {
        "icon": "₿",
        "title": "Crypto & Blockchain",
        "keywords_high": [
            "bitcoin", "ethereum", "crypto crash", "btc", "eth",
            "sec crypto", "defi", "nft", "solana",
        ],
        "keywords_medium": [
            "blockchain", "cryptocurrency", "altcoin", "binance",
            "coinbase", "stablecoin", "web3", "dapp",
        ],
        "keywords_low": [
            "crypto", "token", "wallet", "mining", "halving", "memecoin",
        ],
        "exclude_if": [],
        "weight": 0.80,
        "tier": 2,
    },
    "tech_industry": {
        "icon": "💻",
        "title": "Tech Industry",
        "keywords_high": [
            "ipo", "acquisition", "billion dollar", "major funding",
            "layoffs", "ceo", "merger",
        ],
        "keywords_medium": [
            "startup", "funding round", "series a", "series b",
            "valuation", "venture capital", "tech giant",
        ],
        "keywords_low": [
            "tech company", "earnings", "revenue", "hiring",
            "expansion", "partnership",
        ],
        "exclude_if": [],
        "weight": 0.85,
        "tier": 2,
    },
    
    # =========================================================================
    # BROADER NEWS (5 categories)
    # =========================================================================
    "politics_policy": {
        "icon": "🏛️",
        "title": "Politics & Policy",
        "keywords_high": [
            "executive order", "legislation", "congress", "senate",
            "biden", "trump", "eu commission", "parliament",
        ],
        "keywords_medium": [
            "government", "administration", "federal", "regulatory",
            "antitrust", "investigation", "supreme court",
        ],
        "keywords_low": [
            "policy", "political", "law", "legal", "court", "ruling", "ban",
        ],
        "exclude_if": [],
        "weight": 0.80,
        "tier": 2,
    },
    "world_news": {
        "icon": "🌍",
        "title": "World News",
        "keywords_high": [
            "china", "russia", "ukraine", "europe", "asia",
            "middle east", "global crisis",
        ],
        "keywords_medium": [
            "international", "country", "nation", "foreign",
            "trade war", "sanctions", "diplomacy",
        ],
        "keywords_low": [
            "world", "global", "abroad", "overseas", "export", "import",
        ],
        "exclude_if": [],
        "weight": 0.75,
        "tier": 3,
    },
    "viral_trending": {
        "icon": "🔥",
        "title": "Viral & Trending",
        "keywords_high": [
            "viral", "breaking", "trending", "just announced",
            "exclusive", "leaked",
        ],
        "keywords_medium": [
            "meme", "social media", "twitter", "x.com",
            "went viral", "internet", "tiktok",
        ],
        "keywords_low": [
            "popular", "buzz", "hype", "everyone", "massive",
        ],
        "exclude_if": [],
        "weight": 0.60,
        "tier": 3,
    },
    
    # =========================================================================
    # NEW CATEGORIES (v0.5)
    # =========================================================================
    "science_research": {
        "icon": "🔬",
        "title": "Science & Research",
        "keywords_high": [
            "arxiv", "research paper", "peer review", "phd", "scientific study",
            "nature journal", "science journal", "published study",
        ],
        "keywords_medium": [
            "scientific", "experiment", "study finds", "researchers",
            "discovery", "laboratory", "hypothesis", "findings",
        ],
        "keywords_low": [
            "research", "breakthrough", "scientist", "university",
            "academic", "paper", "study",
        ],
        "exclude_if": [
            "product", "launch", "startup", "funding", "ipo",
        ],
        "weight": 0.90,
        "tier": 2,
    },
    "health_biotech": {
        "icon": "🧬",
        "title": "Health & Biotech",
        "keywords_high": [
            "fda", "clinical trial", "vaccine", "crispr", "gene therapy",
            "drug approval", "phase 3", "phase 2",
        ],
        "keywords_medium": [
            "pharmaceutical", "biotech", "medical", "treatment",
            "therapy", "diagnosis", "patient", "healthcare",
        ],
        "keywords_low": [
            "health", "drug", "medicine", "hospital", "disease",
            "symptom", "cure",
        ],
        "exclude_if": [
            "stock", "earnings", "shares", "investor",
        ],
        "weight": 0.88,
        "tier": 2,
    },
}

# =============================================================================
# IMPORTANCE KEYWORDS FOR SCORING
# =============================================================================

IMPORTANCE_KEYWORDS = {
    # Breaking/Urgent
    "breaking": 0.25,
    "exclusive": 0.22,
    "just announced": 0.20,
    "major": 0.15,
    "urgent": 0.18,
    
    # Scale/Impact
    "billion": 0.18,
    "million": 0.12,
    "unprecedented": 0.15,
    "groundbreaking": 0.14,
    "first ever": 0.16,
    "world first": 0.18,
    "breakthrough": 0.17,
    "record": 0.12,
    
    # Major Companies
    "openai": 0.12,
    "google": 0.10,
    "microsoft": 0.10,
    "meta": 0.09,
    "nvidia": 0.11,
    "anthropic": 0.11,
    "deepmind": 0.10,
    "apple": 0.09,
    "amazon": 0.08,
    
    # Security/Legal
    "breach": 0.14,
    "hack": 0.13,
    "vulnerability": 0.12,
    "ransomware": 0.15,
    "lawsuit": 0.13,
    "acquisition": 0.14,
    "ipo": 0.15,
    "layoffs": 0.12,
    
    # Finance & Crypto
    "bitcoin": 0.12,
    "ethereum": 0.11,
    "crypto crash": 0.16,
    "fed rate": 0.14,
    "market crash": 0.18,
    "all-time high": 0.15,
    "record high": 0.14,
    
    # Science & Health
    "cure": 0.15,
    "fda approval": 0.14,
    "clinical trial": 0.12,
    "discovery": 0.13,
}

# =============================================================================
# KNOWN FEEDS BY DOMAIN (for feed discovery)
# =============================================================================

KNOWN_FEEDS_BY_DOMAIN = {
    "techcrunch.com": ["https://techcrunch.com/feed/"],
    "theverge.com": ["https://www.theverge.com/rss/index.xml"],
    "arstechnica.com": ["https://feeds.arstechnica.com/arstechnica/index"],
    "venturebeat.com": ["https://venturebeat.com/category/ai/feed/"],
    "huggingface.co": ["https://huggingface.co/blog/feed.xml"],
    "marktechpost.com": ["https://www.marktechpost.com/feed/"],
    "openai.com": ["https://openai.com/blog/rss.xml"],
}
