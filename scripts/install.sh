#!/usr/bin/env bash
# Install dida CLI and /dida365 skill for Claude Code.
#
# Usage:
#   ./scripts/install.sh
#
# What it does:
#   1. Install dida CLI via uv (editable mode)
#   2. Symlink skill/dida365/ -> ~/.claude/skills/dida365/

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SKILL_SRC="$PROJECT_DIR/skill/dida365"
SKILL_DST="$HOME/.claude/skills/dida365"
INSTALL_MODE="tool"

for arg in "$@"; do
    case "$arg" in
        --system|--tool)
            INSTALL_MODE="tool"
            ;;
        --editable)
            INSTALL_MODE="editable"
            ;;
        -h|--help)
            echo "Usage: ./scripts/install.sh [--tool|--system|--editable]"
            echo "  --tool/--system  Install global dida command via uv tool (default)"
            echo "  --editable       Install in current Python environment via uv pip -e ."
            exit 0
            ;;
        *)
            echo "Unknown option: $arg"
            echo "Run './scripts/install.sh --help' for usage."
            exit 1
            ;;
    esac
done

echo "==> Installing dida CLI..."
cd "$PROJECT_DIR"
if [ "$INSTALL_MODE" = "tool" ]; then
    uv tool install --from "$PROJECT_DIR" dida --force
else
    uv pip install -e .
fi
echo "    dida CLI installed."

echo "==> Setting up /dida365 skill..."
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
echo "  2. Use '/dida365' in Claude Code to manage tasks"
if [ "$INSTALL_MODE" = "tool" ]; then
    if ! command -v dida >/dev/null 2>&1; then
        echo ""
        echo "Note: dida is not in PATH yet."
        echo 'Add this to ~/.zshrc and reopen terminal: export PATH="$HOME/.local/bin:$PATH"'
    fi
fi
