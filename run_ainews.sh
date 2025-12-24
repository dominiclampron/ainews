#!/usr/bin/env bash
# =============================================================================
# News Aggregator v0.8.1 - Interactive Launcher
# =============================================================================
# This script provides an interactive menu for running the news aggregator.
#
# USAGE:
#   ./run_ainews.sh                    # Launch interactive menu
#   ./run_ainews.sh --preset ai_focus  # Direct run with preset (skip menu)
#   ./run_ainews.sh --menu             # Force interactive menu
#   ./run_ainews.sh --list-presets     # Show available presets
#   ./run_ainews.sh --help             # Show all options
#
# =============================================================================

set -euo pipefail

# =============================================================================
# SIGNAL HANDLING - Graceful Ctrl+C
# =============================================================================

cleanup() {
    echo ""
    echo ""
    echo "⚠️  Interrupted by user (Ctrl+C)"
    echo "   Cleaning up..."
    
    # Kill any background jobs (portable: works on macOS and Linux)
    jobs -p 2>/dev/null | while read pid; do kill "$pid" 2>/dev/null; done || true
    
    echo "   Goodbye!"
    exit 130  # Standard exit code for SIGINT
}

# Trap SIGINT (Ctrl+C) and SIGTERM
trap cleanup SIGINT SIGTERM

# Get the directory where this script is located
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Create installation marker (for curl installer detection)
touch ".ainews_installed"
export AINEWS_INSTALLED="$SCRIPT_DIR"

# =============================================================================
# CONFIGURATION
# =============================================================================

PY_SCRIPT="ainews.py"
SOURCES="sources.txt"
VERSION="0.8.1"

# Default settings
DEFAULT_TOP=30
DEFAULT_OTHER_MIN=10
DEFAULT_OTHER_MAX=20
DEFAULT_WORKERS=25

# =============================================================================
# COLORS & FORMATTING
# =============================================================================

# Detect terminal capabilities
if [ -t 1 ] && command -v tput &>/dev/null && [ "$(tput colors 2>/dev/null || echo 0)" -ge 8 ]; then
    BOLD=$(tput bold)
    RED=$(tput setaf 1)
    GREEN=$(tput setaf 2)
    YELLOW=$(tput setaf 3)
    BLUE=$(tput setaf 4)
    MAGENTA=$(tput setaf 5)
    CYAN=$(tput setaf 6)
    WHITE=$(tput setaf 7)
    NC=$(tput sgr0)
    HAS_COLOR=true
else
    BOLD="" RED="" GREEN="" YELLOW="" BLUE="" MAGENTA="" CYAN="" WHITE="" NC=""
    HAS_COLOR=false
fi

# =============================================================================
# TTY INPUT HANDLING
# =============================================================================
# When script is piped (curl ... | bash), stdin is the pipe, not the terminal.
# We read from /dev/tty directly to get user input in interactive mode.

# Check if /dev/tty is available
if [ -e /dev/tty ]; then
    TTY_AVAILABLE=true
else
    TTY_AVAILABLE=false
fi

# Read a single character from user (works even when piped)
read_char() {
    if [ "$TTY_AVAILABLE" = true ]; then
        read -n 1 -s -r "$@" </dev/tty
    else
        read -n 1 -s -r "$@"
    fi
}

