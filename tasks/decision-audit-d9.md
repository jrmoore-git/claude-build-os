---
decision: D9
original: "Consolidate scattered exploration guidance into Inspect before acting CLAUDE.md rule"
verdict: REVIEW
audit_date: 2026-04-15
models_used: claude-opus-4-6, gemini-3.1-pro, gpt-5.4
---
# D9 Audit

## Original Decision

Rename "Retrieve before planning" → "Inspect before acting" in CLAUDE.md with 3 concrete behavioral rules: (1) read file + context before editing, (2) Grep/Read before answering code questions, (3) never claim "doesn't support" without checking.

Fix 1 (pre-edit hook) deferred because "PreToolUse hook infrastructure doesn't exist yet." Fix 2 (advisory rule) shipped immediately at zero cost.

## Original Rationale

Cross-model refinement found 18+ matches across 7 phrasings of exploration guidance scattered across skills with no consolidated rule and no structural enforcement. The hook was assessed as requiring greenfield infrastructure build — too large for the session. *Date: 2026-04-10.*

## Audit Findings

**3 REVIEW verdicts across three models. All held the same position.**

- **Consolidation (HOLDS):** The rename and 3-rule consolidation were correct. Strictly better than the scattered state. All three reviewers confirmed this. EVIDENCED.

- **Advisory-rule adequacy (DOES NOT HOLD):** The project's own meta-lessons document that advisory rules fail under context pressure. L25 states "advisory rules in 3 places all failed silently." L21 was violated within one turn of being written before D15 structurally fixed it. "Inspect before acting" is the same category of intervention. EVIDENCED.

- **Deferral rationale is obsolete:** D9 stated the deferral blocker was "PreToolUse hook infrastructure doesn't exist yet." Current state: 17 hooks are wired, including `hook-pre-edit-gate.sh` (PreToolUse on Write|Edit). The stated blocker is resolved. EVIDENCED.

- **Gap in what exists vs what D9 wanted:** The current `hook-pre-edit-gate.sh` enforces plan-artifact presence on protected paths — it does not enforce read-before-edit behavior. The exact enforcement D9 envisioned (block edits to files Claude hasn't read) still does not exist. The hook proves the pattern is viable; the specific behavior is unimplemented. EVIDENCED.

- **Alternatives were narrowed too quickly:** The decision framed the space as binary: big hook system or advisory text. Intermediate options (warning-only gate, protected-path enforcement for read-tracking, post-edit audit flagging) were not listed. ESTIMATED.

## Verdict

**REVIEW** — The consolidation holds; the enforcement state is incomplete and the project's own lessons argue it is insufficient. D9 was designed as phase 1 of 2. Phase 2 (structural enforcement) has a clear implementation path that did not exist when D9 was decided. The deferral should be reopened as a concrete task.

**Recommended actions:**
1. Keep the CLAUDE.md "Inspect before acting" rule as-is.
2. Reopen Fix 1 as a scoped task: read-before-edit enforcement on protected paths, warning-only or blocking. Start with the same protected-path scope as `hook-pre-edit-gate.sh` to limit false positives.
3. Evaluate whether a warning-only variant (not blocking) is sufficient before implementing a hard gate — the false-positive surface for new-file creation needs scoping first.

## Risk Assessment

**Risk of keeping advisory-only:** High. The specific failure pattern is documented: advisory rules fail under context pressure, and "inspect before acting" matters most under context pressure (complex sessions, Claude confidently wrong about code behavior). EVIDENCED.

**Risk of building enforcement:** Low-medium. Hook infrastructure is mature. The scoping question — what counts as "read" (same file? same directory? grep match?) and what lookback window — needs design work before implementation. False positive risk for new-file creation is the primary concern. ESTIMATED.

**No spike required** — the need for structural enforcement is not an empirical question. It is answered by L25 and L21. The open question is implementation design, not whether to do it.
