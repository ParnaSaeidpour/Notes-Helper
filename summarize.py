"""Summarize all notes by category, using the Claude Agent SDK.

What is the Claude Agent SDK?
  - It is Claude Code packaged as a Python library. The `query()` call below
    launches the same `claude` CLI you use interactively, as a subprocess, and
    streams its messages back to this script.
  - You get the whole Claude Code "harness" for free: the agent loop (model
    calls a tool -> result goes back -> model calls again until done), MCP
    server management, permissions, and session handling.
  - Compare this with the plain `anthropic` SDK, where you call the Messages
    API directly and have to write that loop, and wire up MCP, yourself.

How is this different from chatting with Claude Code?
  - Interactive Claude Code: you type prompts, it prints replies, you decide
    what happens next. It reads .mcp.json from the project automatically.
  - This script: there is no human in the loop. The prompt is hard-coded, the
    MCP server is configured explicitly in Python, and the final answer is a
    string your program can print, store, or pass on. Think "Claude Code as a
    function call" rather than "Claude Code as a chat".
  - Authentication is the same: it uses whatever `claude` is already logged in
    with, or ANTHROPIC_API_KEY if that is set.

Run it with:
    .venv/bin/python summarize.py
"""

import asyncio
import sys
from pathlib import Path

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    query,
)

# Reuse the exact same server launch command that .mcp.json uses, so this
# script and interactive Claude Code read the same notes.json.
HERE = Path(__file__).parent
PYTHON = HERE / ".venv" / "bin" / "python"
SERVER = HERE / "server.py"

PROMPT = "Summarize all my notes by category."


async def summarize_notes(prompt: str = PROMPT, on_progress=None) -> tuple[str, float | None]:
    """Run the agent and return (summary text, cost in USD).

    The cost comes from the ResultMessage the SDK sends at the end of a run.
    It is None when the SDK cannot report it (for example on some subscription
    plans), in which case the run is covered by your plan rather than billed
    per token.

    `on_progress` is an optional callback that receives intermediate text, so a
    caller (the CLI below, or the web app) can show what Claude is doing.
    """
    options = ClaudeAgentOptions(
        # Register the notes MCP server. Interactive Claude Code picks this up
        # from .mcp.json; the SDK wants it passed explicitly (or you can point
        # mcp_servers at the .mcp.json path instead).
        mcp_servers={
            "notes": {
                "type": "stdio",
                "command": str(PYTHON),
                "args": [str(SERVER)],
            }
        },
        # MCP tools are named mcp__<server>__<tool>. Pre-approving them means
        # the agent never stops to ask for permission, which matters because
        # nobody is sitting at a terminal to say yes.
        allowed_tools=["mcp__notes__list_notes"],
        # Keep the agent focused: no file editing, no shell, just the notes.
        disallowed_tools=["Bash", "Edit", "Write", "Read", "Glob", "Grep"],
        system_prompt=(
            "You are a notes assistant. Use the list_notes tool to fetch the "
            "user's notes, then group them by the [category] tag found in each "
            "note. Notes without a tag go under 'uncategorized'. Reply with a "
            "short Markdown summary, one heading per category."
        ),
        max_turns=5,
        cwd=str(HERE),
    )

    # query() is an async generator. It yields each message as the agent works:
    # SystemMessage (startup info), AssistantMessage (model output, including
    # tool calls), and finally a ResultMessage with the finished answer.
    final_text: str | None = None
    cost_usd: float | None = None
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            # Report progress as it happens, like watching Claude Code work.
            for block in message.content:
                if isinstance(block, TextBlock) and block.text.strip() and on_progress:
                    on_progress(block.text.strip())
        elif isinstance(message, ResultMessage):
            if message.is_error:
                raise RuntimeError(f"Agent failed: {message.result or message.errors}")
            final_text = message.result
            cost_usd = message.total_cost_usd

    return final_text or "(no answer returned)", cost_usd


async def main() -> None:
    summary, cost = await summarize_notes(
        on_progress=lambda text: print(f"[claude] {text}", file=sys.stderr)
    )
    print("\n=== Summary ===")
    print(summary)
    print(f"\n(cost: {format_cost(cost)})")


def format_cost(cost: float | None) -> str:
    """Turn the SDK's cost figure into a short human-readable string."""
    if cost is None:
        return "not reported, covered by your plan"
    return f"${cost:.4f} USD"


if __name__ == "__main__":
    asyncio.run(main())