# Read a line from user (works even when piped)
read_line() {
    if [ "$TTY_AVAILABLE" = true ]; then
        read -r "$@" </dev/tty
    else
        read -r "$@"
    fi
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

print_header() {
    clear
    echo "${BOLD}${BLUE}"
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║           📰 NEWS AGGREGATOR v${VERSION} - LAUNCHER           ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo "${NC}"
}

print_line() {
    echo "${BLUE}──────────────────────────────────────────────────────────${NC}"
}

info() { echo "${GREEN}✓${NC} $1"; }
warn() { echo "${YELLOW}⚠${NC} $1"; }
error() { echo "${RED}✗${NC} $1" >&2; }

wait_key() {
    echo ""
    echo -n "Press any key to continue..."
    read_char
    echo ""
}

# =============================================================================
# ENVIRONMENT SETUP
# =============================================================================

setup_environment() {
    # In Docker, skip venv/pip setup (already handled by Dockerfile)
    if [ "${AINEWS_IN_DOCKER:-0}" = "1" ]; then
        info "Running in Docker (environment ready)"
        return
    fi
    
    # Create virtual environment if it doesn't exist
    if [ ! -d ".venv" ]; then
        echo "📦 Creating virtual environment (first-time setup)..."
        python3 -m venv .venv
        info "Virtual environment created"
    fi

    # Activate virtual environment
    # shellcheck disable=SC1091
    source .venv/bin/activate

    # Install dependencies quietly
    echo "📦 Checking dependencies..."
    python -m pip install --upgrade pip wheel setuptools -q 2>/dev/null || true
    pip install -r requirements.txt -q 2>/dev/null || true
    info "Environment ready"
}

# =============================================================================
# RUN AGGREGATOR
# =============================================================================

run_aggregator() {
    local args="$1"
    echo ""
    print_line
    echo "🚀 ${BOLD}Starting News Aggregator...${NC}"
    print_line
    echo ""
    
    eval "python \"$PY_SCRIPT\" --sources \"$SOURCES\" $args"
    
    echo ""
    print_line
    info "Complete!"
    print_line
}

# =============================================================================
# MENUS
# =============================================================================

show_main_menu() {
    print_header
    echo "  ${BOLD}[1]${NC} 🚀 Run with Default Settings"
    echo "  ${BOLD}[2]${NC} 📋 Quick Presets"
    echo "  ${BOLD}[3]${NC} ⚙️  Custom Run (configure options)"
    echo "  ${BOLD}[4]${NC} 📅 Set Lookback Period"
    echo "  ${BOLD}[5]${NC} 💾 Manage Presets"
    echo "  ${BOLD}[6]${NC} 🤖 AI Settings & Digest"
    echo "  ${BOLD}[7]${NC} 🔧 Settings"
    echo "  ${BOLD}[8]${NC} ℹ️  Help / Documentation"
    echo "  ${BOLD}[0]${NC} ❌ Exit"
    echo ""
    print_line
    echo -n "Enter choice [0-8]: "
}

show_presets_menu() {
    print_header
    echo "  ${BOLD}${CYAN}📋 QUICK PRESETS${NC}"
    echo ""
    echo "  ${BOLD}[1]${NC} 🤖 AI/ML Focus        ${YELLOW}(48h, 25 articles)${NC}"
    echo "  ${BOLD}[2]${NC} 💹 Finance & Markets  ${YELLOW}(24h, 30 articles)${NC}"
    echo "  ${BOLD}[3]${NC} 🔐 Cybersecurity      ${YELLOW}(48h, 20 articles)${NC}"
    echo "  ${BOLD}[4]${NC} 🌍 World & Politics   ${YELLOW}(48h, 25 articles)${NC}"
    echo "  ${BOLD}[5]${NC} 📰 Full Coverage      ${YELLOW}(smart, 30 articles)${NC}"
    echo "  ${BOLD}[6]${NC} ⚡ Quick Update       ${YELLOW}(24h, 15 articles)${NC}"
    echo "  ${BOLD}[7]${NC} 📚 Deep Dive          ${YELLOW}(7 days, 50 articles)${NC}"
    
    # Check if spaCy is installed for precision mode
    local spacy_status=$(python -c "
from curation.precision import is_spacy_available
print('✓' if is_spacy_available() else '⚠️ requires install')
" 2>/dev/null || echo "⚠️ requires install")
    echo "  ${BOLD}[8]${NC} 🧠 Precision Mode     ${CYAN}(spaCy NER: ${spacy_status})${NC}"
    echo ""
    echo "  ${BOLD}[0]${NC} ← Back to Main Menu"
    echo ""
    print_line
    echo -n "Enter choice [0-8]: "
}

show_lookback_menu() {
    print_header
    echo "  ${BOLD}${CYAN}📅 SET LOOKBACK PERIOD${NC}"
    echo ""
    echo "  ${BOLD}[1]${NC} ⚡ Last 12 hours"
    echo "  ${BOLD}[2]${NC} 📅 Last 24 hours (1 day)"
    echo "  ${BOLD}[3]${NC} 📅 Last 48 hours (2 days)"
    echo "  ${BOLD}[4]${NC} 📅 Last 72 hours (3 days)"
    echo "  ${BOLD}[5]${NC} 📅 Last 7 days"
    echo "  ${BOLD}[6]${NC} 📅 Last 14 days"
    echo "  ${BOLD}[7]${NC} 📅 Last 30 days"
    echo "  ${BOLD}[8]${NC} 🔧 Custom hours..."
    echo ""
    echo "  ${BOLD}[0]${NC} ← Back to Main Menu"
    echo ""
    print_line
    echo -n "Enter choice [0-8]: "
}

# Category names and icons for checkbox display
CATEGORY_NAMES=(
    "ai_headlines:📰 AI/ML Headlines"
    "tools_platforms:🛠️ Tools & Platforms"
    "governance_safety:⚖️ Governance & Safety"
    "finance_markets:💹 Finance & Markets"
    "crypto_blockchain:₿ Crypto & Blockchain"
    "cybersecurity:🔐 Cybersecurity"
    "tech_industry:💻 Tech Industry"
    "politics_policy:🏛️ Politics & Policy"
    "world_news:🌍 World News"
    "viral_trending:🔥 Viral & Trending"
)

# Track selected categories (1=selected, 0=not)
declare -a SELECTED_CATS

init_category_selection() {
    SELECTED_CATS=()
    for i in "${!CATEGORY_NAMES[@]}"; do
        if [[ -z "$CUSTOM_CATEGORIES" ]]; then
            SELECTED_CATS[$i]=1  # All selected by default
        else
            local cat_key="${CATEGORY_NAMES[$i]%%:*}"
            if [[ "$CUSTOM_CATEGORIES" == *"$cat_key"* ]]; then
                SELECTED_CATS[$i]=1
            else
                SELECTED_CATS[$i]=0
            fi
        fi
    done
}

show_category_selector() {
    print_header
    echo "  ${BOLD}${CYAN}🏷️ SELECT CATEGORIES${NC}"
    echo ""
    echo "  Toggle categories on/off by entering their number."
    echo "  ${GREEN}[✓]${NC} = included, ${RED}[ ]${NC} = excluded"
    echo ""
    
    local all_selected=true
    for i in "${!CATEGORY_NAMES[@]}"; do
        local num=$((i + 1))
        local cat_display="${CATEGORY_NAMES[$i]#*:}"
        if [[ "${SELECTED_CATS[$i]}" == "1" ]]; then
            echo "  ${BOLD}[$num]${NC} ${GREEN}[✓]${NC} $cat_display"
        else
            echo "  ${BOLD}[$num]${NC} ${RED}[ ]${NC} $cat_display"
            all_selected=false
        fi
    done
    
    echo ""
    print_line
    echo ""
    if [[ "$all_selected" == true ]]; then
        echo "  ${BOLD}[A]${NC} ☐ Deselect All"
    else
        echo "  ${BOLD}[A]${NC} ☑ Select All"
    fi
    echo "  ${BOLD}[9]${NC} ✓ Done - Apply Selection"
    echo "  ${BOLD}[0]${NC} ✗ Cancel"
    echo ""
    print_line
    echo -n "Toggle category [1-10] or action [0/9/A]: "
}

show_custom_menu() {
    print_header
    echo "  ${BOLD}${CYAN}⚙️ CUSTOM RUN CONFIGURATION${NC}"
    echo ""
    echo "  Current settings:"
    echo "    Hours:      ${YELLOW}${CUSTOM_HOURS:-smart}${NC}"
    echo "    Articles:   ${YELLOW}${CUSTOM_TOP:-$DEFAULT_TOP}${NC} main + ${YELLOW}${CUSTOM_OTHER_MIN:-$DEFAULT_OTHER_MIN}-${CUSTOM_OTHER_MAX:-$DEFAULT_OTHER_MAX}${NC} other"
    echo "    Workers:    ${YELLOW}${CUSTOM_WORKERS:-$DEFAULT_WORKERS}${NC}"
    
    # Show categories nicely
    if [[ -z "$CUSTOM_CATEGORIES" ]]; then
        echo "    Categories: ${YELLOW}All (10)${NC}"
    else
        local count=$(echo "$CUSTOM_CATEGORIES" | tr ',' '\n' | wc -l)
        echo "    Categories: ${YELLOW}$count selected${NC}"
    fi
    echo ""
    print_line
    echo ""
    echo "  ${BOLD}[1]${NC} 📅 Set lookback period"
    echo "  ${BOLD}[2]${NC} 📊 Set article counts"
    echo "  ${BOLD}[3]${NC} ⚡ Set worker count"
    echo "  ${BOLD}[4]${NC} 🏷️  Select categories"
    echo ""
    echo "  ${BOLD}[5]${NC} 🚀 ${GREEN}Run with these settings${NC}"
    echo "  ${BOLD}[6]${NC} 💾 Show settings (for config/presets.json)"
    echo ""
    echo "  ${BOLD}[0]${NC} ← Back to Main Menu"
    echo ""
    print_line
    echo -n "Enter choice [0-6]: "
}

show_manage_presets_menu() {
    print_header
    echo "  ${BOLD}${CYAN}💾 MANAGE PRESETS${NC}"
    echo ""
    echo "  ${BOLD}[1]${NC} 📋 List all presets"
    echo "  ${BOLD}[2]${NC} ➕ Create new preset (via custom run)"
    echo "  ${BOLD}[3]${NC} 📝 Edit config/presets.json (opens file)"
    echo ""
    echo "  ${BOLD}[0]${NC} ← Back to Main Menu"
    echo ""
    print_line
    echo -n "Enter choice [0-3]: "
}

show_help() {
    print_header
    echo "  ${BOLD}${CYAN}ℹ️ HELP & DOCUMENTATION${NC}"
    echo ""
    echo "  ${BOLD}What is News Aggregator?${NC}"
    echo "  An intelligent system that curates news from 200+ sources"
    echo "  across 10 categories: AI, Finance, Crypto, Cybersecurity,"
    echo "  Tech, Politics, World News, and more."
    echo ""
    print_line
    echo ""
    echo "  ${BOLD}Quick Start:${NC}"
    echo "  • Option 1: Run with defaults for full coverage"
    echo "  • Option 2: Use a preset for focused news"
    echo "  • Option 3: Configure custom settings"
    echo ""
    echo "  ${BOLD}Files you can edit:${NC}"
    echo "  • ${CYAN}sources.txt${NC}  - Add/remove news sources"
    echo "  • ${CYAN}config/presets.json${NC} - Create/modify presets"
    echo ""
    echo "  ${BOLD}Command line usage:${NC}"
    echo "  ${YELLOW}./run_ainews.sh --preset ai_focus${NC}"
    echo "  ${YELLOW}./run_ainews.sh --hours 24 --top 20${NC}"
    echo "  ${YELLOW}python ainews.py --help${NC}"
    echo ""
    print_line
    wait_key
}

show_run_confirmation() {
    local hours="$1"
    echo ""
    print_line
    echo ""
    echo "  Lookback period set to: ${GREEN}${hours}${NC}"
    echo ""
    echo "  ${BOLD}[1]${NC} 🚀 Run now with this period"
    echo "  ${BOLD}[0]${NC} ← Back to Main Menu"
    echo ""
    print_line
    echo -n "Enter choice [0-1]: "
}

# =============================================================================
# AI SETTINGS MENU
# =============================================================================

show_ai_menu() {
    print_header
    echo "  ${BOLD}${CYAN}🤖 AI SETTINGS & DIGEST${NC}"
    echo ""
    echo "  ${BOLD}[1]${NC} 🔧 Configure AI Provider"
    echo "  ${BOLD}[2]${NC} 📝 Generate Daily Digest"
    echo "  ${BOLD}[3]${NC} 📝 Generate Weekly Digest"
    echo "  ${BOLD}[4]${NC} 📝 Generate Monthly Digest"
    echo "  ${BOLD}[5]${NC} 📊 Show AI Status"
    echo ""
    echo "  ${BOLD}[0]${NC} ← Back to Main Menu"
    echo ""
    print_line
    echo -n "Enter choice [0-5]: "
}

handle_ai_menu() {
    while true; do
        show_ai_menu
        read_line choice
        case $choice in
            1)
                handle_ai_config
                ;;
            2)
                handle_digest_choice "daily" 1
                ;;
            3)
                handle_digest_choice "weekly" 7
                ;;
            4)
                handle_digest_choice "monthly" 30
                ;;
            5)
                echo ""
                python "$PY_SCRIPT" --status
                wait_key
                ;;
            0) return ;;
            *) warn "Invalid choice. Please try again."; sleep 1 ;;
        esac
    done
}

