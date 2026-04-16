"""Tests for embedded Python functions in hooks/hook-plan-gate.sh.

Functions are copied here because they live inside shell heredocs
and can't be imported directly. If the hook logic changes, these
copies must be updated to match.
"""
import os
import re
import pytest


# ── Extracted from hook-plan-gate.sh Block 1: protected path detection ──────

def glob_to_regex(pattern):
    """Convert a glob pattern to a regex. ** means any depth."""
    parts = pattern.split("**")
    converted = []
    for part in parts:
        segment = ""
        for ch in part:
            if ch == "*":
                segment += "[^/]*"
            elif ch == "?":
                segment += "[^/]"
            elif ch in r"\.+^${}()|[]":
                segment += "\\" + ch
            else:
                segment += ch
        converted.append(segment)
    return "^" + ".*".join(converted) + "$"


def matches_any(path, patterns):
    for pat in patterns:
        regex = glob_to_regex(pat)
        if re.match(regex, path):
            return True
    return False


# ── Extracted from hook-plan-gate.sh Block 2: plan validation ───────────────

def validate_plan(tasks_dir, required_fields):
    """Check tasks_dir for a valid *-plan.md file.

    Returns "yes" if a plan with complete frontmatter is found,
    "no" otherwise. Mirrors the logic in the second heredoc block.
    """
    try:
        entries = sorted(os.listdir(tasks_dir))
    except OSError:
        return "no"

    for f in entries:
        if not f.endswith("-plan.md"):
            continue
        path = os.path.join(tasks_dir, f)
        try:
            content = open(path).read()
        except OSError:
            continue

        if not content.startswith("---"):
            continue
        fm_end = content.find("---", 3)
        if fm_end < 0:
            continue
        frontmatter = content[3:fm_end]

        all_present = True
        for field in required_fields:
            if not re.search(r"^" + re.escape(field) + r"\s*:", frontmatter, re.MULTILINE):
                all_present = False
                break
        if not all_present:
            continue

        ve_match = re.search(r"^verification_evidence\s*:\s*(.+)", frontmatter, re.MULTILINE)
        if ve_match:
            val = ve_match.group(1).strip().strip('"').strip("'")
            if val.upper() == "PENDING":
                continue

        return "yes"

    return "no"


# ── Config values from config/protected-paths.json ──────────────────────────

PROTECTED_GLOBS = [
    "skills/**/*.md",
    "scripts/*_tool.py",
    "scripts/*_pipeline.py",
    ".claude/rules/*.md",
    "hooks/hook-*",
    ".claude/settings.json",
]

EXEMPT_PATTERNS = [
    "tasks/*",
    "docs/*",
    "tests/*",
    "config/*",
    "stores/*",
]

REQUIRED_PLAN_FIELDS = [
    "scope",
    "surfaces_affected",
    "verification_commands",
    "rollback",
    "review_tier",
]


# ── glob_to_regex tests ─────────────────────────────────────────────────────

