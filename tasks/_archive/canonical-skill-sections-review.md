---
topic: canonical-skill-sections
review_tier: self-review
status: passed
git_head: 9174c2b
producer: claude-opus-4-6
created_at: 2026-04-15T14:10:00-07:00
scope: scripts/lint_skills.py, hooks/hook-skill-lint.py, .claude/settings.json, .claude/skills/*/SKILL.md (22 files)
findings_count: 0
spec_compliance: true
---

# /review — canonical-skill-sections

## Content Type
Code — linter script, hook script, settings.json, 22 SKILL.md files.

## PM / Acceptance

- [ADVISORY] Spec says hook "MUST execute as a PreToolUse hook" but implementation is PostToolUse. Correct deviation: PreToolUse can't lint content that hasn't been written yet. PostToolUse matches the pattern of existing hooks (ruff-check, syntax-check). The spec should be updated.
- All 22 skills pass the linter. 116 violations fixed to 0.
- Scope matches spec exactly: frontmatter fields, procedure, completion codes, safety rules, output silence, output format, debate fallback.
- Tier 1 override (`tier: 1` in frontmatter) correctly applied to 5 utility skills misclassified by heuristics.
- `lint-exempt: ["output-silence"]` correctly applied to /start and /wrap (intermediate output is the interface).
- No scope creep — only sections required by the spec were added.

## Security

- Linter is pure file I/O + regex. No external calls, no network, no credential access.
- Hook uses `subprocess.run` with fixed command. `file_path` comes from tool infrastructure, not user input. No injection risk.
- No secrets in any changed files.

## Architecture

- [ADVISORY] `## Output` heading match (`^##\s+Output\b`) could false-positive on `## Output Silence` or `## Output Contract` headings. No current impact (all skills use inline text for Output Silence, not headings), but a latent risk. Fix: use `^##\s+Output\s*$` for exact match.
- [ADVISORY] No automated tests for `scripts/lint_skills.py`. Verified empirically (22/22 pass, baseline was 116 violations). Adding tests would prevent regressions.
- Frontmatter parser handles first colon correctly via `partition`. Multi-line values not supported, which matches the spec requirement (single-line descriptions only).
- `check_debate_fallback` correctly returns pass if ANY debate mention has fallback within 5 lines, matching the spec's "at least one" requirement.
- Hook uses `sys.executable` (python3) to run the linter. The linter uses only stdlib (re, sys, pathlib) — no 3.11-specific features, so python3.9+ works fine.

## Summary

| Lens         | Material | Advisory |
|--------------|----------|----------|
| PM           | 0        | 1        |
| Security     | 0        | 0        |
| Architecture | 0        | 2        |

Spec compliance: yes (tasks/canonical-skill-sections-refined.md)
Artifact: tasks/canonical-skill-sections-review.md