# Handle digest choice with saved vs fresh option
handle_digest_choice() {
    local period="$1"
    local days="$2"
    
    echo ""
    print_line
    echo ""
    
    # Check for saved articles
    local article_count=$(python -c "
from data.models import get_recent_articles
articles = get_recent_articles(limit=500, days=$days)
print(len(articles))
" 2>/dev/null || echo "0")
    
    echo "  ${BOLD}${CYAN}📝 Generate ${period^} Digest${NC}"
    echo ""
    
    if [ "$article_count" -gt 0 ]; then
        echo "  ${GREEN}✓ Found $article_count saved articles${NC} (last $days days)"
        echo ""
        echo "  ${BOLD}[1]${NC} Use saved articles ${YELLOW}(quick)${NC}"
        echo "  ${BOLD}[2]${NC} Fetch fresh articles first ${YELLOW}(takes ~2 min)${NC}"
        echo "  ${BOLD}[0]${NC} ← Cancel"
        echo ""
        print_line
        echo -n "Enter choice [0-2]: "
        read_line digest_choice
        
        case $digest_choice in
            1)
                echo ""
                info "Generating $period digest from saved articles..."
                python "$PY_SCRIPT" --digest "$period"
                ;;
            2)
                echo ""
                info "Fetching fresh articles, then generating $period digest..."
                python "$PY_SCRIPT" --fetch-and-digest "$period"
                ;;
            0|*)
                return
                ;;
        esac
    else
        echo "  ${YELLOW}⚠ No saved articles found${NC}"
        echo ""
        echo "  ${BOLD}[1]${NC} Fetch fresh articles and generate digest"
        echo "  ${BOLD}[0]${NC} ← Cancel"
        echo ""
        print_line
        echo -n "Enter choice [0-1]: "
        read_line digest_choice
        
        case $digest_choice in
            1)
                echo ""
                info "Fetching fresh articles, then generating $period digest..."
                python "$PY_SCRIPT" --fetch-and-digest "$period"
                ;;
            0|*)
                return
                ;;
        esac
    fi
    
    wait_key
}

