# Examples

Concrete examples of the Build OS framework's enforcement mechanisms. These supplement the [enforcement ladder](../docs/the-build-os.md#part-v-the-enforcement-ladder) with copy-ready artifacts.

> **Note:** These are **starter examples** for new projects — not the hooks that ship in `hooks/`. The Build OS ships sixteen production hooks in [`hooks/`](../hooks/) (see the [Hooks Reference](../docs/hooks.md)). The examples below are simplified versions you can copy and adapt.

## What's here

### `enforcement-ladder.md` — One policy, four levels

A walkthrough showing the same policy ("don't commit secrets") enforced at all four levels of the enforcement ladder: CLAUDE.md line → `.claude/rules/` file → hook → architecture. **Read this first** to understand when to use each mechanism.

### `rules/security.md` — Starter security rules (always-loaded)

Example `.claude/rules/` file with no `paths:` frontmatter — loads every session. Covers: LLM boundary, provenance, secret handling, hook safety. Copy and adapt for your project.

### `rules/code-quality.md` — Starter code quality rules (path-specific)

Example `.claude/rules/` file WITH `paths:` frontmatter — only loads when Claude reads matching source files. Demonstrates how path-specific rules reduce context noise.

### `hook-block-env-write.sh` — Block writes to .env files

A `PreToolUse` hook that prevents Claude from editing `.env` files. Level 3 enforcement — deterministic, cannot be overridden.

### `hook-test-after-edit.sh` — Run tests after source edits

A `PostToolUse` hook that runs your test suite after any source file edit. Supports Python (pytest), JS/TS (npm test), and Go (go test).

## Hook configuration

Add hooks to your `.claude/settings.json`. **Merge these entries into your existing settings — do not replace the entire file.**

### Block .env writes (PreToolUse)

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "sh examples/hook-block-env-write.sh $CLAUDE_FILE_PATH"
          }
        ]
      }
    ]
  }
}
```

### Run tests after edits (PostToolUse)

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "sh examples/hook-test-after-edit.sh $CLAUDE_FILE_PATH"
          }
        ]
      }
    ]
  }
}
```

## Hook types

Claude Code supports four hook types. See [Platform Features](../docs/platform-features.md) for the full reference.

| Type | What it does | Example use |
|---|---|---|
| `command` | Runs a shell command | Block file writes, run tests (examples above) |
| `http` | POSTs to a URL | External webhooks, audit logging |
| `prompt` | Single-turn LLM evaluation | Policy checks too nuanced for regex |
| `agent` | Multi-turn subagent verification | Complex validation requiring file reads |

The `prompt` and `agent` types are particularly powerful — they bridge the gap between regex-based command hooks and advisory rules by using LLM judgment with deterministic enforcement (exit code 2 = block).

## When to add hooks

Start with one. The highest-value first hooks:
- **Block `.env` writes** — prevents secret exposure (included above)
- **Test after edit** — catches regressions immediately (included above)
- **Block commits when tests fail** — write this for your specific test framework
- **Export session signal** — keeps your memory layer fresh

If you've told Claude not to do something three times and it keeps doing it, that's your signal to add a hook. See [the enforcement ladder](../docs/the-build-os.md#part-v-the-enforcement-ladder) for the full escalation model.