class TestGlobToRegex:
    def test_simple_star(self):
        regex = glob_to_regex("*.py")
        assert re.match(regex, "foo.py")
        assert re.match(regex, "bar.py")
        assert not re.match(regex, "dir/foo.py")

    def test_star_in_directory(self):
        regex = glob_to_regex("scripts/*_tool.py")
        assert re.match(regex, "scripts/foo_tool.py")
        assert re.match(regex, "scripts/bar_tool.py")
        assert not re.match(regex, "scripts/sub/foo_tool.py")

    def test_double_star(self):
        regex = glob_to_regex("skills/**/*.md")
        assert re.match(regex, "skills/foo/SKILL.md")
        assert re.match(regex, "skills/foo/bar/SKILL.md")
        # ** splits into ["skills/", "/*.md"], joined by ".*"
        # Result: ^skills/.*[^/]*\.md$
        # "skills/SKILL.md" -> "skills/" + "" + "/SKILL.md"
        # .* matches empty, [^/]* matches "SKILL", \.md$ matches .md
        # But the "/" before [^/]* must come from somewhere...
        # Let's just verify actual behavior:
        result = bool(re.match(regex, "skills/SKILL.md"))
        # skills/ .* matches empty, then /[^/]*\.md needs /SKILL.md
        # "skills/" + "" + "/SKILL.md" -- the literal / before * is in the pattern
        # Pattern: skills/**/*.md -> parts = ["skills/", "/*.md"]
        # converted[0] = "skills/" , converted[1] = "/[^/]*\\.md"
        # final: ^skills/.*\/[^/]*\.md$
        # "skills/SKILL.md" doesn't start with / after skills/
        assert not result, "skills/SKILL.md should not match (no intermediate dir)"

    def test_double_star_deep_nesting(self):
        regex = glob_to_regex("skills/**/*.md")
        assert re.match(regex, "skills/a/b/c/SKILL.md")

    def test_question_mark(self):
        regex = glob_to_regex("file?.txt")
        assert re.match(regex, "file1.txt")
        assert re.match(regex, "fileA.txt")
        assert not re.match(regex, "file12.txt")
        assert not re.match(regex, "file.txt")

    def test_dot_escaping(self):
        regex = glob_to_regex("*.md")
        # The dot in .md should be escaped so it doesn't match any char
        assert re.match(regex, "README.md")
        assert not re.match(regex, "READMExmd")

    def test_hooks_pattern(self):
        regex = glob_to_regex("hooks/hook-*")
        assert re.match(regex, "hooks/hook-plan-gate.sh")
        assert re.match(regex, "hooks/hook-review-gate.sh")
        assert not re.match(regex, "hooks/README.md")
        assert not re.match(regex, "hooks/sub/hook-foo")

    def test_exact_file_pattern(self):
        regex = glob_to_regex(".claude/settings.json")
        assert re.match(regex, ".claude/settings.json")
        assert not re.match(regex, ".claude/other.json")
        assert not re.match(regex, "x.claude/settings.json")

    def test_rules_pattern(self):
        regex = glob_to_regex(".claude/rules/*.md")
        assert re.match(regex, ".claude/rules/code-quality.md")
        assert re.match(regex, ".claude/rules/security.md")
        assert not re.match(regex, ".claude/rules/ref/detail.md")

    def test_pipeline_pattern(self):
        regex = glob_to_regex("scripts/*_pipeline.py")
        assert re.match(regex, "scripts/data_pipeline.py")
        assert not re.match(regex, "scripts/data_tool.py")

    def test_special_chars_in_path(self):
        # Brackets, parens, plus should be escaped
        regex = glob_to_regex("dir[1]/*.txt")
        assert re.match(regex, "dir[1]/foo.txt")

    def test_empty_pattern(self):
        regex = glob_to_regex("")
        assert re.match(regex, "")
        assert not re.match(regex, "anything")


# ── matches_any tests ────────────────────────────────────────────────────────

class TestMatchesAny:
    def test_hook_file_matches_protected(self):
        assert matches_any("hooks/hook-plan-gate.sh", PROTECTED_GLOBS)

    def test_tool_script_matches_protected(self):
        assert matches_any("scripts/foo_tool.py", PROTECTED_GLOBS)

    def test_pipeline_script_matches_protected(self):
        assert matches_any("scripts/data_pipeline.py", PROTECTED_GLOBS)

    def test_rule_file_matches_protected(self):
        assert matches_any(".claude/rules/security.md", PROTECTED_GLOBS)

    def test_settings_json_matches_protected(self):
        assert matches_any(".claude/settings.json", PROTECTED_GLOBS)

    def test_skill_file_matches_protected(self):
        assert matches_any("skills/review/SKILL.md", PROTECTED_GLOBS)

    def test_readme_matches_nothing(self):
        assert not matches_any("README.md", PROTECTED_GLOBS)
        assert not matches_any("README.md", EXEMPT_PATTERNS)

    def test_src_file_matches_nothing(self):
        assert not matches_any("src/app.py", PROTECTED_GLOBS)
        assert not matches_any("src/app.py", EXEMPT_PATTERNS)

    def test_tasks_file_matches_exempt(self):
        assert matches_any("tasks/foo-plan.md", EXEMPT_PATTERNS)

    def test_docs_file_matches_exempt(self):
        assert matches_any("docs/project-prd.md", EXEMPT_PATTERNS)

    def test_tests_file_matches_exempt(self):
        assert matches_any("tests/test_foo.py", EXEMPT_PATTERNS)

    def test_config_file_matches_exempt(self):
        assert matches_any("config/protected-paths.json", EXEMPT_PATTERNS)

    def test_stores_file_matches_exempt(self):
        assert matches_any("stores/metrics.db", EXEMPT_PATTERNS)

    def test_empty_patterns_matches_nothing(self):
        assert not matches_any("anything.py", [])

    def test_tasks_not_protected(self):
        assert not matches_any("tasks/foo-plan.md", PROTECTED_GLOBS)

    def test_regular_script_not_protected(self):
        # scripts/debate.py does NOT match *_tool.py or *_pipeline.py
        assert not matches_any("scripts/debate.py", PROTECTED_GLOBS)

    def test_nested_rules_not_protected(self):
        # docs/reference/*.md should not match protected rules
        assert not matches_any("docs/reference/detail.md", PROTECTED_GLOBS)


