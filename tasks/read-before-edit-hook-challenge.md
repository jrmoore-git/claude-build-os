---
debate_id: read-before-edit-hook
created: 2026-04-15T20:15:27-0700
mapping:
  A: claude-opus-4-6
  B: gemini-3.1-pro
  C: gpt-5.4
---
# read-before-edit-hook — Challenger Reviews

## Challenger A — Challenges
## Challenges

1. **ASSUMPTION** [MATERIAL] [COST:SMALL]: **`$CLAUDE_SESSION_ID` existence and stability is unverified.** The proposal says "or parent PID fallback, same as decompose gate" — but if the decompose gate's fallback is parent PID, that's fragile across tool restarts, backgrounded processes, or SSH reconnects. If the session key is wrong, the tracker either (a) never finds prior reads (false warnings on every edit) or (b) leaks across sessions (stale reads suppress warnings that should fire). The brief should confirm which env var the decompose gate actually uses and whether it's reliably set. Fix: inspect the decompose gate's session-key logic, reuse it exactly, and add a log line when falling back to PID so you can detect drift.

2. **RISK** [MATERIAL] [COST:SMALL]: **Grep/Glob "awareness" tracking is underspecified and could silently defeat the hook.** The brief says "Grep results that include the target file path" count as awareness. But Grep/Glob PostToolUse output is a list of matches — the hook needs to parse tool output to extract which files appeared in results. This is a different shape than Read tracking (where the file path is an explicit argument). If the parsing is wrong or the output format changes, you either get false positives (annoying) or false negatives (the hook thinks you've seen files you haven't, which is the *exact failure mode you're trying to prevent*). Recommendation: for the simplest testable version, **drop Grep/Glob tracking entirely**. Only count explicit Read. You can add Grep awareness later with data on how often it causes false warnings. This keeps the ~50-line budget honest.

3. **UNDER-ENGINEERED** [ADVISORY]: **No cleanup of `/tmp/buildos-read-tracker-*.json` files.** Over time these accumulate. Not a real problem if sessions are infrequent, but worth a one-liner cleanup (e.g., delete files older than 24h on hook invocation, or use a tmpfiles.d entry).

4. **RISK** [ADVISORY]: **Warning-only mode may have zero behavioral impact.** If the warning is emitted as an advisory message that Claude can observe but isn't trained to act on, it may be ignored 100% of the time, making this a no-op. The brief acknowledges "promote to blocking after validation" but doesn't define the validation criteria (what % ignored = promote?). Suggest: define the threshold now (e.g., "if >50% of warnings are followed by an edit without an intervening read within 2 weeks, promote to block").

5. **ALTERNATIVE** [ADVISORY]: **Could this be a PreToolUse-only hook with no PostToolUse component?** Instead of maintaining state, the PreToolUse gate could check the conversation context / tool call history directly (if the hook infrastructure exposes it). This eliminates the temp file, session-key problem, and cleanup concern entirely. If the hook infrastructure doesn't expose call history — fine, the stateful approach is the only option. But worth 5 minutes to check.

## Concessions

1. **The deferral analysis is solid.** Identifying that the blocker (no hook infrastructure) is resolved, citing the specific existing hook on the same path, is exactly the right way to unblock deferred work.
2. **Warning-before-block is the right rollout strategy.** Shipping a non-blocking version first avoids the risk of halting legitimate workflows while you collect signal.
3. **Scope reuse from `protected-paths.json` and exempt-path list is clean.** No new configuration surface, no new concepts — this slots into the existing hook pattern.

## Verdict

**APPROVE** with two conditions: (1) confirm the session-key mechanism by inspecting the decompose gate's actual implementation rather than assuming, and (2) drop Grep/Glob awareness from v1 to keep the scope honest and avoid a subtle false-negative path. Both are SMALL fixes that don't change the architecture.

---

## Challenger B — Challenges
## Challenges
1. [UNDER-ENGINEERED] [MATERIAL] [COST:MEDIUM]: The proposal states "Grep/Glob matches count as awareness", but the Simplest Testable Version completely omits this mechanism. Extracting read file paths from PostToolUse Grep/Glob output is non-trivial (requires parsing tool stdout/stderr accurately). If you don't implement this, the hook will falsely warn the agent every time it safely inspects a file via `grep` instead of `read_file`, training the agent to ignore the warning. 
2. [RISK] [MATERIAL] [COST:SMALL]: JSON tracking files are prone to corruption under parallel tool execution. If Claude triggers concurrent `read_file` operations, multiple PostToolUse hooks will read/write the JSON simultaneously, breaking the schema. Switch to an atomic append-only flat text file (`echo "$FILE_PATH" >> tracker.txt` and `grep -Fxq`) to avoid state corruption.
3. [RISK] [ADVISORY]: There is no lifecycle management for `/tmp/buildos-read-tracker-{SESSION_ID}.json`. These files will orphan and accumulate. While not an immediate failure, it creates minor operational drift. 
4. [ASSUMPTION] [ADVISORY]: The claim that "extra file read... negligible (JSON parse of a small file)" is [SPECULATIVE]. If implemented in Python as proposed, the 30-50ms interpreter startup time per Edit/Write hook invocation dominates the JSON parsing time. A bash implementation using `grep` on a text file would be significantly faster and more aligned with the MOVE-FAST posture.

## Concessions
1. Warning-only (exit 0) approach is a very safe way to test the hypothesis without breaking existing workflows.
2. Exempting new files (`! -f "$FILE_PATH"`) prevents a frustrating circular dependency for file creation.
3. Reusing the existing `config/protected-paths.json` infrastructure minimizes new configuration surface.

## Verdict
APPROVE with the condition that JSON tracking is swapped for a thread-safe append-only text file, and the Grep/Glob requirement is either properly implemented or explicitly dropped from V1 expectations.

---

## Challenger C — Challenges
## Challenges
1. [ASSUMPTION] [ADVISORY]: “Grep/Glob matches count as awareness” is weaker than the stated problem (“edits files it hasn’t read”). A pathname hit from Grep/Glob does not establish the model saw current file contents, so this may reduce warning value and let the original failure mode continue. Risk of the change: low-friction rollout. Risk of not changing: advisory-only rule continues to fail. Given MOVE-FAST and warning-only scope, this is not material, but it should be treated as a deliberate accuracy tradeoff, not equivalent to Read.

2. [UNDER-ENGINEERED] [ADVISORY]: The temp tracking file in `/tmp/buildos-read-tracker-{SESSION_ID}.json` crosses a trust boundary: session state is taken from a world-writable area and then used to influence enforcement. If `CLAUDE_SESSION_ID` is predictable or reused, stale or tampered entries could suppress warnings. In this proposal that only weakens an advisory warning, so it doesn’t rise to material, but the behavior may be less reliable than implied.

3. [ASSUMPTION] [ADVISORY]: The proposal assumes PostToolUse Read and PreToolUse Edit/Write receive canonicalized paths in the same format. If one hook sees relative paths, symlinked paths, or different casing/normalization than the other, warnings may fire incorrectly or be skipped. This affects whether the hook “actually works” more than security.

4. [ASSUMPTION] [ADVISORY]: Session ID fallback to parent PID is only safe if the existing “decompose gate” pattern has demonstrated no collisions across concurrent Claude sessions. Without that evidence, reliability is uncertain. This is especially relevant for `/tmp` state keyed solely by session identifier.

5. [ALTERNATIVE] [ADVISORY]: JSON is not obviously the simplest implementation for a ~50-line hook if all you need is membership checks. A newline-delimited canonical path set may be faster and less failure-prone than repeated JSON parse/update cycles. The current choice is still acceptable, just not clearly justified as the minimal path.

6. [ASSUMPTION] [ADVISORY]: Performance claim “negligible” is ESTIMATED: assumes a small tracker file and low per-session path count; no measurements are provided. That’s fine for a warning-only hook, but it is not EVIDENCED.

## Concessions
- Reuses existing hook points and protected-path scoping instead of inventing new infrastructure.
- Warning-only rollout is appropriately incremental for a behavior-shaping mechanism with possible false positives.
- New-file exemption directly addresses the most obvious bad warning case.

## Verdict
APPROVE — the proposal is a plausible, low-cost behavior nudge that fits existing infrastructure; the main gaps are reliability assumptions, not blockers.

---
