# 📰 News Aggregator v0.1

An intelligent news aggregation system that curates the most important AI, tech, cybersecurity, and world news from 190+ sources.

## ✨ Features

- **8-Category Classification**: AI/ML, Tools, Governance, Cybersecurity, Tech Industry, Politics, World News, Viral
- **Intelligent Scoring**: Multi-factor algorithm considering recency, importance, and source reputation
- **Source Diversity**: Balanced representation from 190+ trusted sources
- **Smart Lookback**: Remembers last run date, automatically fetches new articles since then
- **Dark Mode UI**: Beautiful, modern dark theme output
- **Auto-Open Browser**: Automatically opens report in Chrome/Safari/default browser
- **Parallel Processing**: 25 concurrent workers for fast fetching

---

## 📋 Requirements

| Requirement | Details |
|-------------|---------|
| Python | 3.9 or higher |
| OS | Linux, macOS, Windows (WSL recommended) |
| Network | Internet connection |
| GPU | **Not required** - pure Python |

---

## 🚀 Quick Start

### Step 1: Make the launcher executable (first time only)
```bash
chmod +x run_ainews.sh
```

### Step 2: Run it!
```bash
./run_ainews.sh
```

That's it! The launcher will:
1. Create a virtual environment (first run only)
2. Install all Python dependencies
3. Fetch and curate news articles
4. Generate a beautiful HTML report
5. Open it in your browser automatically

---

## ⚙️ Customization

### Easy Way: Edit `run_ainews.sh`

Open the launcher script and look for the **CONFIGURATION** section:

```bash
# Number of main articles (default: 30)
TOP_ARTICLES=30

# "Other Interesting" section range
OTHER_MIN=10
OTHER_MAX=20

# Parallel workers (lower if connection issues)
WORKERS=25

# Manual lookback override (leave empty for smart mode)
HOURS_OVERRIDE=""
```

### Advanced: Command Line Options

```bash
python3 ainews.py [OPTIONS]

Options:
  --sources FILE    Source URLs file (default: sources.txt)
  --hours N         Override lookback period in hours
  --top N           Number of main articles (default: 30)
  --other-min N     Min "Other Interesting" articles (default: 10)
  --other-max N     Max "Other Interesting" articles (default: 20)
  --workers N       Parallel fetch workers (default: 25)
  --out FILE        Output filename (default: auto-timestamped)
```

### Examples

```bash
# Quick update - last 24 hours, fewer articles
python3 ainews.py --hours 24 --top 15

# Deep dive - last week, more articles
python3 ainews.py --hours 168 --top 50 --other-max 30

# Fast mode - fewer workers for slow connections
python3 ainews.py --workers 10
```

---

## 📁 File Structure

```
project/
├── ainews.py           # Main aggregator script (don't edit unless developing)
├── sources.txt         # News source URLs (edit to add/remove sources)
├── requirements.txt    # Python dependencies (auto-installed)
├── run_ainews.sh       # Launcher script (edit for customization)
├── README.md           # This file
├── .gitignore          # Git ignore rules
│
├── last_ran_date.txt   # Auto-created: tracks last run time
├── cache/              # Auto-created: URL resolution cache
└── ainews_*.html       # Auto-created: generated reports
```

### What to Edit

| File | Safe to Edit? | Purpose |
|------|---------------|---------|
| `sources.txt` | ✅ Yes | Add/remove news sources |
| `run_ainews.sh` | ✅ Yes (config section) | Change default settings |
| `ainews.py` | ⚠️ Careful | Core logic - only for developers |
| `requirements.txt` | ❌ No | Auto-managed dependencies |

---

## 📰 Adding News Sources

Edit `sources.txt` to customize your news feed:

```bash
# Comments start with #
# Add RSS/Atom feed URLs directly:
https://example.com/feed.xml
https://example.com/rss

# Or add website URLs (feeds auto-discovered):
https://techcrunch.com
https://arstechnica.com

# Reddit subreddits work too:
https://www.reddit.com/r/MachineLearning/
```

### Source Categories Already Included

- **AI/ML**: OpenAI, Anthropic, DeepMind, Hugging Face, ArXiv
- **Tech News**: TechCrunch, The Verge, Ars Technica, Wired
- **Cybersecurity**: Krebs, Bleeping Computer, The Hacker News
- **Business**: Bloomberg, Reuters, Business Insider
- **Policy**: Politico Tech, The Hill, Axios

---

## 🔄 How Smart Lookback Works

The aggregator remembers when you last ran it (stored in `last_ran_date.txt`):

| Scenario | Lookback Period |
|----------|-----------------|
| First run ever | 48 hours |
| Ran 6 hours ago | 24 hours (minimum) |
| Ran 3 days ago | 3 days (from last run) |
| Ran 45 days ago | 30 days (maximum cap) |

**Override anytime** with `--hours N` to manually specify the period.

---

## 🔧 Troubleshooting

### "Permission denied" when running script
```bash
chmod +x run_ainews.sh
```

### Dependencies not installing
```bash
# Activate venv manually and install
source .venv/bin/activate
pip install -r requirements.txt
```

### Browser doesn't open automatically
The report is still generated! Open it manually:
```bash
# On WSL
explorer.exe ainews_*.html

# On macOS
open ainews_*.html

# On Linux
xdg-open ainews_*.html
```

### Too many connection errors
Reduce parallel workers:
```bash
python3 ainews.py --workers 10
```

---

## 📊 Understanding the Output

The generated HTML report contains:

1. **Header**: Date range, total stories, unique sources
2. **Main Sections** (3+ articles each): Full cards with images
3. **More Top Stories**: Compact cards for categories with 1-2 articles
4. **Other Interesting**: List of 10-20 additional noteworthy articles

### Priority Badges
- 🔴 **Breaking**: High importance + very recent
- 🟠 **Important**: Notable story worth attention

---

## 📄 License

MIT License - Feel free to use, modify, and distribute.

## 🤝 Contributing

1. Fork the repository
2. Make your changes
3. Test with `./run_ainews.sh`
4. Submit a pull request