handle_ai_config() {
    print_header
    echo "  ${BOLD}${CYAN}🔧 CONFIGURE AI PROVIDER${NC}"
    echo ""
    echo "  ${BOLD}[1]${NC} Google Gemini ${YELLOW}(Recommended)${NC}"
    echo "  ${BOLD}[2]${NC} OpenAI"
    echo "  ${BOLD}[3]${NC} Anthropic Claude"
    echo "  ${BOLD}[4]${NC} Local LLM (Ollama)"
    echo ""
    echo "  ${BOLD}[0]${NC} ← Cancel"
    echo ""
    print_line
    echo -n "Select provider [0-4]: "
    read_line provider_choice
    
    case $provider_choice in
        1) PROVIDER="gemini"; DEFAULT_MODEL="gemini-2.5-flash"; DEFAULT_URL="https://generativelanguage.googleapis.com/v1beta" ;;
        2) PROVIDER="openai"; DEFAULT_MODEL="gpt-4o-mini"; DEFAULT_URL="" ;;
        3) PROVIDER="claude"; DEFAULT_MODEL="claude-3-haiku-20240307"; DEFAULT_URL="" ;;
        4) PROVIDER="local"; DEFAULT_MODEL="llama2"; DEFAULT_URL="http://localhost:11434" ;;
        0) return ;;
        *) warn "Invalid choice."; sleep 1; return ;;
    esac
    
    echo ""
    print_line
    echo ""
    echo "  ${BOLD}Enter API Key:${NC}"
    echo -n "  > "
    read_line API_KEY
    
    if [ -z "$API_KEY" ] && [ "$PROVIDER" != "local" ]; then
        error "API key required for $PROVIDER"
        wait_key
        return
    fi
    
    echo ""
    echo "  ${BOLD}API URL${NC} (press Enter for default: ${YELLOW}${DEFAULT_URL:-auto}${NC}):"
    echo -n "  > "
    read_line CUSTOM_URL
    [ -z "$CUSTOM_URL" ] && CUSTOM_URL="$DEFAULT_URL"
    
    echo ""
    echo "  ${BOLD}Model Name${NC} (press Enter for default: ${YELLOW}${DEFAULT_MODEL}${NC}):"
    echo -n "  > "
    read_line CUSTOM_MODEL
    [ -z "$CUSTOM_MODEL" ] && CUSTOM_MODEL="$DEFAULT_MODEL"
    
    # Save to .env file
    echo ""
    info "Saving configuration..."
    
    # Create or update .env file
    cat > .env << EOF