# ── Combined exempt-then-protected logic (mirrors shell script flow) ─────────

class TestExemptThenProtected:
    """The shell script checks exempt first, then protected.
    A file matching exempt is never flagged as protected."""

    def _is_protected_hit(self, paths):
        """Replicate the shell script's staged-file scan logic."""
        for path in paths:
            path = path.strip()
            if not path:
                continue
            if matches_any(path, EXEMPT_PATTERNS):
                continue
            if matches_any(path, PROTECTED_GLOBS):
                return True
        return False

    def test_only_exempt_files(self):
        assert not self._is_protected_hit(["tasks/foo-plan.md", "docs/readme.md"])

    def test_only_protected_files(self):
        assert self._is_protected_hit(["hooks/hook-plan-gate.sh"])

    def test_mixed_exempt_and_protected(self):
        assert self._is_protected_hit(["tasks/foo.md", "hooks/hook-plan-gate.sh"])

    def test_only_unrelated_files(self):
        assert not self._is_protected_hit(["src/app.py", "README.md"])

    def test_empty_staged(self):
        assert not self._is_protected_hit([])

    def test_blank_lines_ignored(self):
        assert not self._is_protected_hit(["", "  ", "\n"])


# ── Plan validation tests ───────────────────────────────────────────────────

class TestValidatePlan:
    def _write_plan(self, tmp_path, filename, content):
        plan_path = tmp_path / filename
        plan_path.write_text(content)

    def test_valid_plan_all_fields(self, tmp_path):
        self._write_plan(tmp_path, "feature-plan.md", """\
---
scope: Add new widget
surfaces_affected: UI, API
verification_commands: pytest tests/
rollback: git revert HEAD
review_tier: T2
verification_evidence: "Tests pass, manual QA done"
---
# Plan body
""")
        assert validate_plan(str(tmp_path), REQUIRED_PLAN_FIELDS) == "yes"

    def test_missing_scope_field(self, tmp_path):
        self._write_plan(tmp_path, "feature-plan.md", """\
---
surfaces_affected: UI
verification_commands: pytest
rollback: revert
review_tier: T2
verification_evidence: "Tests pass"
---
""")
        assert validate_plan(str(tmp_path), REQUIRED_PLAN_FIELDS) == "no"

    def test_missing_rollback_field(self, tmp_path):
        self._write_plan(tmp_path, "feature-plan.md", """\
---
scope: stuff
surfaces_affected: UI
verification_commands: pytest
review_tier: T2
verification_evidence: "Tests pass"
---
""")
        assert validate_plan(str(tmp_path), REQUIRED_PLAN_FIELDS) == "no"

    def test_missing_review_tier_field(self, tmp_path):
        self._write_plan(tmp_path, "feature-plan.md", """\
---
scope: stuff
surfaces_affected: UI
verification_commands: pytest
rollback: revert
verification_evidence: "Tests pass"
---
""")
        assert validate_plan(str(tmp_path), REQUIRED_PLAN_FIELDS) == "no"

    def test_verification_evidence_pending(self, tmp_path):
        self._write_plan(tmp_path, "feature-plan.md", """\
---
scope: stuff
surfaces_affected: UI
verification_commands: pytest
rollback: revert
review_tier: T2
verification_evidence: PENDING
---
""")
        assert validate_plan(str(tmp_path), REQUIRED_PLAN_FIELDS) == "no"

    def test_verification_evidence_pending_quoted(self, tmp_path):
        self._write_plan(tmp_path, "feature-plan.md", """\
---
scope: stuff
surfaces_affected: UI
verification_commands: pytest
rollback: revert
review_tier: T2
verification_evidence: "PENDING"
---
""")
        assert validate_plan(str(tmp_path), REQUIRED_PLAN_FIELDS) == "no"

    def test_verification_evidence_pending_case_insensitive(self, tmp_path):
        self._write_plan(tmp_path, "feature-plan.md", """\
---
scope: stuff
surfaces_affected: UI
verification_commands: pytest
rollback: revert
review_tier: T2
verification_evidence: Pending
---
""")
        assert validate_plan(str(tmp_path), REQUIRED_PLAN_FIELDS) == "no"

    def test_verification_evidence_real_value(self, tmp_path):
        self._write_plan(tmp_path, "feature-plan.md", """\
---
scope: stuff
surfaces_affected: UI
verification_commands: pytest
rollback: revert
review_tier: T2
verification_evidence: "All tests pass"
---
""")
        assert validate_plan(str(tmp_path), REQUIRED_PLAN_FIELDS) == "yes"

    def test_no_frontmatter(self, tmp_path):
        self._write_plan(tmp_path, "feature-plan.md", """\
# Just a plan with no frontmatter
Some content here.
""")
        assert validate_plan(str(tmp_path), REQUIRED_PLAN_FIELDS) == "no"

    def test_incomplete_frontmatter_no_closing(self, tmp_path):
        self._write_plan(tmp_path, "feature-plan.md", """\
---
scope: stuff
surfaces_affected: UI
verification_commands: pytest
rollback: revert
review_tier: T2
verification_evidence: "done"
This frontmatter never closes
""")
        assert validate_plan(str(tmp_path), REQUIRED_PLAN_FIELDS) == "no"

    def test_no_plan_files(self, tmp_path):
        # Write a non-plan file
        (tmp_path / "notes.md").write_text("not a plan")
        assert validate_plan(str(tmp_path), REQUIRED_PLAN_FIELDS) == "no"

    def test_empty_tasks_dir(self, tmp_path):
        assert validate_plan(str(tmp_path), REQUIRED_PLAN_FIELDS) == "no"

    def test_nonexistent_tasks_dir(self, tmp_path):
        assert validate_plan(str(tmp_path / "nonexistent"), REQUIRED_PLAN_FIELDS) == "no"

    def test_multiple_plans_first_invalid_second_valid(self, tmp_path):
        # First plan is invalid (missing fields)
        self._write_plan(tmp_path, "alpha-plan.md", """\
---
scope: partial
---
""")
        # Second plan is valid
        self._write_plan(tmp_path, "beta-plan.md", """\
---
scope: stuff
surfaces_affected: UI
verification_commands: pytest
rollback: revert
review_tier: T2
verification_evidence: "done"
---
""")
        assert validate_plan(str(tmp_path), REQUIRED_PLAN_FIELDS) == "yes"

    def test_multiple_plans_all_invalid(self, tmp_path):
        self._write_plan(tmp_path, "alpha-plan.md", """\
---
scope: partial
---
""")
        self._write_plan(tmp_path, "beta-plan.md", """\
---
scope: other
surfaces_affected: UI
verification_commands: pytest
rollback: revert
review_tier: T2
verification_evidence: PENDING
---
""")
        assert validate_plan(str(tmp_path), REQUIRED_PLAN_FIELDS) == "no"

    def test_verification_evidence_not_required_field_but_checked(self, tmp_path):
        """verification_evidence is not in required_plan_fields but is
        checked separately. A plan without it should still pass."""
        self._write_plan(tmp_path, "feature-plan.md", """\
---
scope: stuff
surfaces_affected: UI
verification_commands: pytest
rollback: revert
review_tier: T2
---
""")
        assert validate_plan(str(tmp_path), REQUIRED_PLAN_FIELDS) == "yes"

    def test_field_with_extra_whitespace(self, tmp_path):
        self._write_plan(tmp_path, "feature-plan.md", """\
---
scope  :  stuff
surfaces_affected :UI
verification_commands:  pytest
rollback : revert
review_tier : T2
verification_evidence : "Tests pass"
---
""")
        assert validate_plan(str(tmp_path), REQUIRED_PLAN_FIELDS) == "yes"

    def test_plan_file_not_matching_suffix(self, tmp_path):
        """Files that don't end in -plan.md are ignored."""
        self._write_plan(tmp_path, "feature-design.md", """\
---
scope: stuff
surfaces_affected: UI
verification_commands: pytest
rollback: revert
review_tier: T2
verification_evidence: "done"
---
""")
        assert validate_plan(str(tmp_path), REQUIRED_PLAN_FIELDS) == "no"

    def test_frontmatter_with_body_content(self, tmp_path):
        self._write_plan(tmp_path, "feature-plan.md", """\
---
scope: Add new widget
surfaces_affected: UI, API
verification_commands: pytest tests/
rollback: git revert HEAD
review_tier: T2
verification_evidence: "Tests pass"
---

# Implementation Plan

## Steps
1. Do the thing
2. Test the thing
""")
        assert validate_plan(str(tmp_path), REQUIRED_PLAN_FIELDS) == "yes"

    def test_empty_required_fields_list(self, tmp_path):
        """With no required fields, any frontmatter-bearing plan passes."""
        self._write_plan(tmp_path, "feature-plan.md", """\
---
anything: goes
---
""")
        assert validate_plan(str(tmp_path), []) == "yes"
