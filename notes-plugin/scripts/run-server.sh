#!/bin/sh
# Launcher for the notes MCP server.
#
# Claude Code runs this instead of a hard-coded python path, so the plugin
# works on any machine with python3. On first run it creates a private
# virtualenv under CLAUDE_PLUGIN_DATA (a per-user folder that survives plugin
# updates) and installs the `mcp` package there. Later runs reuse it.
#
# Rule for MCP stdio servers: stdout carries protocol messages only, so every
# bit of setup output goes to stderr.
set -eu

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
DATA_DIR="${CLAUDE_PLUGIN_DATA:-$HOME/.claude/plugins/data/notes-helper}"
VENV="$DATA_DIR/venv"

if [ ! -x "$VENV/bin/python" ]; then
  echo "[notes-helper] first run: creating virtualenv in $VENV" >&2
  mkdir -p "$DATA_DIR"
  python3 -m venv "$VENV" >&2
  "$VENV/bin/python" -m pip install --quiet --disable-pip-version-check "mcp>=2,<3" >&2
fi

exec "$VENV/bin/python" "$PLUGIN_ROOT/server/server.py"
