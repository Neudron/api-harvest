#!/usr/bin/env bash
set -euo pipefail

# Require Python 3.11+
if ! command -v python3 &>/dev/null; then
    echo "Error: python3 not found. Install Python 3.11 or later and re-run." >&2
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(sys.version_info.major * 100 + sys.version_info.minor)")
if [ "$PYTHON_VERSION" -lt 311 ]; then
    echo "Error: Python 3.11+ is required (found $(python3 --version))." >&2
    exit 1
fi

# Create venv on first run, reuse on subsequent runs
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

echo "Installing dependencies..."
pip install -e . -q

echo "Installing browser (Playwright Chromium)..."
playwright install chromium

mkdir -p ./harvest-chrome

echo ""
echo "Setup complete. Starting harvest..."
echo ""
exec harvest run --profile-dir ./harvest-chrome
