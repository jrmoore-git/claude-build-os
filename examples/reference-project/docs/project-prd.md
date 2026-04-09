# Product Requirements: Bookmark CLI

## What are we building?
A command-line bookmark manager that saves URLs with tags to a local SQLite database and supports fast tag-based search.

## Who is it for?
Solo developer who saves ~20 bookmarks/day from terminal and needs instant tag-based retrieval.

## Requirements
- `bm add <url> --tags tag1,tag2` — save a bookmark with tags
- `bm search <query>` — full-text search across URLs, titles, and tags
- `bm tags` — list all tags with bookmark counts
- `bm export --format json` — export all bookmarks as JSON to stdout
- `bm import <file>` — import bookmarks from JSON file

## Out of scope
- Web UI or browser extension
- Sync between machines
- Bookmark validation (checking if URLs are live)
- User accounts or multi-user support

## Technical decisions
- Python 3.11, SQLite with WAL mode
- Click for CLI framework
- FTS5 for full-text search
- Single-file database at `~/.bookmarks.db`

## Success criteria
- Add + search round-trip in <100ms for 10,000 bookmarks
- Export produces valid JSON that import can round-trip
- All commands work offline
