"""A tiny MCP server for a notes app.

What makes this an "MCP server"?
  - It speaks the Model Context Protocol: a JSON-RPC message format that
    clients like Claude Code use to discover and call "tools".
  - It advertises tools (name + description + input schema) that a client
    can list, then executes them when the client asks.
  - It talks over a transport. Here it's stdio: Claude Code launches this
    script as a subprocess and exchanges messages over stdin/stdout.

The official SDK handles all the protocol details; we just write Python functions.
"""

import json
import os
from pathlib import Path

# MCPServer is the SDK's high-level server class (called FastMCP in SDK v1).
from mcp.server.mcpserver import MCPServer

# Create the server. The name is what clients show when they list servers.
mcp = MCPServer("notes")

# Where notes live. Default: next to this file. The NOTES_FILE environment
# variable overrides it; the plugin uses that to store notes in a stable
# per-user data directory instead of inside the (replaceable) plugin folder.
NOTES_FILE = Path(os.environ.get("NOTES_FILE") or Path(__file__).parent / "notes.json")


def _load() -> list[str]:
    """Read all notes from disk (an empty list if the file doesn't exist yet)."""
    if NOTES_FILE.exists():
        return json.loads(NOTES_FILE.read_text())
    return []


# @mcp.tool() turns a plain function into an MCP tool:
#   - the function name becomes the tool name ("add_note")
#   - the docstring becomes the description the model reads to decide when to use it
#   - the type hints (text: str) become the JSON schema for the tool's input
@mcp.tool()
def add_note(text: str) -> str:
    """Save a new note."""
    notes = _load()
    notes.append(text)
    NOTES_FILE.write_text(json.dumps(notes, indent=2))
    return f"Saved note #{len(notes)}."


@mcp.tool()
def list_notes() -> list[str]:
    """Return all saved notes."""
    return _load()


if __name__ == "__main__":
    # Start the server on stdio. Don't print() anything else to stdout:
    # stdout carries the protocol messages, and stray output would corrupt them.
    mcp.run(transport="stdio")
