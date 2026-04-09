# Decisions

### D1: Use Click instead of argparse
Click provides better help generation, type validation, and composability for multi-command CLIs. argparse would work but requires more boilerplate for the same result.
**Date:** 2025-01-15

### D2: FTS5 over LIKE queries for search
SQLite FTS5 gives ranked results and handles 10K+ bookmarks in <10ms. LIKE with wildcards degrades linearly and can't rank by relevance.
**Date:** 2025-01-15

### D3: Single database file, not per-tag files
Considered one JSON file per tag for simplicity. Rejected because cross-tag search becomes O(n) file reads. SQLite handles both use cases with one file.
**Date:** 2025-01-16

### D4: WAL mode required for all connections
WAL allows concurrent reads during writes. Default journal mode blocks readers during any write. Since export can be long-running, WAL prevents search from blocking.
**Date:** 2025-01-18