# AI Configuration - Generated by run_ainews.sh
AINEWS_API_KEY=$API_KEY
AINEWS_PROVIDER=$PROVIDER
AINEWS_MODEL=$CUSTOM_MODEL
AINEWS_ENDPOINT=$CUSTOM_URL
EOF
    
    # Set file permissions (owner only)
    chmod 600 .env
    
    # Update config/config.json
    python -c "
import json
from pathlib import Path

config_file = Path('config/config.json')
config = {}
if config_file.exists():
    try:
        config = json.loads(config_file.read_text())
    except:
        pass

config['ai'] = {
    'provider': '$PROVIDER',
    'model': '$CUSTOM_MODEL',
    'endpoint': '$CUSTOM_URL'
}
config_file.write_text(json.dumps(config, indent=2))
print('✓ Configuration saved')
"
    
    # Test connection
    echo ""
    echo "  Testing connection..."
    python -c "
import os
os.environ['AINEWS_API_KEY'] = '$API_KEY'
from ai.factory import create_provider
provider = create_provider('$PROVIDER', '$CUSTOM_MODEL')
if provider.test_connection():
    print('  ${GREEN}✓ Connection successful!${NC}')
else:
    print('  ${RED}✗ Connection failed - check credentials${NC}')
"
    
    wait_key
}

# =============================================================================
# SETTINGS MENU
# =============================================================================

show_settings_menu() {
    print_header
    echo "  ${BOLD}${CYAN}🔧 SETTINGS${NC}"
    echo ""
    
    # Read current settings
    local max_age=$(python -c "
from config.settings import get_settings
s = get_settings()
print(s.database.max_age_days)
" 2>/dev/null || echo "30")

    # Check if spaCy is installed
    local spacy_status=$(python -c "
from curation.precision import is_spacy_available
print('Installed ✓' if is_spacy_available() else 'Not installed')
" 2>/dev/null || echo "Not installed")
    
    echo "  ${BOLD}Current Settings:${NC}"
    echo "    Max article age: ${GREEN}${max_age} days${NC}"
    echo "    spaCy Precision: ${YELLOW}${spacy_status}${NC}"
    echo ""
    echo "  ${BOLD}[1]${NC} Change max article age"
    echo "  ${BOLD}[2]${NC} Clear all articles from database"
    echo "  ${BOLD}[3]${NC} Show database stats"
    echo "  ${BOLD}[4]${NC} 🧠 Install spaCy Precision Mode"
    echo ""
    echo "  ${BOLD}[0]${NC} ← Back to Main Menu"
    echo ""
    print_line
    echo -n "Enter choice [0-4]: "
}

handle_settings_menu() {
    while true; do
        show_settings_menu
        read_line choice
        case $choice in
            1)
                echo ""
                echo "  ${BOLD}Enter new max article age (days):${NC}"
                echo -n "  > "
                read_line new_age
                
                if [[ "$new_age" =~ ^[0-9]+$ ]] && [ "$new_age" -gt 0 ]; then
                    # Update config/config.json
                    python -c "
import json
from pathlib import Path

config_file = Path('config/config.json')
config = {}
if config_file.exists():
    try:
        config = json.loads(config_file.read_text())
    except:
        pass

if 'database' not in config:
    config['database'] = {}
config['database']['max_age_days'] = $new_age
config_file.write_text(json.dumps(config, indent=2))
print('✓ Max article age set to $new_age days')
"
                else
                    warn "Invalid input. Please enter a positive number."
                fi
                wait_key
                ;;
            2)
                echo ""
                warn "This will delete ALL articles from the database!"
                echo -n "  Are you sure? [y/N]: "
                read_line confirm
                if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
                    python -c "
from data.models import delete_old_articles
deleted = delete_old_articles(0)  # Delete all
print(f'🗑️ Deleted {deleted} articles')
"
                else
                    info "Cancelled."
                fi
                wait_key
                ;;
            3)
                echo ""
                python "$PY_SCRIPT" --status
                wait_key
                ;;
            4)
                handle_spacy_install
                ;;
            0) return ;;
            *) warn "Invalid choice. Please try again."; sleep 1 ;;
        esac
    done
}

