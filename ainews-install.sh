#!/usr/bin/env bash
# =============================================================================
# News Aggregator - One-Line Installer & Launcher
# =============================================================================
# USAGE:
#   curl -fsSL https://github.com/dominiclampron/ainews/releases/latest/download/ainews-install.sh | bash
#
# WITH OPTIONS:
#   curl -fsSL ... | bash -s -- --preset ai_focus     # Use a preset
#   curl -fsSL ... | bash -s -- --update              # Update to latest version
#   curl -fsSL ... | bash -s -- --list-presets        # Show all presets
#
# AVAILABLE PRESETS:
#   default        - Full coverage, smart lookback (30 articles)
#   ai_focus       - AI/ML headlines only (48h, 25 articles)
#   finance        - Finance & Crypto (24h, 30 articles)
#   cybersecurity  - Security news (48h, 20 articles)
#   world          - World & Politics (48h, 25 articles)
#   quick_update   - Fast summary (24h, 15 articles)
#   deep_dive      - Full week comprehensive (168h, 50 articles)
#
# WHAT IT DOES:
#   1. Checks for required dependencies (git, python3)
#   2. Clones the repository (first run) or uses existing install
#   3. Optionally updates to latest version (with --update flag)
#   4. Runs the news aggregator
# =============================================================================

set -euo pipefail

# =============================================================================
# CONFIGURATION
# =============================================================================

REPO_URL="https://github.com/dominiclampron/ainews.git"
INSTALL_DIR="${AINEWS_HOME:-$HOME/ainews}"
MARKER_FILE=".ainews_installed"
VERSION="0.3"

# =============================================================================
# COLORS (auto-disable if not a terminal)
# =============================================================================

if [ -t 1 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    BOLD='\033[1m'
    NC='\033[0m'
else
    RED='' GREEN='' YELLOW='' BLUE='' BOLD='' NC=''
fi

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

info() { echo -e "${GREEN}✓${NC} $1"; }
warn() { echo -e "${YELLOW}⚠${NC} $1"; }
error() { echo -e "${RED}✗${NC} $1" >&2; }
header() { echo -e "\n${BOLD}${BLUE}$1${NC}"; }

check_command() {
    if ! command -v "$1" &> /dev/null; then
        error "$1 is required but not installed."
        echo "  Please install $1 and try again."
        exit 1
    fi
}

# =============================================================================
# PARSE ARGUMENTS - Extract --update flag, pass rest to launcher
# =============================================================================

DO_UPDATE=false
LAUNCHER_ARGS=()

for arg in "$@"; do
    if [[ "$arg" == "--update" ]]; then
        DO_UPDATE=true
    else
        LAUNCHER_ARGS+=("$arg")
    fi
done

# =============================================================================
# MAIN INSTALLATION LOGIC
# =============================================================================

echo ""
echo -e "${BOLD}📰 News Aggregator v${VERSION} - Installer${NC}"
echo "============================================"

# Check dependencies
header "Checking dependencies..."
check_command git
info "git found"
check_command python3
info "python3 found"

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 9 ]; }; then
    error "Python 3.9+ required, found $PYTHON_VERSION"
    exit 1
fi
info "Python $PYTHON_VERSION OK"

# Install or update
header "Setting up News Aggregator..."

if [ -d "$INSTALL_DIR" ] && [ -f "$INSTALL_DIR/$MARKER_FILE" ]; then
    info "Existing installation found at $INSTALL_DIR"
    cd "$INSTALL_DIR"
    
    # Only update if --update flag was passed
    if [ "$DO_UPDATE" = true ]; then
        echo "  Updating to latest version..."
        if git pull --quiet origin main 2>/dev/null; then
            info "Updated to latest version"
        else
            warn "Could not update (offline?), continuing with current version..."
        fi
    else
        info "Using current version (use --update to check for updates)"
    fi
else
    if [ -d "$INSTALL_DIR" ]; then
        warn "Directory exists but not a valid installation"
        echo "  Backing up to ${INSTALL_DIR}.backup"
        mv "$INSTALL_DIR" "${INSTALL_DIR}.backup.$(date +%s)"
    fi
    
    echo "  Installing to $INSTALL_DIR..."
    git clone --depth 1 "$REPO_URL" "$INSTALL_DIR"
    
    # Create marker file with installation metadata
    cat > "$INSTALL_DIR/$MARKER_FILE" << EOF
installed_at=$(date '+%Y-%m-%dT%H:%M:%S%z')
installed_by=ainews-install.sh
version=$VERSION
EOF
    
    info "Installation complete"
fi

# Export environment variable for launcher detection
export AINEWS_INSTALLED="$INSTALL_DIR"

# Make launcher executable
cd "$INSTALL_DIR"
chmod +x run_ainews.sh

# Run the launcher with remaining arguments (excluding --update)
header "Launching News Aggregator..."
echo ""
exec ./run_ainews.sh "${LAUNCHER_ARGS[@]}"
