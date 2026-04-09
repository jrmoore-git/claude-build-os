# Handoff

## Current focus
Adding `bm import` command — the last feature before v1.0.

## What's done
- `bm add`, `bm search`, `bm tags`, `bm export` all working
- FTS5 search returns ranked results in <50ms on 5K test bookmarks
- 23 tests passing, including round-trip export/import test skeleton

## What's not done
- `bm import` — JSON parsing done, but duplicate detection not implemented yet
- Duplicate detection: need to decide on URL normalization (trailing slash, www prefix, query params)
- No error handling for malformed JSON input in import

## Next session should
1. Read D3 (database decisions) and L1 (FTS tokenizer) before touching import
2. Implement duplicate detection using normalized URL as unique key
3. Add import error handling (malformed JSON, missing required fields)
4. Run full test suite and verify export→import round-trip

## Open questions
- Should `bm import` merge tags on duplicate URLs, or skip the duplicate entirely?
