# News Aggregator - Roadmap v0.2+

> **Version**: 2.0 | **Date**: 2025-12-19 | **Status**: Phase 1 ✅ Phase 2 ✅

---

## Executive Summary

This roadmap evolves the News Aggregator from a CLI tool (v0.1) into a **preset-driven, one-command-installable news curation system** with:
- One-liner curl install for instant setup
- Interactive launcher with topic presets
- 10 content categories (AI, Finance, Crypto, etc.)
- Multi-source verification per story (coming soon)
- Future AI-powered weekly digests

---

## 🎯 Vision

Transform the aggregator into a system that:
- **Installs in one command** via curl ✅
- **Offers one-click topic presets** (AI/ML, Finance, World, etc.) ✅
- **Achieves >95% classification accuracy** (Phase 4)
- **Shows multiple sources per story** (Phase 3)
- **Generates AI-powered summaries** (Phase 5)

---

## ✅ Decisions Made

| Question | Decision | Rationale |
|----------|----------|-----------|
| Preset Storage | **JSON file** | Simple, human-editable, git-friendly |
| ~~Classification Library~~ | **Scrapped** | Adds complexity for little value |
| ~~Sentiment Analysis~~ | **Scrapped** | Importance > Sentiment; no value add |
| Category Limits | **Per Quick Presets menu** | Keep all presets as designed |
| Last Run Date + Presets | **Only for default preset** | Other presets use explicit time windows |
| Source Button Design | **`[Read more →] [CNN] [Reuters]`** | Separate buttons, cleaner UX |

---

## ✅ Phase 1 Complete - Foundation (v0.2)

### Completed Tasks

| Task | Status |
|------|--------|
| Create `ainews-install.sh` curl installer | ✅ Done |
| Add `.ainews_installed` marker detection | ✅ Done |
| Update `run_ainews.sh` with env var awareness | ✅ Done |
| Create `presets.json` with 7 built-in presets | ✅ Done |
| Implement preset loading in `ainews.py` | ✅ Done |
| Add `--preset` CLI argument | ✅ Done |
| Add `--categories` filter argument | ✅ Done |
| Add `--list-presets` command | ✅ Done |
| Add Finance & Markets category + keywords | ✅ Done |
| Add Crypto & Blockchain category + keywords | ✅ Done |
| Add new RSS sources (12 new feeds) | ✅ Done |
| Update README with curl Quick Start | ✅ Done |
| Update version to 0.2 | ✅ Done |

### New Files Created

- `ainews-install.sh` - One-liner curl installer
- `presets.json` - 7 built-in presets

### Categories (Now 10)

| Category | Icon | Status |
|----------|------|--------|
| AI/ML Headlines | 📰 | ✅ Exists |
| Tools, Models & Platforms | 🛠️ | ✅ Exists |
| Governance, Safety & Ethics | ⚖️ | ✅ Exists |
| **Finance & Markets** | 💹 | ✅ **NEW** |
| **Crypto & Blockchain** | ₿ | ✅ **NEW** |
| Cybersecurity | 🔐 | ✅ Exists |
| Tech Industry | 💻 | ✅ Exists |
| Politics & Policy | 🏛️ | ✅ Exists |
| World News | 🌍 | ✅ Exists |
| Viral & Trending | 🔥 | ✅ Exists |

### Available Presets

| Preset | Hours | Articles | Categories |
|--------|-------|----------|------------|
| `default` | smart | 30 | All |
| `ai_focus` | 48 | 25 | AI, Tools, Governance |
| `finance` | 24 | 30 | Finance, Crypto, Tech |
| `cybersecurity` | 48 | 20 | Cyber, Tech |
| `world` | 48 | 25 | World, Politics, Viral |
| `quick_update` | 24 | 15 | All |
| `deep_dive` | 168 | 50 | All |

---

## ✅ Phase 2 Complete - Interactive Launcher (v0.2.x)

**Focus**: Full interactive menu system

### Completed Tasks

