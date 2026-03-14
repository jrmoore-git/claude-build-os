# Example Hooks

Claude Code hooks are shell commands that fire automatically before or after tool events. They turn advisory rules into deterministic enforcement — Level 3 on the [enforcement ladder](../docs/the-build-os.md#part-v-the-enforcement-ladder).

For full hook API documentation (matcher syntax, available events, environment variables), see [Anthropic's official hook docs](https://docs.anthropic.com/en/docs/claude-code/hooks).

## What's here

### `hook-block-env-write.sh` — Block writes to .env files
A `PreToolUse` hook that prevents Claude from editing `.env` files, keeping secrets out of tool output. Use this when your project has credentials in `.env` that should never appear in Claude's context.

### `hook-test-after-edit.sh` — Run tests after source edits
A `PostToolUse` hook that runs your test suite after any source file edit. Supports Python (pytest), JS/TS (npm test), and Go (go test). Use this to catch regressions immediately.

## Starter settings.json

Wire up both hooks by adding this to `.claude/settings.json`:

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
    ],
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

## When to add hooks

Start with one. The highest-value first hooks:
- **Block `.env` writes** — prevents secret exposure (included above)
- **Test after edit** — catches regressions immediately (included above)
- **Block commits when tests fail** — prevents broken code from landing
- **Export session signal** — keeps your memory layer fresh

If you've told Claude not to do something three times and it keeps doing it, that's your signal to add a hook. See [the enforcement ladder](../docs/the-build-os.md#part-v-the-enforcement-ladder) for the full escalation model.
