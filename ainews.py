#!/usr/bin/env python3
"""
News Aggregator v0.7.2 - Intelligent News Curation with AI Summaries

Main orchestrator that imports from modular components:
- core/: Article dataclass, configuration, fetching logic
- curation/: Clustering, classification, scoring, selection
- output/: HTML templates and generation
- config/: Settings, secrets, setup wizard (v0.6)
- data/: SQLite database for article history (v0.6)
- ai/: AI providers for summaries and digests (v0.6)

Features:
- 12-category classification system
- Preset-based configuration system
- Multi-factor intelligent scoring
- Source diversity enforcement
- Multi-source story clustering (TF-IDF)
- AI-powered summaries (Gemini, OpenAI, Claude, Ollama)
- Weekly/daily AI-generated digests
- SQLite database for article persistence
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
import shutil
import signal
import subprocess
import sys
import warnings
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
# Note: SequenceMatcher moved to curation/clusterer.py fallback
from pathlib import Path
from typing import Optional, Any

from bs4 import XMLParsedAsHTMLWarning
from dateutil import parser as dateparser
from tqdm import tqdm

# Suppress XML parsing warning
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# =============================================================================
# IMPORT FROM MODULES
# =============================================================================

from core.article import Article
from core.config import (
    VERSION,
    UA,
    PRESETS_FILE,
    HEADERS,
    SOURCE_TIERS,
    CATEGORIES,
    IMPORTANCE_KEYWORDS,
)
from core.fetcher import (
    now_utc,
    normalize_url,
    is_duplicate_story,
    load_sources,
    build_feed_list,
    process_feed,
    enrich_image,
)
from output.templates import HTML_TEMPLATE
from curation.clusterer import cluster_articles_tfidf
from curation.precision import is_spacy_available, PrecisionClassifier


# =============================================================================
# DIVERSITY SELECTION (will move to curation/selector.py in Phase 4.2+)
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


# Note: cluster_similar_articles moved to curation/clusterer.py as cluster_articles_tfidf
# Uses TF-IDF vectorization + cosine similarity instead of SequenceMatcher


def calculate_reading_time(article: Article, words_per_minute: int = 200) -> int:
    """
    Estimate reading time in minutes based on title + summary length.
    Minimum 1 minute, adds extra time for articles with images.
    """
    text = f"{article.title} {article.summary}"
    word_count = len(text.split())
    
    # Base reading time
    minutes = max(1, round(word_count / words_per_minute))
    
    # Add time for articles that likely have more content
    if article.image_url:
        minutes += 1  # Articles with images tend to be longer
    
    # Cap at reasonable max
    return min(minutes, 15)


def enrich_reading_times(articles: list[Article]) -> None:
    """Calculate and set reading times for all articles."""
    for article in articles:
        article.reading_time_min = calculate_reading_time(article)


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
# BROWSER OPENING & UTILITIES
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


# =============================================================================
# PRESET LOADING & LAST RUN DATE
# =============================================================================

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


# =============================================================================
# MAIN
# =============================================================================

def main():
    ap = argparse.ArgumentParser(
        description=f"News Aggregator v{VERSION} - Intelligent Curation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python ainews.py                     # Use smart lookback from last run
  python ainews.py --preset ai_focus   # Use AI/ML preset
  python ainews.py --hours 24 --top 15 # Quick 24h summary
  python ainews.py --list-presets      # Show available presets
  python ainews.py --setup             # Configure AI provider
  python ainews.py --digest weekly     # Generate weekly AI digest
  python ainews.py --status            # Show configuration status
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
    
    # Phase 5: AI Integration commands
    ap.add_argument("--setup", action="store_true",
                    help="Run the AI provider setup wizard")
    ap.add_argument("--status", action="store_true",
                    help="Show configuration and AI provider status")
    ap.add_argument("--digest", type=str, choices=["daily", "weekly", "monthly"], default=None,
                    help="Generate AI-powered news digest (daily, weekly, or monthly)")
    ap.add_argument("--fetch-and-digest", type=str, choices=["daily", "weekly", "monthly"], default=None,
                    help="Fetch fresh articles, save to DB, then generate digest")
    ap.add_argument("--save-articles", action="store_true",
                    help="Save fetched articles to database for later digest generation")
    
    # v0.7: Metrics and transparency flags (opt-in only)
    ap.add_argument("--metrics", action="store_true",
                    help="Show precision mode metrics (entity stats, confidence distribution)")
    ap.add_argument("--debug-classify", action="store_true",
                    help="Show per-article classification explanation (verbose)")
    ap.add_argument("--ab-precision", action="store_true",
                    help="Run A/B comparison: Standard vs Precision classification")
    ap.add_argument("--explain-score", action="store_true",
                    help="Show scoring breakdown for top articles")
    
    timestamp = dt.datetime.now().strftime("%Y-%m-%d_%H%M")
    ap.add_argument("--out", default=f"ainews_{timestamp}.html")
    args = ap.parse_args()
    
    # ==========================================================================
    # AUTO-PURGE OLD ARTICLES ON STARTUP
    # ==========================================================================
    try:
        from config.settings import get_settings
        from data.models import delete_old_articles
        
        settings = get_settings()
        max_age = settings.database.max_age_days
        if max_age > 0:
            purged = delete_old_articles(max_age)
            if purged > 0:
                print(f"🗑️ Purged {purged} articles older than {max_age} days")
    except Exception:
        pass  # Ignore if database not initialized yet
    
    # Handle --setup (AI configuration wizard)
    if args.setup:
        from config.setup import setup_wizard
        setup_wizard()
        sys.exit(0)
    
    # Handle --status (show config status)
    if args.status:
        from config.setup import show_status
        from data import get_database_stats
        
        show_status()
        
        # Also show database stats
        print()
        print("  Database:")
        try:
            stats = get_database_stats()
            print(f"    Articles:     {stats['articles']}")
            print(f"    Summaries:    {stats['summaries']}")
            print(f"    Digests:      {stats['digests']}")
            print(f"    Size:         {stats['size_mb']} MB")
        except Exception:
            print("    (not initialized)")
        print()
        sys.exit(0)
    
    # Handle --fetch-and-digest (fetch + save + digest in one command)
    if args.fetch_and_digest:
        print(f"📰 Fetching fresh articles for {args.fetch_and_digest} digest...")
        # Override args to do a full run with save
        args.save_articles = True
        args.digest = None  # Will call digest after the run
        # Continue to main flow, then call digest at the end
        _pending_digest_type = args.fetch_and_digest
    else:
        _pending_digest_type = None
    
    # Handle --digest (generate AI digest from stored articles)
    if args.digest:
        from ai import get_summarizer
        from data.models import get_recent_articles
        
        summarizer = get_summarizer()
        if not summarizer.is_available():
            print("❌ AI provider not configured.")
            print("   Run: python ainews.py --setup")
            sys.exit(1)
        
        # Check if we have articles
        days = {"daily": 1, "weekly": 7, "monthly": 30}[args.digest]
        articles = get_recent_articles(limit=100, days=days)
        
        if not articles:
            print(f"⚠️ No articles found for {args.digest} digest.")
            print(f"   Run: python ainews.py --fetch-and-digest {args.digest}")
            print(f"   Or run the aggregator first to save articles.")
            sys.exit(1)
        
        print(f"📝 Generating {args.digest} digest from {len(articles)} articles...")
        
        if args.digest == "weekly":
            output = summarizer.generate_weekly_digest(output_format="markdown")
        elif args.digest == "monthly":
            output = summarizer.generate_monthly_digest(output_format="markdown")
        else:
            output = summarizer.generate_daily_digest(output_format="markdown")
        
        if output.success:
            print()
            print("=" * 60)
            print(output.text)
            print("=" * 60)
            print()
            print(f"✓ Articles: {output.article_count}")
            print(f"✓ Tokens: {output.token_count}")
            print(f"✓ Provider: {output.provider}/{output.model}")
        else:
            print(f"❌ Failed: {output.error}")
        
        sys.exit(0)
    
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
    
    # Precision mode handling (optional spaCy)
    precision_mode = preset_config.get("precision_mode", False)
    precision_classifier = None
    if precision_mode:
        print("🧠 Precision mode requested...")
        if is_spacy_available():
            precision_classifier = PrecisionClassifier()
            print("✓ spaCy available, precision mode enabled")
        else:
            # Prompt for install
            from curation.precision import prompt_install_spacy, install_spacy
            if prompt_install_spacy():
                if install_spacy():
                    precision_classifier = PrecisionClassifier()
                    print("✓ Precision mode enabled")
                else:
                    print("⚠️ Falling back to standard mode")
            else:
                print("⚠️ spaCy declined, using standard mode")
    
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
    
    # Cluster similar stories from multiple sources using TF-IDF
    print("🔗 Clustering with TF-IDF (threshold=0.75)...")
    all_articles = cluster_articles_tfidf(all_articles, similarity_threshold=0.75)
    multi_source_count = sum(1 for a in all_articles if len(a.related_articles) > 0)
    print(f"✓ Found {multi_source_count} stories with multiple sources")
    
    # Calculate reading times
    enrich_reading_times(all_articles)
    
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
            "related_articles": article.related_articles,  # List of (outlet, url) tuples
            "reading_time": article.reading_time_min,
        })
    
    other_list = [{
        "title": a.title,
        "url": a.url,
        "outlet": a.outlet,
        "date_str": a.published.strftime("%Y-%m-%d") if a.published else "Unknown",
        "category": a.category,
        "related_articles": a.related_articles,
        "reading_time": a.reading_time_min,
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
    
    # AUTO-SAVE articles to database (always, not just when --save-articles)
    all_to_save = top_articles + other_articles
    try:
        from data import save_articles
        saved_count = save_articles(all_to_save)
        print(f"💾 Saved {saved_count} articles to database")
    except Exception as e:
        print(f"⚠️ Could not save articles to database: {e}")
    
    print(f"\n📈 Category breakdown:")
    for cat, data in display_categories.items():
        count = len(sections.get(cat, []))
        if count:
            print(f"   {data['icon']} {data['title']}: {count}")
    
    # ==========================================================================
    # v0.7: METRICS OUTPUT (opt-in via --metrics, --ab-precision, --explain-score)
    # ==========================================================================
    if args.metrics or args.ab_precision or args.explain_score:
        from curation.metrics import (
            calculate_entity_stats,
            run_ab_comparison,
            print_metrics_summary,
            print_score_breakdown,
        )
        
        all_articles = top_articles + other_articles
        
        # Calculate entity stats if precision mode
        entity_stats = None
        if args.metrics and precision_mode:
            entity_stats = calculate_entity_stats(all_articles)
        
        # Run A/B comparison if requested
        ab_result = None
        if args.ab_precision:
            print("\n⚡ Running A/B comparison (this may take a moment)...")
            ab_result = run_ab_comparison(all_articles)
        
        # Print metrics summary
        if args.metrics or args.ab_precision:
            print_metrics_summary(
                all_articles,
                entity_stats=entity_stats,
                ab_result=ab_result,
                precision_mode=precision_mode
            )
        
        # Print score breakdown
        if args.explain_score:
            print_score_breakdown(all_articles, top_n=10)
    
    # Auto-open in browser
    open_in_browser(args.out)
    
    # If --fetch-and-digest was used, now generate the digest
    if _pending_digest_type:
        print()
        print("=" * 60)
        print(f"📝 Now generating {_pending_digest_type} digest...")
        print("=" * 60)
        
        from ai import get_summarizer
        
        summarizer = get_summarizer()
        if not summarizer.is_available():
            print("❌ AI provider not configured. Run: python ainews.py --setup")
        else:
            if _pending_digest_type == "weekly":
                output = summarizer.generate_weekly_digest(output_format="markdown")
            elif _pending_digest_type == "monthly":
                output = summarizer.generate_monthly_digest(output_format="markdown")
            else:
                output = summarizer.generate_daily_digest(output_format="markdown")
            
            if output.success:
                print()
                print(output.text)
                print()
                print(f"✓ Articles: {output.article_count}")
                print(f"✓ Tokens: {output.token_count}")
                print(f"✓ Provider: {output.provider}/{output.model}")
            else:
                print(f"❌ Digest failed: {output.error}")


def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully."""
    print("\n")
    print("⚠️  Interrupted by user (Ctrl+C)")
    print("   Exiting gracefully...")
    sys.exit(130)  # Standard exit code for SIGINT


if __name__ == "__main__":
    # Set up signal handlers for graceful exit
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n")
        print("⚠️  Interrupted by user (Ctrl+C)")
        print("   Exiting gracefully...")
        sys.exit(130)
