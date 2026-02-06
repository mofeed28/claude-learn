#!/bin/bash
# claude-learn installer
# Copies /learn commands to your ~/.claude/commands directory

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

echo "  Installed:"
echo "    /learn        -> $COMMANDS_DIR/learn.md"
echo "    /learn-update -> $COMMANDS_DIR/learn-update.md"
echo "    /learn-list   -> $COMMANDS_DIR/learn-list.md"
echo ""
echo "  Restart Claude Code, then try:"
echo "    /learn stripe"
echo "    /learn react:hooks"
echo "    /learn ./path/to/api-spec.yaml"
echo ""
echo "  Done!"
echo ""