# Handle spaCy installation
handle_spacy_install() {
    echo ""
    print_line
    echo ""
    echo "  ${BOLD}${CYAN}🧠 spaCy Precision Mode${NC}"
    echo ""
    
    # Check if already installed
    local is_installed=$(python -c "
from curation.precision import is_spacy_available
print('yes' if is_spacy_available() else 'no')
" 2>/dev/null || echo "no")
    
    if [ "$is_installed" = "yes" ]; then
        echo "  ${GREEN}✓ spaCy is already installed!${NC}"
        echo ""
        echo "  Use the '${BOLD}precision${NC}' preset to enable enhanced classification."
        echo "  Example: python ainews.py --preset precision"
        wait_key
        return
    fi
    
    echo "  ${YELLOW}# Package installation required on first use${NC}"
    echo ""
    echo "  spaCy provides enhanced entity recognition for better"
    echo "  classification of AI companies, financial terms, etc."
    echo ""
    echo "  ${BOLD}This will install:${NC}"
    echo "    - spaCy (~50MB)"
    echo "    - en_core_web_sm model (~15MB)"
    echo ""
    echo -n "  Do you want to proceed? [y/N]: "
    read_line confirm
    
    if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
        echo ""
        info "Installing spaCy..."
        python -c "
from curation.precision import install_spacy
if install_spacy():
    print('✓ spaCy installed successfully!')
    print('  Use --preset precision to enable enhanced mode.')
else:
    print('✗ Installation failed. Try manually:')
    print('  pip install spacy')
    print('  python -m spacy download en_core_web_sm')
"
    else
        info "Installation cancelled."
    fi
    
    wait_key
}

# =============================================================================
# MENU HANDLERS
# =============================================================================

handle_presets_menu() {
    while true; do
        show_presets_menu
        read_line choice
        case $choice in
            1) run_aggregator "--preset ai_focus"; wait_key ;;
            2) run_aggregator "--preset finance"; wait_key ;;
            3) run_aggregator "--preset cybersecurity"; wait_key ;;
            4) run_aggregator "--preset world"; wait_key ;;
            5) run_aggregator "--preset default"; wait_key ;;
            6) run_aggregator "--preset quick_update"; wait_key ;;
            7) run_aggregator "--preset deep_dive"; wait_key ;;
            8) handle_precision_mode ;;
            0) return ;;
            *) warn "Invalid choice. Please try again."; sleep 1 ;;
        esac
    done
}

# Handle precision mode with spaCy install check
handle_precision_mode() {
    # Check if spaCy is installed
    local is_installed=$(python -c "
from curation.precision import is_spacy_available
print('yes' if is_spacy_available() else 'no')
" 2>/dev/null || echo "no")
    
    if [ "$is_installed" = "yes" ]; then
        # spaCy is ready, run precision mode
        info "Running with Precision Mode (spaCy NER enabled)..."
        run_aggregator "--preset precision"
        wait_key
    else
        # Need to install spaCy first
        echo ""
        print_line
        echo ""
        echo "  ${BOLD}${CYAN}🧠 Precision Mode${NC}"
        echo ""
        echo "  ${YELLOW}# Package installation required on first use${NC}"
        echo ""
        echo "  Precision mode uses spaCy NER for enhanced entity recognition."
        echo "  This improves classification of AI companies, financial entities, etc."
        echo ""
        echo "  ${BOLD}This will install:${NC}"
        echo "    - spaCy library (~50MB)"
        echo "    - en_core_web_sm model (~15MB)"
        echo ""
        echo -n "  Install and run Precision Mode? [y/N]: "
        read_line confirm
        
        if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
            echo ""
            info "Installing spaCy..."
            
            local install_result=$(python -c "
from curation.precision import install_spacy
if install_spacy():
    print('success')
else:
    print('failed')
" 2>&1)
            
            if [[ "$install_result" == *"success"* ]]; then
                success "spaCy installed successfully!"
                echo ""
                info "Running with Precision Mode..."
                run_aggregator "--preset precision"
            else
                error "Installation failed. Try manually:"
                echo "    pip install spacy"
                echo "    python -m spacy download en_core_web_sm"
            fi
            wait_key
        else
            info "Cancelled. You can install spaCy later from Settings menu [7]."
            wait_key
        fi
    fi
}

handle_lookback_menu() {
    local selected_hours=""
    
    while true; do
        show_lookback_menu
        read_line choice
        case $choice in
            1) selected_hours="12" ;;
            2) selected_hours="24" ;;
            3) selected_hours="48" ;;
            4) selected_hours="72" ;;
            5) selected_hours="168" ;;
            6) selected_hours="336" ;;
            7) selected_hours="720" ;;
            8)
                echo ""
                echo -n "Enter hours (1-720): "
                read_line hours
                if [[ "$hours" =~ ^[0-9]+$ ]] && [ "$hours" -ge 1 ] && [ "$hours" -le 720 ]; then
                    selected_hours="$hours"
                else
                    error "Invalid hours. Please enter a number between 1 and 720."
                    sleep 2
                    continue
                fi
                ;;
            0) return ;;
            *) warn "Invalid choice. Please try again."; sleep 1; continue ;;
        esac
        
        # Show confirmation if hours were selected
        if [[ -n "$selected_hours" ]]; then
            show_run_confirmation "${selected_hours} hours"
            read_line confirm
            case $confirm in
                1)
                    run_aggregator "--hours $selected_hours"
                    wait_key
                    return
                    ;;
                0) return ;;
                *) return ;;
            esac
        fi
    done
}