| Task | Status |
|------|--------|
| Create interactive menu framework (bash) | ✅ Done |
| Implement main menu with 6 options | ✅ Done |
| Implement Quick Presets menu (7 presets) | ✅ Done |
| Add custom run configuration flow | ✅ Done |
| Add "Save as Preset" info display | ✅ Done |
| Add lookback period quick-set menu | ✅ Done |
| Add help/documentation display | ✅ Done |
| Terminal color/emoji detection | ✅ Done |
| Direct CLI passthrough (skip menu) | ✅ Done |

### Features Implemented

- **Main Menu**: 6 options with emoji icons and color formatting
- **Quick Presets**: All 7 presets accessible from menu
- **Custom Run**: Configure hours, articles, workers, categories interactively
- **Lookback Menu**: Quick selection from 12h to 30 days, plus custom input
- **Preset Management**: List presets, open editor
- **Help Screen**: Usage tips and file documentation
- **Smart Mode Detection**: Menu for no-args, direct run for CLI args
- **Color Support**: Auto-detects terminal capabilities

**Deliverable**: Beautiful interactive launcher with preset management ✅

---

## 🔜 Phase 3: Multi-Source & UI (v0.2.x) - ~1 week

**Focus**: Story clustering and source buttons

| Task | Priority | Effort |
|------|----------|--------|
| Implement article clustering algorithm | 🔴 High | 4h |
| Update Article dataclass for clusters | 🔴 High | 1h |
| Update HTML template for multi-source buttons | 🔴 High | 3h |
| Add reading time estimates | 🟡 Medium | 1h |

**Deliverable**: Articles show `[Read more →] [CNN] [Reuters]`

---

## 🔮 Phase 4: Advanced Curation v2 (v0.3) - TBD

> **Deferred**: Separate plan will be created with user's design documents

**Scope**:
- Semantic clustering algorithm
- Improved classification (>95% accuracy target)
- Enhanced importance scoring
- Multi-source selection logic
- Full architecture diagrams

---

## 🔮 Phase 5: API Summaries (v0.4) - TBD

**Focus**: AI-powered digests

| Task | Priority |
|------|----------|
| Design SQLite schema | 🟡 Medium |
| Implement article history storage | 🟡 Medium |
| Create API abstraction layer (Gemini/OpenAI/Claude/Local) | 🟡 Medium |
| Implement summary generation | 🟡 Medium |
| Add summary menu to launcher | 🟢 Low |

**Deliverable**: Weekly AI-generated news digest

---

## 📁 Current Project Structure

```
ainews/
├── .ainews_installed          # Marker for curl detection
├── .gitignore
├── README.md                  # Updated with curl Quick Start
├── LICENSE
│
├── ainews-install.sh          # NEW: Curl installer
├── run_ainews.sh              # Updated: Preset support
├── ainews.py                  # Updated: v0.2, 10 categories, presets
├── requirements.txt
│
├── presets.json               # NEW: 7 built-in presets
├── sources.txt                # Updated: 12 new Finance/Crypto feeds
├── last_ran_date.txt          # Smart lookback tracking
│
├── cache/                     # URL cache (gitignored)
└── plan/                      # Planning docs
    └── implementation_plan.md
```

---

## 📈 Success Metrics

| Metric | v0.1 | v0.2 ✅ | Target v0.3 |
|--------|------|---------|-------------|
| Install commands | Multiple | **1 (curl)** | 1 |
| Categories | 8 | **10** | 12 |
| Presets available | 0 | **7** | 10+ |
| Classification accuracy | ~80% | ~85% | >95% |
| Multi-source articles | 0% | 0% | 30% |
| AI summaries | ❌ | ❌ | ❌ (v0.4) |

---

## 🚦 Next Steps

1. ✅ ~~Phase 1 complete~~ - curl installer + presets work
2. **Test the new features** - run `./run_ainews.sh --list-presets`
3. **Create GitHub release** - attach `ainews-install.sh` as asset
4. **Begin Phase 2** - interactive launcher menu

---

*Document Updated: 2025-12-18 | Phase 1 Complete*
