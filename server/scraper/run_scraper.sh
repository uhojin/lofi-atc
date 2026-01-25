#!/bin/bash
# Convenience script to run the scraper

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment
if [ ! -d ".venv" ]; then
    echo "Virtual environment not found. Creating..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements-playwright.txt
    playwright install chromium
else
    source .venv/bin/activate
fi

# Run scraper with provided arguments
python top_feeds_playwright.py "$@"