handle_category_selector() {
    init_category_selection
    
    while true; do
        show_category_selector
        read_line choice
        
        case $choice in
            [1-9]|10)
                local idx=$((choice - 1))
                if [[ $idx -lt ${#CATEGORY_NAMES[@]} ]]; then
                    if [[ "${SELECTED_CATS[$idx]}" == "1" ]]; then
                        SELECTED_CATS[$idx]=0
                    else
                        SELECTED_CATS[$idx]=1
                    fi
                fi
                ;;
            [Aa])
                # Toggle all
                local all_selected=true
                for i in "${!SELECTED_CATS[@]}"; do
                    if [[ "${SELECTED_CATS[$i]}" == "0" ]]; then
                        all_selected=false
                        break
                    fi
                done
                
                if [[ "$all_selected" == true ]]; then
                    # Deselect all
                    for i in "${!SELECTED_CATS[@]}"; do
                        SELECTED_CATS[$i]=0
                    done
                else
                    # Select all
                    for i in "${!SELECTED_CATS[@]}"; do
                        SELECTED_CATS[$i]=1
                    done
                fi
                ;;
            9)
                # Done - build categories string
                local cats=""
                local all_selected=true
                for i in "${!CATEGORY_NAMES[@]}"; do
                    if [[ "${SELECTED_CATS[$i]}" == "1" ]]; then
                        local cat_key="${CATEGORY_NAMES[$i]%%:*}"
                        if [[ -n "$cats" ]]; then
                            cats="$cats,$cat_key"
                        else
                            cats="$cat_key"
                        fi
                    else
                        all_selected=false
                    fi
                done
                
                if [[ "$all_selected" == true ]]; then
                    CUSTOM_CATEGORIES=""  # All = empty (no filter)
                else
                    CUSTOM_CATEGORIES="$cats"
                fi
                return
                ;;
            0)
                return
                ;;
            *)
                warn "Invalid choice."
                sleep 1
                ;;
        esac
    done
}

handle_custom_menu() {
    # Initialize custom settings
    CUSTOM_HOURS=""
    CUSTOM_TOP="$DEFAULT_TOP"
    CUSTOM_OTHER_MIN="$DEFAULT_OTHER_MIN"
    CUSTOM_OTHER_MAX="$DEFAULT_OTHER_MAX"
    CUSTOM_WORKERS="$DEFAULT_WORKERS"
    CUSTOM_CATEGORIES=""
    
    while true; do
        show_custom_menu
        read_line choice
        case $choice in
            1)
                # Lookback period - show quick options
                echo ""
                echo "  Quick options: 1=12h, 2=24h, 3=48h, 4=72h, 5=7days, 6=smart"
                echo -n "  Enter choice or hours (1-720): "
                read_line hours_input
                case $hours_input in
                    1) CUSTOM_HOURS="12" ;;
                    2) CUSTOM_HOURS="24" ;;
                    3) CUSTOM_HOURS="48" ;;
                    4) CUSTOM_HOURS="72" ;;
                    5) CUSTOM_HOURS="168" ;;
                    6) CUSTOM_HOURS="" ;;
                    *)
                        if [[ "$hours_input" =~ ^[0-9]+$ ]] && [ "$hours_input" -ge 1 ] && [ "$hours_input" -le 720 ]; then
                            CUSTOM_HOURS="$hours_input"
                        else
                            error "Invalid input."
                            sleep 1
                        fi
                        ;;
                esac
                ;;
            2)
                echo ""
                echo "  Quick options: 1=15, 2=20, 3=30, 4=40, 5=50"
                echo -n "  Main articles count [1-5 or number]: "
                read_line top_input
                case $top_input in
                    1) CUSTOM_TOP="15" ;;
                    2) CUSTOM_TOP="20" ;;
                    3) CUSTOM_TOP="30" ;;
                    4) CUSTOM_TOP="40" ;;
                    5) CUSTOM_TOP="50" ;;
                    *)
                        if [[ "$top_input" =~ ^[0-9]+$ ]]; then
                            CUSTOM_TOP="$top_input"
                        fi
                        ;;
                esac
                ;;
            3)
                echo ""
                echo "  Quick options: 1=10, 2=15, 3=25, 4=35, 5=50"
                echo -n "  Worker count [1-5 or number]: "
                read_line worker_input
                case $worker_input in
                    1) CUSTOM_WORKERS="10" ;;
                    2) CUSTOM_WORKERS="15" ;;
                    3) CUSTOM_WORKERS="25" ;;
                    4) CUSTOM_WORKERS="35" ;;
                    5) CUSTOM_WORKERS="50" ;;
                    *)
                        if [[ "$worker_input" =~ ^[0-9]+$ ]] && [ "$worker_input" -ge 1 ] && [ "$worker_input" -le 50 ]; then
                            CUSTOM_WORKERS="$worker_input"
                        else
                            error "Invalid worker count."
                            sleep 1
                        fi
                        ;;
                esac
                ;;
            4)
                handle_category_selector
                ;;
            5)
                # Run
                local args="--top $CUSTOM_TOP --other-min $CUSTOM_OTHER_MIN --other-max $CUSTOM_OTHER_MAX --workers $CUSTOM_WORKERS"
                if [[ -n "$CUSTOM_HOURS" ]]; then
                    args="$args --hours $CUSTOM_HOURS"
                fi
                if [[ -n "$CUSTOM_CATEGORIES" ]]; then
                    args="$args --categories $CUSTOM_CATEGORIES"
                fi
                run_aggregator "$args"
                wait_key
                ;;
            6)
                # Show settings for copy/paste
                echo ""
                print_line
                echo "  ${BOLD}Copy these to config/presets.json:${NC}"
                echo ""
                echo "  \"my_preset\": {"
                echo "      \"name\": \"My Custom Preset\","
                echo "      \"description\": \"Custom configuration\","
                if [[ -n "$CUSTOM_HOURS" ]]; then
                    echo "      \"hours\": $CUSTOM_HOURS,"
                else
                    echo "      \"hours\": null,"
                fi
                echo "      \"top_articles\": $CUSTOM_TOP,"
                echo "      \"other_min\": $CUSTOM_OTHER_MIN,"
                echo "      \"other_max\": $CUSTOM_OTHER_MAX,"
                echo "      \"workers\": $CUSTOM_WORKERS,"
                if [[ -n "$CUSTOM_CATEGORIES" ]]; then
                    # Format categories as array
                    local cats_json=$(echo "$CUSTOM_CATEGORIES" | sed 's/,/", "/g')
                    echo "      \"categories\": [\"$cats_json\"]"
                else
                    echo "      \"categories\": [\"all\"]"
                fi
                echo "  }"
                echo ""
                print_line
                wait_key
                ;;
            0) return ;;
            *) warn "Invalid choice. Please try again."; sleep 1 ;;
        esac
    done
}

