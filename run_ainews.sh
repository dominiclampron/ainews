#!/usr/bin/env bash
# =============================================================================
# News Aggregator v0.1 - Launcher Script
# =============================================================================
# This script sets up the environment and runs the news aggregator.
# It handles virtual environment creation, dependency installation, and execution.
#
# USAGE:
#   ./run_ainews.sh              # Run with default settings
#   chmod +x run_ainews.sh       # Make executable (first time only)
#
# WHAT IT DOES:
#   1. Creates a Python virtual environment (if not exists)
#   2. Installs required Python packages
#   3. Runs the news aggregator
#   4. Opens the generated report in your browser
#
# =============================================================================

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Get the directory where this script is located
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# =============================================================================
# CONFIGURATION - You can customize these values
# =============================================================================

# Main Python script (don't change unless you rename it)
PY_SCRIPT="ainews.py"

# Sources file containing RSS feed URLs
# Edit sources.txt to add/remove news sources
SOURCES="sources.txt"

# -----------------------------------------------------------------------------
# AGGREGATOR SETTINGS - Adjust these to change article selection
# -----------------------------------------------------------------------------

# Number of main articles to include (default: 30)
# Higher = more articles, longer report
TOP_ARTICLES=30

# Range for "Other Interesting" section (10-20 additional articles)
OTHER_MIN=10
OTHER_MAX=20

# Number of parallel workers for fetching (default: 25)
# Higher = faster but uses more bandwidth/connections
# Lower if you experience connection issues
WORKERS=25

# Override lookback period in hours (optional)
# Leave empty to use smart lookback from last_ran_date.txt
# Examples: 24 (last day), 48 (last 2 days), 168 (last week)
HOURS_OVERRIDE=""

# =============================================================================
# SCRIPT EXECUTION - Generally don't modify below this line
# =============================================================================

echo "📰 News Aggregator v0.1 - Launcher"
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
python -m pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "✓ Dependencies OK"

# Step 4: Build the command with settings
CMD="python \"$PY_SCRIPT\" --sources \"$SOURCES\""
CMD="$CMD --top $TOP_ARTICLES"
CMD="$CMD --other-min $OTHER_MIN --other-max $OTHER_MAX"
CMD="$CMD --workers $WORKERS"

# Add hours override if set
if [ -n "$HOURS_OVERRIDE" ]; then
    CMD="$CMD --hours $HOURS_OVERRIDE"
    echo "⏰ Using manual lookback: ${HOURS_OVERRIDE}h"
else
    echo "⏰ Using smart lookback from last_ran_date.txt"
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
echo "  • Edit sources.txt to add/remove news sources"
echo "  • Edit the CONFIGURATION section above to change defaults"
echo "  • Run with: ./run_ainews.sh"
