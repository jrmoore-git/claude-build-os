# Contract Tests

Behavioral invariants that must hold regardless of implementation changes. Run these after any significant change.

## Essential Eight (applied to Bookmark CLI)

### C1: Idempotency
`bm add` with the same URL twice must not create duplicate rows. Second call updates tags if different, no-ops if identical. Verify: `bm add https://example.com --tags a && bm add https://example.com --tags a && bm search example | wc -l` returns 1.

### C2: Approval gating
Not applicable — single-user CLI with no destructive operations requiring confirmation. If bulk delete is added later, it must require `--confirm` flag.

### C3: Audit completeness
Every `bm add` and `bm import` records a `created_at` timestamp. Every `bm export` includes the timestamp per bookmark. Verify: exported JSON has `created_at` field on every entry.

### C4: Degraded mode visible
If the database is locked (concurrent access), CLI must print a clear error to stderr and exit 1 — not hang silently. Verify: `flock ~/.bookmarks.db sleep 5 & bm search test` returns error within 1 second.

### C5: State machine validation
Bookmark states: `active` (default), `archived`. No direct transition from `archived` to `deleted` — must go through `active` first. Verify: `bm archive <id> && bm delete <id>` fails with "must unarchive first."

### C6: Rollback path exists
`bm import` must be atomic — if any row fails, no rows are committed. Verify: create a JSON file with 5 valid + 1 malformed entry, run `bm import`, confirm 0 new rows in database.

### C7: Version pinning enforced
`setup.py` / `pyproject.toml` pins all dependencies to exact versions. No `>=` or `~=` specifiers. Verify: `grep -c '[>~]=' pyproject.toml` returns 0.

### C8: Exactly-once scheduling
Not applicable — no scheduled/cron operations in v1. If RSS auto-import is added, it must deduplicate by URL before insert.

## Domain-specific

### C9: Search correctness
FTS5 search for "python" must return bookmarks tagged "python" AND bookmarks with "python" in the URL or title. Verify: add bookmark with tag "python" and another with URL containing "python" — search returns both.

### C10: Export/import round-trip
`bm export > /tmp/bm.json && bm import /tmp/bm.json` on an empty database must produce identical bookmark set. Verify: export again, diff the two JSON files (ignoring `created_at` on import).

### C11: Tag integrity
Deleting a bookmark must remove its tag associations. Orphan tags (associated with 0 bookmarks) must not appear in `bm tags` output. Verify: add bookmark with unique tag, delete bookmark, `bm tags` no longer shows that tag.