handle_manage_presets() {
    while true; do
        show_manage_presets_menu
        read_line choice
        case $choice in
            1)
                echo ""
                python "$PY_SCRIPT" --list-presets
                wait_key
                ;;
            2)
                handle_custom_menu
                ;;
            3)
                echo ""
                info "Opening config/presets.json..."
                if command -v code &>/dev/null; then
                    code config/presets.json
                elif command -v nano &>/dev/null; then
                    nano config/presets.json
                elif command -v vim &>/dev/null; then
                    vim config/presets.json
                else
                    echo "Please edit config/presets.json with your preferred editor."
                fi
                wait_key
                ;;
            0) return ;;
            *) warn "Invalid choice. Please try again."; sleep 1 ;;
        esac
    done
}

# =============================================================================
# MAIN MENU LOOP
# =============================================================================

main_menu_loop() {
    while true; do
        show_main_menu
        read_line choice
        case $choice in
            1)
                run_aggregator "--top $DEFAULT_TOP --other-min $DEFAULT_OTHER_MIN --other-max $DEFAULT_OTHER_MAX --workers $DEFAULT_WORKERS"
                wait_key
                ;;
            2) handle_presets_menu ;;
            3) handle_custom_menu ;;
            4) handle_lookback_menu ;;
            5) handle_manage_presets ;;
            6) handle_ai_menu ;;
            7) handle_settings_menu ;;
            8) show_help ;;
            0)
                echo ""
                info "Goodbye!"
                exit 0
                ;;
            *)
                warn "Invalid choice. Please enter 0-8."
                sleep 1
                ;;
        esac
    done
}

# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

# Parse arguments
FORCE_MENU=false
REMAINING_ARGS=()

for arg in "$@"; do
    case "$arg" in
        --menu)
            FORCE_MENU=true
            ;;
        --help|-h|--list-presets)
            # Pass through to Python directly
            setup_environment
            python "$PY_SCRIPT" "$@"
            exit $?
            ;;
        *)
            REMAINING_ARGS+=("$arg")
            ;;
    esac
done

# If we have arguments (and not forcing menu), run directly
if [ ${#REMAINING_ARGS[@]} -gt 0 ] && [ "$FORCE_MENU" = false ]; then
    echo "📰 News Aggregator v${VERSION}"
    echo "========================================"
    setup_environment
    echo ""
    run_aggregator "${REMAINING_ARGS[*]}"
    echo ""
    echo "TIP: Run ${CYAN}./run_ainews.sh${NC} for interactive menu"
    exit 0
fi

# If forced menu mode, skip stdin check
if [ "$FORCE_MENU" = true ]; then
    setup_environment
    main_menu_loop
    exit 0
fi

# Check if we can show interactive menu
# Even when piped (curl | bash), we can use /dev/tty for interaction
if [ "$TTY_AVAILABLE" = false ]; then
    # No TTY available - truly non-interactive (e.g., cron, no terminal)
    echo "📰 News Aggregator v${VERSION}"
    echo "========================================"
    echo ""
    echo "ℹ️  No terminal available - running with defaults"
    echo ""
    setup_environment
    run_aggregator "--top $DEFAULT_TOP --other-min $DEFAULT_OTHER_MIN --other-max $DEFAULT_OTHER_MAX --workers $DEFAULT_WORKERS"
    exit 0
fi

# Interactive mode - TTY is available (works even when piped via curl)
setup_environment
main_menu_loop
