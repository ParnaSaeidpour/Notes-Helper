---
name: note-style
description: Formatting rules for notes saved with the notes MCP server (add_note). Use whenever the user asks to add, save, or write a note.
---

# Note style

Every note saved through the `add_note` tool must follow these rules:

1. **Start with a date** in ISO format (`YYYY-MM-DD`). Use today's date unless the user gives another.
2. **Then a category in square brackets**, such as `[work]` or `[personal]`. Pick the category from the user's wording; if it is unclear, use `[personal]`.
3. **Keep the whole note under 20 words**, including the date and category. Shorten the user's text if needed, but keep its meaning.

Format:

```
YYYY-MM-DD [category] note text
```

Examples:

```
2026-11-03 [personal] buy milk
2026-11-03 [work] send the quarterly report to finance by Friday
```

If the user's request is too long to fit in 20 words, condense it and tell the user what you shortened.
