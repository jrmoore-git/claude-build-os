---
description: macOS, Docker, Homebrew, Node, Python platform rules
globs:
  - "docker/**"
  - "scripts/**"
  - "*.sh"
---

# Platform Rules

- macOS uses BSD tools (date, sed, grep) — NOT GNU. Use `python3` for timestamp math. No `flock` — use `mkdir` for atomic locking.
- Homebrew on Apple Silicon installs to `/opt/homebrew`, not `/usr/local`. Set `HOMEBREW_NO_AUTO_UPDATE=1` in shells.
- Python 3.11+ required. Use `python3` (resolved by `hooks/resolve-python.sh`). Run `./setup.sh` to detect and cache the path.
- nvm is a shell function, not a binary — launchd/cron can't use it. All plists must use absolute Node path.
- `brew unlink node` if Homebrew installs a conflicting Node version. Check `which node` resolves to expected version.
- Docker Desktop on macOS may need manual first launch. Verify daemon before writing compose files.
- Docker images must be ARM64 native (Apple Silicon). Verify with `docker inspect | grep Architecture`.
- Docker `internal: true` networks need a second bridge network for services that need internet.
- Docker `env_file` provides vars to container; `environment: ${VAR}` resolves from HOST. Don't mix both for same vars.
- Docker credential helper symlinks break on macOS — clear `credsStore` in `~/.docker/config.json` if broken.
- `node_modules` from different Node versions break with MODULE_NOT_FOUND. Fix: `rm -rf node_modules && npm install`.
- User home directory is mode 700 — framework service account can't traverse it. Own all dbs as the primary user. Never run the framework service user for files under the home directory.
- `sqlite3 -json` with `.timeout 5000` as an inline dot-command silently returns empty output (exit 0). The `.timeout` dot-command and `-json` flag are incompatible when combined in a single argument string. Fix: use `sqlite3 -json -cmd ".timeout 5000" /path/to/db "SELECT ..."` — the `-cmd` flag runs dot-commands before the main query.
- Stale `-shm` files cause "disk I/O error" in SQLite. Remove `-shm` and `-wal` before migrations. Stop gateway first.
- Do not use `:latest` Docker tags — pin everything. Verify tags exist on registry before writing compose files.
- Framework gateway bind valid values: "loopback", "lan", "all", "private" (NOT "tailscale"). Non-loopback requires `controlUi.dangerouslyAllowHostHeaderOriginFallback: true` or explicit `allowedOrigins`.
- Framework cron + Claude Code can now run concurrently (scoped rate-limit cooldowns prevent cascading 429s). Heavy concurrent usage may still hit individual Tier 2 limits (450K ITPM), but one model's 429 no longer blocks all models on the same auth profile. One-off `debate.py` calls are fine — they mostly hit non-Anthropic models via LiteLLM.
- `PyYAML` is not installed. Parse YAML frontmatter with stdlib (regex/string splitting). Do not `import yaml`.
- `pytz` is not installed. Use stdlib `zoneinfo` for timezone math (`from zoneinfo import ZoneInfo`). Use `America/Los_Angeles` (canonical IANA), not deprecated `US/Pacific`.
- SQLite date functions (`date('now')`, `datetime('now')`, `CURRENT_TIMESTAMP`) always return UTC. If the application stores or compares timestamps in Pacific time, SQLite date functions produce wrong results. Always use Python with `ZoneInfo('America/Los_Angeles')` for timezone-aware date arithmetic — never rely on SQLite date functions for Pacific time comparisons.
- launchd `KeepAlive: true` means the process is managed by launchd — `pkill` or `kill` will auto-restart it immediately. To stop a KeepAlive service: `launchctl unload <plist>` first, then kill. Never `nohup` a process that is already managed by a KeepAlive plist.
