#!/bin/bash
# docker_entrypoint.sh - Docker entry point with volume support
# v0.8.0
# This script sets up the Docker environment for ainews:
# - Creates output directories
# - Sets environment variables for paths
# - Runs the main workflow or interactive menu
# - Prints the output path for easy access
# - Attempts best-effort auto-open on host
#
# USAGE:
#   docker run ... ainews                    # One-shot run (default preset)
#   docker run ... ainews --menu             # Interactive menu
#   docker run ... ainews --preset ai_focus  # Custom preset
#

set -e

# Ensure output directories exist
mkdir -p /out /data

# Set env vars for ainews.py (these override defaults when set)
export AINEWS_OUT_DIR="/out"
export AINEWS_DB_PATH="/data/ainews.db"
export AINEWS_LAST_RUN="/data/last_ran_date.txt"
export AINEWS_IN_DOCKER="1"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🐳 News Aggregator (Docker)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check for --menu flag
if [ "$1" = "--menu" ]; then
    shift  # Remove --menu from args
    echo "📋 Launching interactive menu..."
    echo ""
    exec ./run_ainews.sh "$@"
fi

# Default args if none provided
if [ $# -eq 0 ]; then
    set -- --preset default --hours 6 --top 30
fi

# Run the main workflow
python ainews.py "$@"
EXIT_CODE=$?

# Find the most recent generated HTML file
HTML_FILE=$(ls -t /out/ainews_*.html 2>/dev/null | head -1)

if [ -n "$HTML_FILE" ]; then
    FILENAME=$(basename "$HTML_FILE")
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📄 OPEN THIS FILE: ./out/$FILENAME"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    # Best-effort auto-open (only works if host commands available via WSL interop)
    # These commands are available in Docker Desktop on WSL/Windows
    if command -v explorer.exe &>/dev/null; then
        # WSL with Windows interop
        explorer.exe "out\\$FILENAME" 2>/dev/null || true
    elif command -v /mnt/c/Windows/explorer.exe &>/dev/null; then
        # Alternative WSL path
        /mnt/c/Windows/explorer.exe "out\\$FILENAME" 2>/dev/null || true
    fi
    # Note: macOS and Linux auto-open from container is not possible
    # The user should open ./out/$FILENAME manually on host
fi

exit $EXIT_CODE
