# 📰 News Aggregator v0.3

An intelligent news aggregation system that curates the most important AI, tech, finance, crypto, cybersecurity, and world news from 200+ sources.

## ✨ Features

- **10-Category Classification**: AI/ML, Tools, Governance, Finance, Crypto, Cybersecurity, Tech Industry, Politics, World News, Viral
- **Preset System**: Quick presets for different use cases (AI focus, Finance, Quick Update, Deep Dive)
- **Intelligent Scoring**: Multi-factor algorithm considering recency, importance, and source reputation
- **Source Diversity**: Balanced representation from 200+ trusted sources
- **Smart Lookback**: Remembers last run date, automatically fetches new articles since then
- **Dark Mode UI**: Beautiful, modern dark theme output
- **Auto-Open Browser**: Automatically opens report in Chrome/Safari/default browser
- **Parallel Processing**: 25 concurrent workers for fast fetching

---

## 🚀 Quick Start

### One Command Install & Run

Copy and paste this into your terminal:

```bash
curl -fsSL https://github.com/dominiclampron/ainews/releases/latest/download/ainews-install.sh | bash
```

That's it! The script will:
1. Clone the repository (first run only)
2. Set up Python virtual environment
3. Install dependencies
4. Launch the **interactive menu**
5. Open your news report in the browser

---

### Adding Options

You can pass options to customize the run. Add `-s --` after `bash`, then your options:

```bash
curl -fsSL https://github.com/dominiclampron/ainews/releases/latest/download/ainews-install.sh | bash -s -- [OPTIONS]
```

#### Available Options

| Option | Description |
|--------|-------------|
| `--preset ai_focus` | AI/ML focused news only |
| `--preset finance` | Finance, crypto & tech industry |
| `--preset quick_update` | Fast 24h summary, fewer articles |
| `--preset deep_dive` | Full week, comprehensive report |
| `--hours 24` | Look back 24 hours |
| `--top 20` | Get 20 main articles |
| `--update` | Update to latest version before running |
| `--list-presets` | Show all available presets |

#### Examples

```bash
# Use AI/ML preset
curl -fsSL https://github.com/dominiclampron/ainews/releases/latest/download/ainews-install.sh | bash -s -- --preset ai_focus

# Quick 24-hour summary
curl -fsSL https://github.com/dominiclampron/ainews/releases/latest/download/ainews-install.sh | bash -s -- --preset quick_update

# Update to latest version, then run finance preset
curl -fsSL https://github.com/dominiclampron/ainews/releases/latest/download/ainews-install.sh | bash -s -- --update --preset finance

# Show all presets
curl -fsSL https://github.com/dominiclampron/ainews/releases/latest/download/ainews-install.sh | bash -s -- --list-presets
```

---

## 📋 Requirements

| Requirement | Details |
|-------------|---------|
| Python | 3.9 or higher |
| OS | Linux, macOS, Windows (WSL recommended) |
| Network | Internet connection |
| GPU | **Not required** - pure Python |

---

## 🖥️ Interactive Launcher

Running without arguments launches an interactive menu:

```bash
./run_ainews.sh
```

```
╔══════════════════════════════════════════════════════════╗
║           📰 NEWS AGGREGATOR v0.2 - LAUNCHER             ║
╚══════════════════════════════════════════════════════════╝

  [1] 🚀 Run with Default Settings
  [2] 📋 Quick Presets
  [3] ⚙️  Custom Run (configure options)
  [4] 📅 Set Lookback Period
  [5] 💾 Manage Presets
  [6] ℹ️  Help / Documentation
  [0] ❌ Exit
```

### Menu Options

| Option | Description |
|--------|-------------|
| **1. Default Settings** | Full coverage with smart lookback |
| **2. Quick Presets** | Choose from 7 preset configurations |
| **3. Custom Run** | Configure hours, article counts, workers, categories |
| **4. Lookback Period** | Quick selection: 12h, 24h, 48h, 7 days, etc. |
| **5. Manage Presets** | List presets, edit presets.json |
| **6. Help** | Documentation and usage tips |

---

## 🛠️ Developer Setup

For contributors or advanced users who want to clone directly:

```bash
# Clone the repository
git clone https://github.com/dominiclampron/ainews.git
cd ainews

# Launch interactive menu
./run_ainews.sh

# Or run directly with preset (skip menu)
./run_ainews.sh --preset ai_focus
```

### Show Available Presets

```bash
./run_ainews.sh --list-presets
```

---

## 📋 Available Presets

| Preset | Hours | Articles | Categories | Description |
|--------|-------|----------|------------|-------------|
| `default` | smart* | 30 | All | Full coverage with smart lookback |
| `ai_focus` | 48h | 25 | AI, Tools, Governance | AI/ML headlines and developments |
| `finance` | 24h | 30 | Finance, Crypto, Tech | Markets, stocks, and crypto news |
| `cybersecurity` | 48h | 20 | Cyber, Tech | Security threats and vulnerabilities |
| `world` | 48h | 25 | World, Politics, Viral | Global news and policy |
| `quick_update` | 24h | 15 | All | Fast summary, fewer articles |
| `deep_dive` | 168h | 50 | All | Full week comprehensive report |

