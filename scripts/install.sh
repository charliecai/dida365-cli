#!/usr/bin/env bash
# Install dida CLI and /ticktick skill for Claude Code.
#
# Usage:
#   ./scripts/install.sh
#
# What it does:
#   1. Install dida CLI via uv (editable mode)
#   2. Symlink skill/ticktick/ -> ~/.claude/skills/ticktick/

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SKILL_SRC="$PROJECT_DIR/skill/ticktick"
SKILL_DST="$HOME/.claude/skills/ticktick"

echo "==> Installing dida CLI..."
cd "$PROJECT_DIR"
uv pip install -e .
echo "    dida CLI installed."

echo "==> Setting up /ticktick skill..."
mkdir -p "$HOME/.claude/skills"

if [ -L "$SKILL_DST" ]; then
    echo "    Removing existing symlink: $SKILL_DST"
    rm "$SKILL_DST"
elif [ -d "$SKILL_DST" ]; then
    echo "    Warning: $SKILL_DST exists as a directory, backing up to ${SKILL_DST}.bak"
    mv "$SKILL_DST" "${SKILL_DST}.bak"
fi

ln -s "$SKILL_SRC" "$SKILL_DST"
echo "    Symlinked: $SKILL_DST -> $SKILL_SRC"

echo ""
echo "Done! To get started:"
echo "  1. Run 'dida auth login' to authenticate with Dida365"
echo "  2. Use '/ticktick' in Claude Code to manage tasks"
