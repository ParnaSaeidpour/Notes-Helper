# Notes Helper plugin

Installs two things into Claude Code in one step:

- **MCP server `notes`** with tools `add_note` and `list_notes`. Notes are stored in
  `~/.claude/plugins/data/notes-helper/notes.json`.
- **Skill `note-style`** that makes Claude write every note as `YYYY-MM-DD [category] text`.

Requires `python3` on the machine. The server's `mcp` dependency is installed
automatically into a private virtualenv the first time the server starts.

## Install

```
claude plugin marketplace add <path-or-git-url-of-this-repo>
claude plugin install notes-helper@notes-helper-marketplace
```

Or try it for one session without installing:

```
claude --plugin-dir ./notes-plugin
```
