# Lessons

### L1: SQLite FTS5 tokenizer strips hyphens from URLs
FTS5's default tokenizer treats hyphens as word separators. Searching for "my-project" matches "my" and "project" separately. Fix: use `tokenize='unicode61 remove_diacritics 2'` and also store the raw URL in a separate indexed column for exact matching.
**Source:** Search returned wrong results for hyphenated domains.

### L2: Click's `--tags` option needs a custom type for comma-separated values
`click.STRING` treats "tag1,tag2" as one string. Need a custom `CommaSeparated` type or use `multiple=True` with repeated `--tag` flags. Chose comma-separated for UX (one flag, one argument).
**Source:** Tags were stored as single string including commas.

### L3: JSON export must use stdout, progress must use stderr
Mixed stdout/stderr in early version broke piping (`bm export | jq`). All progress messages, warnings, and counts go to stderr. Only the JSON payload goes to stdout.
**Source:** `bm export | jq` failed with "parse error: Invalid numeric literal."
