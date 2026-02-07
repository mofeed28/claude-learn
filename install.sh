#!/bin/bash
# claude-learn installer
# Copies /learn commands and optionally installs the Python scraper

set -e

COMMANDS_DIR="$HOME/.claude/commands"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SOURCE_DIR="$SCRIPT_DIR/commands"

echo ""
echo "  claude-learn installer"
echo "  ======================"
echo ""

# Create commands directory if it doesn't exist
if [ ! -d "$COMMANDS_DIR" ]; then
    mkdir -p "$COMMANDS_DIR"
    echo "  Created $COMMANDS_DIR"
fi

# Copy command files
cp "$SOURCE_DIR/learn.md" "$COMMANDS_DIR/learn.md"
cp "$SOURCE_DIR/learn-update.md" "$COMMANDS_DIR/learn-update.md"
cp "$SOURCE_DIR/learn-list.md" "$COMMANDS_DIR/learn-list.md"
cp "$SOURCE_DIR/learn-delete.md" "$COMMANDS_DIR/learn-delete.md"
cp "$SOURCE_DIR/learn-audit.md" "$COMMANDS_DIR/learn-audit.md"

echo "  Installed commands:"
echo "    /learn        -> $COMMANDS_DIR/learn.md"
echo "    /learn-update -> $COMMANDS_DIR/learn-update.md"
echo "    /learn-list   -> $COMMANDS_DIR/learn-list.md"
echo "    /learn-delete -> $COMMANDS_DIR/learn-delete.md"
echo "    /learn-audit  -> $COMMANDS_DIR/learn-audit.md"
echo ""

# Install Python scraper (optional but recommended)
SCRAPER_INSTALLED=false

if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    PYTHON=""
fi

if [ -n "$PYTHON" ]; then
    echo "  Python found: $($PYTHON --version 2>&1)"

    # Check if pip is available
    if $PYTHON -m pip --version &>/dev/null; then
        echo "  Installing runtime scraper..."
        if $PYTHON -m pip install -e "$SCRIPT_DIR" --quiet 2>/dev/null; then
            SCRAPER_INSTALLED=true
            echo "  Scraper installed successfully (pip install -e)"
        else
            # Try without editable mode (some environments don't support it)
            if $PYTHON -m pip install "$SCRIPT_DIR" --quiet 2>/dev/null; then
                SCRAPER_INSTALLED=true
                echo "  Scraper installed successfully (pip install)"
            else
                echo "  Warning: Could not install scraper via pip"
                echo "  You can install manually: pip install -e $SCRIPT_DIR"
            fi
        fi
    else
        echo "  Warning: pip not found. Scraper not installed."
        echo "  Install pip, then run: pip install -e $SCRIPT_DIR"
    fi
else
    echo "  Warning: Python not found. Scraper not installed."
    echo "  /learn will use Claude's built-in WebFetch/WebSearch (still works)."
fi

echo ""
if [ "$SCRAPER_INSTALLED" = true ]; then
    echo "  Setup complete (with scraper)"
    echo ""
    echo "  Verify scraper: $PYTHON -m scraper --help"
else
    echo "  Setup complete (commands only — scraper not installed)"
    echo "  /learn will use Claude's built-in tools for web scraping."
    echo "  For better results, install the scraper: pip install -e $SCRIPT_DIR"
fi

echo ""
echo "  Restart Claude Code, then try:"
echo "    /learn stripe"
echo "    /learn stripe --quick"
echo "    /learn react:hooks --lang typescript"
echo "    /learn https://github.com/honojs/hono"
echo "    /learn ./path/to/api-spec.yaml"
echo ""
echo "  Done!"
echo ""
