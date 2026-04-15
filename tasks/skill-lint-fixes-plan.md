---
scope: "Fix 5 SKILL.md files to pass lint_skills.py linter"
surfaces_affected:
  - ".claude/skills/simulate/SKILL.md"
  - ".claude/skills/start/SKILL.md"
  - ".claude/skills/sync/SKILL.md"
  - ".claude/skills/think/SKILL.md"
  - ".claude/skills/wrap/SKILL.md"
verification_commands:
  - "python3.11 scripts/lint_skills.py .claude/skills/simulate/SKILL.md"
  - "python3.11 scripts/lint_skills.py .claude/skills/start/SKILL.md"
  - "python3.11 scripts/lint_skills.py .claude/skills/sync/SKILL.md"
  - "python3.11 scripts/lint_skills.py .claude/skills/think/SKILL.md"
  - "python3.11 scripts/lint_skills.py .claude/skills/wrap/SKILL.md"
rollback: "git checkout HEAD -- .claude/skills/simulate/SKILL.md .claude/skills/start/SKILL.md .claude/skills/sync/SKILL.md .claude/skills/think/SKILL.md .claude/skills/wrap/SKILL.md"
review_tier: "T0"
verification_evidence: "All 5 skills pass lint_skills.py with exit 0"
---

# Plan: Fix SKILL.md Linter Violations

Add missing frontmatter fields (version, Use when in description), procedure sections, completion status sections, safety rules, output silence references, output format sections, and debate fallback text to 5 skills: simulate, start, sync, think, wrap.