*smart = Uses time since last run (24h minimum, 30 days maximum)

### Preset Usage Examples

```bash
# Via curl installer
curl -fsSL https://...ainews-install.sh | bash -s -- --preset ai_focus
curl -fsSL https://...ainews-install.sh | bash -s -- --preset finance
curl -fsSL https://...ainews-install.sh | bash -s -- --preset quick_update

# Via launcher script
./run_ainews.sh --preset ai_focus
./run_ainews.sh --preset cybersecurity
./run_ainews.sh --preset deep_dive

# Via Python directly
python3 ainews.py --preset world
python3 ainews.py --preset finance --hours 12  # Override preset hours
```

---

## ⚙️ Command Line Options

```bash
python3 ainews.py [OPTIONS]

Preset Options:
  --preset NAME      Use a preset: default, ai_focus, finance, cybersecurity,
                     world, quick_update, deep_dive
  --list-presets     List all available presets and exit

Filter Options:
  --categories LIST  Comma-separated categories to include
                     (e.g., ai_headlines,finance_markets,crypto_blockchain)
  --hours N          Override lookback period in hours

Output Options:
  --top N            Number of main articles (default: 30)
  --other-min N      Min "Other Interesting" articles (default: 10)
  --other-max N      Max "Other Interesting" articles (default: 20)
  --out FILE         Output filename (default: auto-timestamped)

Performance Options:
  --sources FILE     Source URLs file (default: sources.txt)
  --workers N        Parallel fetch workers (default: 25)
```

### Examples

```bash
# Quick AI-only update
python3 ainews.py --preset ai_focus

# Finance & Crypto focus
python3 ainews.py --preset finance

# World news and politics
python3 ainews.py --preset world

# Cybersecurity brief
python3 ainews.py --preset cybersecurity

# Deep dive - last week, comprehensive
python3 ainews.py --preset deep_dive

# Specific categories only (custom filter)
python3 ainews.py --categories ai_headlines,crypto_blockchain

# Fast mode - fewer workers for slow connections
python3 ainews.py --workers 10
```

---

## 📁 File Structure

```
ainews/
├── ainews-install.sh   # Curl one-liner installer
├── run_ainews.sh       # Launcher script (edit for defaults)
├── ainews.py           # Main aggregator script
├── presets.json        # Preset configurations (edit to customize)
├── sources.txt         # News source URLs (edit to add/remove)
├── requirements.txt    # Python dependencies (auto-installed)
├── README.md           # This file
├── .gitignore          # Git ignore rules
│
├── .ainews_installed   # Auto-created: installation marker
├── last_ran_date.txt   # Auto-created: tracks last run time
├── cache/              # Auto-created: URL resolution cache
└── ainews_*.html       # Auto-created: generated reports
```

### What to Edit

| File | Safe to Edit? | Purpose |
|------|---------------|---------|
| `sources.txt` | ✅ Yes | Add/remove news sources |
| `presets.json` | ✅ Yes | Create custom presets |
| `run_ainews.sh` | ✅ Yes (config section) | Change default settings |
| `ainews.py` | ⚠️ Careful | Core logic - only for developers |
| `requirements.txt` | ❌ No | Auto-managed dependencies |

---

## 📰 Categories

| Category | Icon | Description |
|----------|------|-------------|
| AI/ML Headlines | 📰 | OpenAI, Anthropic, DeepMind news |
| Tools & Platforms | 🛠️ | New releases, frameworks, SDKs |
| Governance & Safety | ⚖️ | AI policy, regulation, ethics |
| Finance & Markets | 💹 | Stocks, markets, trading |
| Crypto & Blockchain | ₿ | Bitcoin, Ethereum, DeFi |
| Cybersecurity | 🔐 | Breaches, vulnerabilities, threats |
| Tech Industry | 💻 | Funding, acquisitions, layoffs |
| Politics & Policy | 🏛️ | Government, legislation |
| World News | 🌍 | Global events, international |
| Viral & Trending | 🔥 | Breaking, trending stories |

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

---

## 🔄 How Smart Lookback Works

The aggregator remembers when you last ran it (stored in `last_ran_date.txt`):

| Scenario | Lookback Period |
|----------|-----------------|
| First run ever | 48 hours |
| Ran 6 hours ago | 24 hours (minimum) |
| Ran 3 days ago | 3 days (from last run) |
| Ran 45 days ago | 30 days (maximum cap) |

**Note**: Smart lookback only applies when using default settings. Presets use their configured hours.

**Override anytime** with `--hours N` to manually specify the period.

---

## 🔧 Troubleshooting

### "Permission denied" when running script
```bash
chmod +x run_ainews.sh ainews-install.sh
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
