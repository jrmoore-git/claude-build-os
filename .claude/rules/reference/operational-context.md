---
description: Check operational health before modifying skills, toolbelt scripts, or cron schedules
---

# Operational Context — Read Before You Write

Before modifying a skill (`skills/*/SKILL.md`), toolbelt script (`scripts/*_tool.py`), or cron schedule, check the operational health of what you're changing. The data is in `stores/debate-log.jsonl` and `stores/metrics.db`.

## When to Check

- Before editing a skill's SKILL.md or its backing script
- Before changing a cron schedule or adding a cron job
- During `/recall` session bootstrap (skill health query only)

## Data Sources

### debate-log.jsonl — debate engine log

One JSON object per line. Each entry records a debate.py run:

```json
{"timestamp": "2026-04-10T...", "phase": "challenge", "debate_id": "...", "challengers": 3, ...}
```

Fields vary by phase (challenge, judge, refine, review, review-panel). Common fields: `timestamp`, `phase`, `debate_id`.

### metrics.db — quality_metrics

```
id              INTEGER PRIMARY KEY AUTOINCREMENT
metric_date     TEXT NOT NULL                     -- YYYY-MM-DD Pacific
metric_type     TEXT NOT NULL
category        TEXT
value           REAL NOT NULL
threshold       REAL
breached        INTEGER DEFAULT 0
detail          TEXT                              -- JSON aggregates only, never message content
created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
UNIQUE(metric_date, metric_type, category)
```

## Queries

### A. Recent debate activity

```bash
tail -20 stores/debate-log.jsonl | python3.11 -c "
import sys, json
for line in sys.stdin:
    try:
        e = json.loads(line)
        print(f\"{e.get('timestamp','?')[:16]}  {e.get('phase','?'):15s}  {e.get('debate_id','?')}\")
    except: pass
"
```

### B. Activity by phase (last 7 days)

```bash
python3.11 -c "
import json, sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
cutoff = (datetime.now(ZoneInfo('America/Los_Angeles')) - timedelta(days=7)).isoformat()
counts = {}
for line in open('stores/debate-log.jsonl'):
    try:
        e = json.loads(line)
        if e.get('timestamp', '') >= cutoff:
            phase = e.get('phase', 'unknown')
            counts[phase] = counts.get(phase, 0) + 1
    except: pass
for phase, n in sorted(counts.items(), key=lambda x: -x[1]):
    print(f'{phase}: {n} runs')
"
```

### C. Total entry count

```bash
wc -l < stores/debate-log.jsonl
```

## Output Format

When reporting health to the session, use structured signals only:

```
Debate Activity (7d):
  challenge: 8 runs, last=2026-04-10T14:00
  review-panel: 5 runs, last=2026-04-10T11:30
  judge: 3 runs, last=2026-04-09T16:00
  Total entries: 95
```

Do not paste raw JSON into conversation context. Summarize into the format above.
