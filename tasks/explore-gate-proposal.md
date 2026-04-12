# Proposal: Structural Enforcement for "Explore Before Acting" and "Inspect Before Answering"

## Problem Statement

Two recurring complaints about Claude Code's behavior in the BuildOS framework:

1. **"Not enough iterative exploration before it goes to work"** — the AI jumps to implementation without exploring the codebase first
2. **"Doesn't inspect code before giving answers, assumes it can't do something"** — the AI answers questions about code without reading it, defaulting to training knowledge

Both are partially addressed in the debate/review workflow (explore mode, pre-flight, --enable-tools) but NOT structurally enforced for general Claude Code usage — which is the daily experience.

## Current State

### What exists
- Decomposition gate (`hook-decompose-gate.py`) blocks `Write|Edit` until decomposition is assessed — proves the pattern works
- `workflow.md` says "read code before proposing changes" — advisory, not enforced
- `--enable-tools` gives debate engine challengers read-only tools — but only applies to external model calls through LiteLLM
- Explore mode with pre-flight discovery in `/explore` — but only for explore workflow, not general coding

### What's missing
- No hook blocking edits until target files are read
- No mechanism detecting "model is answering about code without reading it"
- No structural enforcement of the "orient before planning" rule
- Advisory rules don't reliably fire under context pressure

## Proposed Solution

### Fix 1: Pre-edit exploration gate (hook-enforced)

A hook on `Edit`/`Write` tool calls that verifies the target file (or files in the same directory) has been read in the current session before allowing modification.

**Implementation:** `hooks/hook-pre-edit-read-check.py`
- Track session-level read operations (Read, Grep, Glob calls)
- On Edit/Write, check if the target file was previously read
- If not read: block with "Read the file before editing it"
- Claude Code already enforces this for Edit (errors if unread), but Write has no such check, and neither enforces reading *neighboring* files (tests, related modules)

**Lightweight variant:** Track a session-level counter of read-type tool calls. If Edit/Write fires before 3+ reads have occurred in the session, emit a warning (not a hard block — just friction).

**Trade-offs:**
- Pro: Same proven pattern as decomposition gate
- Pro: Low false-positive rate — legitimate edits almost always involve reading first
- Con: Doesn't enforce *understanding*, only reading
- Con: Could be annoying for trivial single-file edits (mitigation: bypass for files under 50 lines or commits tagged `[TRIVIAL]`)

### Fix 2: Behavioral pattern rule (CLAUDE.md-enforced)

Rewrite the vague "orient before planning" rule to a specific, actionable behavioral pattern:

```
When asked about code behavior, implementation details, or "can we do X":
1. Grep/Read the relevant code FIRST
2. Only THEN answer based on what you found
3. Never say "I don't think this supports..." without checking
```

**Why this over a hook:** You can't hook on text output — there's no way to detect "the model is about to answer a question about code" before it does. The strongest lever for Claude Code's own session behavior is specific instructions in CLAUDE.md. The current rule ("orient before planning") is too vague to trigger reliably.

**Trade-offs:**
- Pro: Specific behavioral instructions in CLAUDE.md are the strongest non-hook lever
- Pro: Zero implementation cost
- Con: Not structurally enforced — model can and will skip under context pressure
- Con: Only as good as the model's instruction following

### What NOT to build

- A hook on text output detecting "answering about code" — fighting the model architecture, too many false positives
- A mandatory N-file-read gate before any response — would make simple questions unbearably slow
- Upstream BuildOS changes — the CPO's version would need to be updated separately anyway

## Recommendation

Build Fix 1 (pre-edit gate hook) and ship Fix 2 (behavioral rule rewrite) together. The hook provides structural enforcement for the editing path; the rule provides behavioral guidance for the answering path. Neither alone is sufficient.

Priority: Fix 1 first — it's the higher-value change because it prevents the most damaging behavior (editing without understanding).
