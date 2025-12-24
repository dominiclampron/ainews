# 📰 News Aggregator v0.8.0

**See the most important news in seconds !**

Pulls from **200+ curated sources in parallel**, **dedupes + clusters** related coverage, **ranks by signal**, and generates a **beautiful dark-mode report** that **auto-opens** when it's done. Optional **AI summaries/digests** and optional **spaCy "Precision Mode"** for stronger entity-aware classification.

> 💡 **Works without AI** — the aggregator runs standalone. AI features (summaries, digests) are opt-in.

---

## Table of Contents

1. [Core Features](#-core-features)
2. [Quick Start](#-quick-start)
3. [Using the Interactive Menu](#-using-the-interactive-menu)
4. [Categories](#-categories)
5. [Requirements](#-requirements)
6. [Advanced Usage (CLI)](#-advanced-usage-cli)
7. [AI Provider Setup & Security](#-ai-provider-setup--security)
8. [Digests](#-digests)
9. [Troubleshooting](#-troubleshooting)
10. [Project Structure](#-project-structure)
11. [Version History](#-version-history)

---

## ✨ Core Features

### What It Does

- **Fetches** articles from 200+ RSS feeds in parallel (25 workers)
- **Classifies** each article into one of 12 categories
- **Scores** articles by recency, source reputation, and keyword importance
- **Deduplicates** and clusters related stories from multiple sources
- **Generates** a beautiful dark-mode HTML report
- **Auto-opens** the report in your browser

### Smart Lookback

The aggregator remembers when you last ran it. If you run it again, it automatically fetches only articles since your last run (capped at 30 days).

### Article Selection

- **Top 30** highest-scoring articles in the main report
- **10–20** "Other Interesting" articles for broader coverage
- **Max 3** articles from the same source (diversity enforcement)

---

## 🚀 Quick Start

### One Command Install & Run

```bash
curl -fsSL https://raw.githubusercontent.com/dominiclampron/ainews/main/ainews-install.sh | bash
```

**What happens:**
1. Checks for `git` and `python3` (required)
2. Clones the repository to `~/ainews`
3. Creates a Python virtual environment
4. Installs all dependencies
5. Opens the **interactive menu** for you to run the aggregator

> **Note:** First-time AI setup is optional. The aggregator works without AI—it just won't generate summaries or digests until you configure a provider.

---

## 🖥️ Using the Interactive Menu

### Main Menu

```
╔══════════════════════════════════════════════════════════╗
║           📰 NEWS AGGREGATOR v0.8 - LAUNCHER             ║
╚══════════════════════════════════════════════════════════╝

[1] 🚀 Run with Default Settings    → Fetch articles, generate HTML report
[2] 📋 Quick Presets                → Choose preset (AI Focus, Finance, etc.)
[3] ⚙️  Custom Run                   → Configure hours, categories, article count
[4] 📅 Set Lookback Period          → 12h / 24h / 48h / 7 days / custom
[5] 💾 Manage Presets               → View/edit preset configurations
[6] 🤖 AI Settings & Digest         → Configure AI, generate digests
[7] 🔧 Settings                     → Install spaCy, set max article age
[8] ℹ️  Help / Documentation        → View help and version info
[0] ❌ Exit
```

### Common Workflows

| Goal | Menu Path |
|------|-----------|
| **Quick daily update** | `[1]` or `[2] → [6] Quick Update` |
| **Focus on AI/ML only** | `[2] → [1] AI/ML Focus` |
| **Full 7-day report** | `[2] → [7] Deep Dive` |
| **Generate AI digest** | `[6] → [2] Daily Digest` or `[3] Weekly Digest` |
| **Set up AI provider** | `[6] → [1] Configure AI Provider` |
| **Install spaCy** | `[7] → [4] Install spaCy Precision Mode` |

### Presets Menu (`[2]`)

| # | Preset | Lookback | Articles |
|---|--------|----------|----------|
| 1 | 🤖 AI/ML Focus | 48h | 25 |
| 2 | 💹 Finance & Markets | 24h | 30 |
| 3 | 🔐 Cybersecurity | 48h | 20 |
| 4 | 🌍 World & Politics | 48h | 25 |
| 5 | 📰 Full Coverage | Smart | 30 |
| 6 | ⚡ Quick Update | 24h | 15 |
| 7 | 📚 Deep Dive | 7 days | 50 |
| 8 | 🧠 Precision Mode | Smart | 30 |

---

## 📂 Categories

The aggregator classifies articles into **12 categories**:

| Icon | Category | Description |
|------|----------|-------------|
| 📰 | **AI/ML Headlines** | OpenAI, Anthropic, model releases, AI research |
| 🛠️ | **Tools & Platforms** | APIs, SDKs, open-source releases, frameworks |
| ⚖️ | **Governance & Safety** | AI regulation, ethics, policy, alignment |
| 🔐 | **Cybersecurity** | Breaches, vulnerabilities, malware, hacking |
| 💹 | **Finance & Markets** | Stock market, Fed, earnings, trading |
| ₿ | **Crypto & Blockchain** | Bitcoin, Ethereum, DeFi, NFTs, exchanges |
| 💻 | **Tech Industry** | Startups, funding, layoffs, acquisitions |
| 🏛️ | **Politics & Policy** | Legislation, government, antitrust |
| 🌍 | **World News** | International, geopolitics, trade |
| 🔥 | **Viral & Trending** | Breaking news, viral content, social media |
| 🔬 | **Science & Research** | Papers, discoveries, academic research |
| 🏥 | **Health & Biotech** | Medical, FDA, biotech, pharma |


### Manual Installation

```bash
git clone https://github.com/dominiclampron/ainews.git
cd ainews
python3 -m venv .venv
source .venv/bin/activate        # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
./run_ainews.sh                  # Or: python ainews.py
```

### 🐳 Docker

```bash
# Build the image
docker build -t ainews .
```

| Volume | Contents |
|--------|----------|
| `./out` | HTML reports |
| `./data` | Database, last run tracking |

**Linux/WSL:**
```bash
docker run --rm -v ./out:/out -v ./data:/data ainews
```

**macOS (interactive menu):**
```bash
mkdir -p out data
docker run --rm -it -v "$PWD/out:/out" -v "$PWD/data:/data" ainews --menu
```

**Windows PowerShell:**
```powershell
docker run --rm -v ${PWD}/out:/out -v ${PWD}/data:/data ainews
```

**Interactive menu (all platforms, add -it):**
```bash
docker run --rm -it -v "$PWD/out:/out" -v "$PWD/data:/data" ainews --menu
```

**With API keys:**
```bash
docker run --rm -v "$PWD/out:/out" -v "$PWD/data:/data" --env-file .env ainews
```

**Docker Compose:**
```bash
docker-compose up --build
```

---

## 📋 Requirements
### Required

- **Python 3.9+** (3.10+ recommended)
- **Operating System:** macOS, Linux, or Windows (WSL recommended)
- **Network:** Internet connection for RSS fetching

### Auto-Installed Dependencies

These are installed automatically via `pip install -r requirements.txt`:

- `requests`, `feedparser` — RSS fetching
- `beautifulsoup4`, `lxml` — HTML parsing
- `python-dateutil` — Date parsing
- `jinja2` — HTML templating
- `tqdm` — Progress bars
- `scikit-learn` — TF-IDF clustering
- `python-dotenv` — Environment variables

### Optional Dependencies

| Feature | Dependency | Install Command |
|---------|------------|-----------------|
| **Gemini AI** | `google-generativeai` | `pip install google-generativeai` |
| **OpenAI** | `openai` | `pip install openai` |
| **Claude** | `anthropic` | `pip install anthropic` |
| **Ollama (local)** | `ollama` | `pip install ollama` |
| **Precision Mode** | `spacy` | Via menu: `[7] → [4]` |

---

## 🖥️ Advanced Usage (CLI)

For power users, bypass the interactive menu:

```bash
source .venv/bin/activate
python ainews.py [options]
```

### CLI Options

```
Presets:
  --preset NAME        Use a preset (default, ai_focus, finance, etc.)
  --list-presets       List all available presets and exit

Filters:
  --categories LIST    Comma-separated categories (e.g., ai_headlines,cybersecurity)
  --hours N            Override lookback period in hours

Output:
  --top N              Number of main articles (default: 30)
  --other-min N        Min "Other Interesting" articles (default: 10)
  --other-max N        Max "Other Interesting" articles (default: 20)
  --out FILE           Output filename (default: auto-timestamped)

Performance:
  --sources FILE       Source URLs file (default: sources.txt)
  --workers N          Parallel fetch workers (default: 25)

AI Commands:
  --setup              Run the AI provider configuration wizard
  --status             Show configuration and database status
  --digest TYPE        Generate digest from saved articles (daily/weekly/monthly)
  --fetch-and-digest TYPE    Fetch, save, then generate digest
  --save-articles      Save fetched articles to database

v0.7 Metrics (opt-in):
  --metrics            Show precision mode metrics
  --ab-precision       A/B comparison: Standard vs Precision
  --explain-score      Scoring breakdown for top articles
  --debug-classify     Per-article classification debug
```

### CLI Examples

```bash
# Default run (smart lookback)
python ainews.py

# AI/ML focus preset
python ainews.py --preset ai_focus

# Quick 24-hour summary, 15 articles
python ainews.py --hours 24 --top 15

# Cybersecurity + AI only
python ainews.py --categories cybersecurity,ai_headlines --hours 48

# Full week comprehensive report
python ainews.py --preset deep_dive

# Precision mode with metrics
python ainews.py --preset precision --metrics

# A/B comparison
python ainews.py --ab-precision --hours 24
```

### Presets Reference

| Preset | Name | Categories | Lookback | Articles |
|--------|------|------------|----------|----------|
| `default` | Full Coverage | All | Smart | 30 |
| `ai_focus` | AI/ML Focus | AI, Tools, Governance | 48h | 25 |
| `finance` | Finance & Markets | Finance, Crypto, Tech | 24h | 30 |
| `cybersecurity` | Cybersecurity Brief | Cybersecurity, Tech | 48h | 20 |
| `world` | World News & Politics | World, Politics, Viral | 48h | 25 |
| `quick_update` | Quick Update | All | 24h | 15 |
| `deep_dive` | Deep Dive | All | 7 days | 50 |
| `precision` | Precision Mode | All | Smart | 30 |

---

## 🔐 AI Provider Setup & Security

### Supported Providers

| Provider | API Key Required | Models |
|----------|------------------|--------|
| **Gemini** | Yes | gemini-2.5-flash (default), gemini-1.5-pro |
| **OpenAI** | Yes | gpt-4o, gpt-4o-mini, gpt-3.5-turbo |
| **Claude** | Yes | claude-3-sonnet, claude-3-haiku |
| **Ollama** | No (local) | llama3.1, mistral, etc. |

### Setup via Menu (Recommended)

1. Run `./run_ainews.sh`
2. Select `[6] 🤖 AI Settings & Digest`
3. Select `[1] Configure AI Provider`
4. Follow the prompts to enter your API key

### Setup via CLI

```bash
python ainews.py --setup
```

### Where Keys Are Stored

- **`.env`** file in the project root (plaintext — keep private)
- `config.json` stores provider/model selection (no secrets)

### Security Warning

> ⚠️ **Never commit `.env` or `*.db` files to git!**
>
> Both are already in `.gitignore`. If you fork this repo, double-check that your API keys and database are not being tracked.

---

## 📅 Digests

AI-generated summaries of recent news.

### Types

| Type | Period | Use Case |
|------|--------|----------|
| **Daily** | Last 24 hours | Morning briefing |
| **Weekly** | Last 7 days | End-of-week summary |
| **Monthly** | Last 30 days | Long-term trends |

### Generate via Menu

1. `[6] 🤖 AI Settings & Digest`
2. Choose `[2] Daily Digest`, `[3] Weekly Digest`, or `[4] Monthly Digest`
3. If articles exist in database, digest is generated immediately

### Generate via CLI

```bash
# From saved articles (must have run aggregator first with --save-articles or default)
python ainews.py --digest daily
python ainews.py --digest weekly
python ainews.py --digest monthly

# Fetch fresh + generate digest in one command
python ainews.py --fetch-and-digest weekly
```

---

## 🔧 Troubleshooting

### Browser Doesn't Open

| OS | Solution |
|----|----------|
| **WSL** | Chrome/Edge are tried first; if not found, `explorer.exe` is used |
| **macOS** | Uses `open` command (default browser) |
| **Linux** | Uses `xdg-open` if available |

If auto-open fails, the file path is printed—open it manually.

### "No articles found"

- Check your internet connection
- Try increasing `--hours` (e.g., `--hours 72`)
- Verify `sources.txt` exists and contains valid RSS URLs

### AI Digest Fails

- Run `python ainews.py --status` to check AI configuration
- Ensure your API key is valid
- Check your provider's rate limits

### spaCy Installation Issues

Install manually:
```bash
source .venv/bin/activate
pip install spacy
python -m spacy download en_core_web_sm
```

### Dependency Errors

```bash
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

---

## 📁 Project Structure

```
ainews/
├── ainews.py              # Main orchestrator
├── run_ainews.sh          # Interactive menu launcher
├── ainews-install.sh      # One-line installer
├── sources.txt            # RSS feed URLs (200+)
├── presets.json           # Preset configurations
├── config.json            # Runtime configuration
├── .env                   # API keys (gitignored)
├── requirements.txt       # Python dependencies
│
├── core/                  # Core logic
│   ├── article.py         # Article dataclass
│   ├── config.py          # Categories, source tiers, keywords
│   └── fetcher.py         # RSS fetching, scoring
│
├── curation/              # Classification & clustering
│   ├── classifier.py      # 12-category classifier
│   ├── clusterer.py       # TF-IDF story clustering
│   ├── precision.py       # spaCy NER precision mode
│   └── metrics.py         # v0.7 transparency metrics
│
├── ai/                    # AI providers
│   ├── factory.py         # Provider factory
│   ├── gemini.py          # Gemini provider
│   ├── openai.py          # OpenAI provider
│   ├── claude.py          # Claude provider
│   ├── ollama.py          # Ollama (local) provider
│   └── summarizer.py      # Digest generation
│
├── config/                # Configuration
│   ├── settings.py        # Settings management
│   ├── secrets.py         # API key handling
│   ├── setup.py           # Setup wizard
│   ├── entity_map.json    # NER entity mappings
│   ├── category_weights.json  # Preset weights
│   └── exclusions.json    # Classification exclusions
│
├── data/                  # Database
│   ├── database.py        # SQLite connection
│   └── models.py          # Article, Summary, Digest models
│
├── output/                # HTML generation
│   └── templates.py       # Jinja2 HTML template
│
└── tests/                 # Tests
    ├── test_regression.py # v0.7 regression tests
    └── fixtures/          # Test data
```

---

### v0.7 Additions: Transparency & Metrics

New opt-in flags for inspecting classification behavior:

| Flag | Description |
|------|-------------|
| `--metrics` | Show entity stats and confidence distribution |
| `--ab-precision` | Run A/B comparison: Standard vs Precision mode |
| `--explain-score` | Show scoring breakdown for top articles |
| `--debug-classify` | Per-article classification explanation (verbose) |

These flags produce additional terminal output but do not change the default behavior or HTML report.

---

## 📜 Version History

| Version | Date | Highlights |
|---------|------|------------|
| **0.7.0** | 2025-12-20 | Classification transparency, --metrics, --ab-precision, regression corpus |
| **0.6.1** | 2025-12-19 | Classification accuracy fix, AI menu, rate limiting |
| **0.6.0** | 2025-12-18 | AI summaries, digests, SQLite database, setup wizard |
| **0.5.0** | 2025-12-17 | 12-category system, presets, TF-IDF clustering |
| **0.4.0** | 2025-12-16 | Interactive menu, source diversity |
| **0.3.0** | 2025-12-15 | Multi-factor scoring, smart lookback |
| **0.2.0** | 2025-12-14 | Dark mode UI, image enrichment |
| **0.1.0** | 2025-12-13 | Initial release |

For full details, see [CHANGELOG.md](CHANGELOG.md).

---

**Made with ☕ and AI**
