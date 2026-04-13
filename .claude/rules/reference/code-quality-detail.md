---
description: Domain-specific code quality rules — bulk mutations, SQLite pitfalls, testing patterns. Read when working with databases, pipelines, or test suites.
---

# Code Quality — Domain-Specific Rules

## Bulk Data Mutations

Before executing any operation that modifies or deletes >10 records:
1. **Dry-run first:** Run `SELECT COUNT(*)` with the same WHERE clause. Show the count to the user.
2. **Sample preview:** Show `LIMIT 5` of the rows that will be affected.
3. **Explicit confirmation:** Get the user's approval before executing.
4. **Pre-execution audit:** Log the operation to audit.db BEFORE executing (action_type, record count, WHERE clause summary).
5. **Prefer soft deletes:** Use state changes (e.g., `state='dismissed'`) over `DELETE` where schema supports it.

## Ad-hoc Database Queries

Before writing any inline Python that queries a SQLite database, inspect the schema first to get exact column names. NEVER guess column names — tables often have non-obvious names (`target` not `source`, `content` not `subject`). Schema mismatches in heredoc Python cause cascading errors that waste time.

## SQLite Pitfalls

- `DEFAULT CURRENT_TIMESTAMP` on `updated_at` only applies at INSERT. It does NOT auto-update on subsequent UPDATEs. Add an AFTER UPDATE trigger: `CREATE TRIGGER <table>_updated_at AFTER UPDATE ON <table> BEGIN UPDATE <table> SET updated_at=datetime('now') WHERE rowid=NEW.rowid; END;`
- Never use bare `except Exception: pass` in skill Python. Always log the error: `except Exception as e: print(f"ERROR: {e}", file=sys.stderr)`. Silent exceptions mask operational failures and prevent debugging.
- `sqlite3.Row` objects support `row["key"]` bracket access but NOT `.get("key")`. Code using `.get()` on Row objects raises `AttributeError`. Always use `row["key"]` with `try/except KeyError` or check column existence beforehand.

## Filter and Pipeline Testing

Every pipeline filter rule MUST have a corresponding test proving it fires in the actual execution path. A filter wired to one subsystem silently diverges from another if there is no end-to-end test. No test = not implemented. This is a recurring pattern: phone extraction filters, noise config, and calendar prefix filters all existed in isolation but were never wired to the code path they were supposed to guard.

**Pattern:** When adding a filter (e.g., `should_skip_draft`, contact exclusion, dedup gate), write a test that exercises the full path from input to filtered output — not just the filter function in isolation.

## Testing — Module-Level Constants

Do not monkeypatch module-level constants (DB paths, API URLs, feature flags) in tests. Monkeypatch coverage is fragile — missing one constant silently uses production resources. Instead, read configuration from environment variables at module load time and set those env vars in the test fixture.

**Pattern:** Replace `PREFS_DB = "/path/to/production.db"` with `PREFS_DB = os.environ.get("APP_STORE_DIR", "/default/path") + "/preferences.db"`. Tests set `APP_STORE_DIR` to `tmp_path` before import. Add a boundary test proving the safety gate actually blocks (e.g., verify `_send_email` is a no-op when `TEST_MODE=1`).

