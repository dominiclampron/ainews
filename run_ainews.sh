#!/usr/bin/env bash
# =============================================================================
# News Aggregator v0.2 - Launcher Script
# =============================================================================
# This script sets up the environment and runs the news aggregator.
# It handles virtual environment creation, dependency installation, and execution.
#
# USAGE:
#   ./run_ainews.sh                    # Run with default settings
#   ./run_ainews.sh --preset ai_focus  # Use AI/ML preset
#   ./run_ainews.sh --list-presets     # Show available presets
#   ./run_ainews.sh --help             # Show all options
#
# WHAT IT DOES:
#   1. Creates a Python virtual environment (if not exists)
#   2. Installs required Python packages
#   3. Runs the news aggregator with your settings
#   4. Opens the generated report in your browser
#
# =============================================================================

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Get the directory where this script is located
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Create installation marker (for curl installer detection)
touch ".ainews_installed"

# Export environment variable for detection
export AINEWS_INSTALLED="$SCRIPT_DIR"

# =============================================================================
# CONFIGURATION - You can customize these values
# =============================================================================

# Main Python script (don't change unless you rename it)
PY_SCRIPT="ainews.py"

# Sources file containing RSS feed URLs
# Edit sources.txt to add/remove news sources
SOURCES="sources.txt"

# -----------------------------------------------------------------------------
# DEFAULT AGGREGATOR SETTINGS (used when no --preset is specified)
# These can be overridden via command line: ./run_ainews.sh --top 40
# -----------------------------------------------------------------------------

# Number of main articles to include (default: 30)
# Higher = more articles, longer report
DEFAULT_TOP_ARTICLES=30

# Range for "Other Interesting" section (10-20 additional articles)
DEFAULT_OTHER_MIN=10
DEFAULT_OTHER_MAX=20

# Number of parallel workers for fetching (default: 25)
# Higher = faster but uses more bandwidth/connections
# Lower if you experience connection issues
DEFAULT_WORKERS=25

# =============================================================================
# SCRIPT EXECUTION - Generally don't modify below this line
# =============================================================================

# Check if help or list-presets is requested (pass through to Python)
for arg in "$@"; do
    if [[ "$arg" == "--help" || "$arg" == "-h" || "$arg" == "--list-presets" ]]; then
        # Ensure venv exists for these commands too
        if [ ! -d ".venv" ]; then
            python3 -m venv .venv
        fi
        source .venv/bin/activate
        pip install -q -r requirements.txt 2>/dev/null || true
        python "$PY_SCRIPT" "$@"
        exit $?
    fi
done

echo "📰 News Aggregator v0.2 - Launcher"
echo "========================================"
echo "📁 Working directory: $SCRIPT_DIR"
echo ""

# Step 1: Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment (first-time setup)..."
    python3 -m venv .venv
    echo "✓ Virtual environment created"
fi

# Step 2: Activate virtual environment
# shellcheck disable=SC1091
source .venv/bin/activate
echo "✓ Virtual environment activated"

# Step 3: Install/upgrade dependencies
echo "📦 Checking dependencies..."
python -m pip install --upgrade pip wheel setuptools -q
pip install -r requirements.txt -q
echo "✓ Dependencies OK"

# Step 4: Build the command with settings
# If no arguments provided, use defaults. Otherwise pass through to Python.
if [ $# -eq 0 ]; then
    # No arguments - use defaults
    CMD="python \"$PY_SCRIPT\" --sources \"$SOURCES\""
    CMD="$CMD --top $DEFAULT_TOP_ARTICLES"
    CMD="$CMD --other-min $DEFAULT_OTHER_MIN --other-max $DEFAULT_OTHER_MAX"
    CMD="$CMD --workers $DEFAULT_WORKERS"
    echo "⚙️ Using default settings (30 articles, smart lookback)"
else
    # Arguments provided - pass them through to Python directly
    CMD="python \"$PY_SCRIPT\" --sources \"$SOURCES\" $*"
    echo "⚙️ Using custom settings: $*"
fi

# Step 5: Run the aggregator
echo ""
echo "🚀 Starting aggregator..."
echo "========================================"
eval "$CMD"

echo ""
echo "========================================"
echo "✅ Complete!"
echo ""
echo "TIPS:"
echo "  • Run with --list-presets to see all available presets"
echo ""
echo "AVAILABLE PRESETS:"
echo "  --preset default        Full coverage, smart lookback"
echo "  --preset ai_focus       AI/ML headlines (48h, 25 articles)"
echo "  --preset finance        Finance & Crypto (24h, 30 articles)"
echo "  --preset cybersecurity  Security news (48h, 20 articles)"
echo "  --preset world          World & Politics (48h, 25 articles)"
echo "  --preset quick_update   Fast summary (24h, 15 articles)"
echo "  --preset deep_dive      Full week (168h, 50 articles)"
echo ""
echo "CUSTOMIZATION:"
echo "  • Edit sources.txt to add/remove news sources"
echo "  • Edit presets.json to customize or add presets"
