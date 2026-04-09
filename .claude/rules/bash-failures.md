# Bash Failures — Fix Forward, Don't Bandaid

**A bash error is a signal to investigate, not an obstacle to bulldoze through.**

When a command fails, diagnose the root cause and apply a permanent fix. Do not retry, workaround, or delete your way past the error. If a permanent fix isn't feasible in the current task, apply the workaround AND log the root cause to `tasks/lessons.md`.

## Never Delete or Move Hook Scripts

`hooks/hook-*` and `.claude/settings.json` are critical infrastructure. Deleting or moving hook scripts causes total deadlock: every tool call fails, the stop hook loops, and recovery requires manual Terminal intervention.

**Prohibited:**
- `rm -rf hooks/` or any deletion of the hooks directory
- Moving hook scripts out of `hooks/` (even with symlinks — symlinks broke this on 2026-03-30)
- Replacing real files in `hooks/` with symlinks to another directory
- `rm hooks/hook-*` or any bulk deletion of hook files

**Hook files must be real files in `hooks/`, never symlinks.** Settings.json references `hooks/hook-*` directly. If the real file is elsewhere and linked, deleting the target = total lockout.

*Origin: 2026-03-30 — hooks lived in `hooks/` with symlinks from `scripts/`. `rm -rf hooks/` broke all symlinks. Four sessions deadlocked.*

## Prohibited Patterns (Hook-Enforced)

These commands are blocked by `hook-bash-fix-forward.py` until investigation is performed:

| Pattern | Required First |
|---------|---------------|
| `rm .git/index.lock` | `lsof .git/index.lock` or `pgrep git` — remove only if no process holds it |
| `kill -9` / `kill -KILL` | `ps aux` to identify the process and why it's stuck — graceful `kill <pid>` is OK |
| `pkill <name>` | `pgrep -a <name>` to see what's running — then kill specific PIDs |
| `rm *.lock` / `rm *.pid` | `lsof <file>` or `fuser <file>` — check if still in use |

## Advisory Patterns (Not Hook-Enforced)

| Pattern | Do Instead |
|---------|-----------|
| `rm -rf node_modules && npm install` | Read the error message. Check `node -v`. Verify the failing module. Only reinstall if the error is genuinely a stale cache. |
| Retrying the same command after failure | Try a different approach. If the same command failed, running it again won't help. |
| `sudo` or `chmod 777` after permission denied | `ls -la <path>` and `whoami` — understand the ownership before changing it |
| Hardcoding paths after "command not found" | `which <cmd>` or `type <cmd>` — fix PATH in shell profile or .env, not inline |
| Inline `export VAR=x` before a command | Fix the variable in `.env`, shell profile, or the relevant plist |

## Diagnostic Sequences

### `.git/index.lock` exists
1. `lsof .git/index.lock` — is a process holding it?
2. `pgrep -a git` — any git processes running?
3. If no process holds the lock → stale crash artifact, safe to remove
4. If a process holds the lock → wait for it or investigate why it's stuck

### `MODULE_NOT_FOUND` or npm errors
1. Read the full error — which module, which path?
2. `node -v` — correct Node version? (should be 22.22.0 via nvm)
3. `cat package.json | grep <module>` — is it a declared dependency?
4. Only then consider targeted reinstall of the specific module

### `Permission denied`
1. `ls -la <path>` — who owns it? What are the permissions?
2. `whoami` — are you the expected user?
3. Fix ownership (`chown`) or permissions (`chmod`) specifically — never `chmod 777`

### `command not found`
1. `which <command>` or `type <command>` — is it in PATH?
2. Check if the tool is installed (`brew list`, `pip list`, etc.)
3. Fix PATH in the shell profile or relevant config — don't hardcode absolute paths inline
