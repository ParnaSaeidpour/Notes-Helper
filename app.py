"""A small web interface for the notes app.

Runs a local web server (Python standard library only, nothing to install) that:
  - lists the notes from notes.json, the same file the MCP server uses
  - adds a note in the note-style format: "YYYY-MM-DD [category] text"
  - summarizes the notes by category by calling summarize.py (Claude Agent SDK)

Run it with:
    .venv/bin/python app.py
then open http://localhost:8787
"""

import asyncio
import json
import os
import re
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# Reuse the storage path from the MCP server, so both see the same notes.
from server import NOTES_FILE, _load
from summarize import format_cost, summarize_notes

PORT = int(os.environ.get("PORT", "8787"))  # override with PORT=... if busy
HTML = (Path(__file__).parent / "static" / "index.html").read_text()

MAX_WORDS = 20
NOTE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})\s+\[([^\]]+)\]\s+(.*)$")


def _save(notes: list[str]) -> None:
    NOTES_FILE.write_text(json.dumps(notes, indent=2))


def format_note(text: str, category: str) -> str:
    """Apply the note-style rules: date prefix, [category], under 20 words."""
    category = (category or "personal").strip().lower()
    note = f"{date.today().isoformat()} [{category}] {text.strip()}"
    words = note.split()
    if len(words) > MAX_WORDS:
        note = " ".join(words[:MAX_WORDS])
    return note


def parse_note(note: str) -> dict:
    """Split a stored note into its parts for display. Old notes without a
    date or category are shown as 'uncategorized'."""
    m = NOTE_RE.match(note)
    if m:
        return {"date": m.group(1), "category": m.group(2), "text": m.group(3), "raw": note}
    return {"date": "", "category": "uncategorized", "text": note, "raw": note}


class Handler(BaseHTTPRequestHandler):
    def _json(self, status: int, payload) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(length) or b"{}")

    def do_GET(self) -> None:
        if self.path == "/":
            body = HTML.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/api/notes":
            self._json(200, [parse_note(n) for n in _load()])
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self) -> None:
        if self.path == "/api/notes":
            data = self._body()
            text = (data.get("text") or "").strip()
            if not text:
                return self._json(400, {"error": "note text is required"})
            notes = _load()
            notes.append(format_note(text, data.get("category", "")))
            _save(notes)
            self._json(201, parse_note(notes[-1]))
        elif self.path == "/api/notes/delete":
            idx = self._body().get("index")
            notes = _load()
            if not isinstance(idx, int) or not 0 <= idx < len(notes):
                return self._json(400, {"error": "bad index"})
            notes.pop(idx)
            _save(notes)
            self._json(200, {"ok": True})
        elif self.path == "/api/summarize":
            # The Agent SDK is async; run it to completion inside this request.
            try:
                summary, cost = asyncio.run(summarize_notes())
                self._json(200, {"summary": summary, "cost": format_cost(cost)})
            except Exception as e:  # surface the error in the UI instead of a 500 page
                self._json(500, {"error": str(e)})
        else:
            self._json(404, {"error": "not found"})

    def log_message(self, fmt, *args):  # quieter console
        print(f"{self.command} {self.path} -> {args[1] if len(args) > 1 else ''}")


if __name__ == "__main__":
    print(f"Notes Helper UI running at http://localhost:{PORT}  (Ctrl+C to stop)")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
