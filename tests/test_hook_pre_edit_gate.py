"""Tests for embedded Python functions in hooks/hook-pre-edit-gate.sh.

The hook has two Python blocks:
  Block 1: Protected path classification (fnmatch with ** expansion)
  Block 2: Plan artifact matching (frontmatter parsing + surface matching)

Functions are copied here because they live inside shell heredocs.
"""
import fnmatch
import json
import os
import re
import time

import pytest


# ── Extracted from hook-pre-edit-gate.sh Block 1 ──────────────────────────────

def check_protected(rel, config):
    """Classify a relative path as protected or not.

    Returns "yes" if the path is protected, "no" otherwise.
    Mirrors the embedded Python in hook-pre-edit-gate.sh exactly.
    """
    # Self-check: this hook is always protected
    if rel == "scripts/hook-pre-edit-gate.sh":
        return "yes"

    if config is None:
        # Config missing/broken — fail open
        return "no"

    # Exempt paths — always pass
    for pat in config.get("exempt_patterns", []):
        if fnmatch.fnmatch(rel, pat):
            return "no"

    # Protected globs — block if matched
    for pat in config.get("protected_globs", []):
        if "**" in pat:
            base, rest = pat.split("**", 1)
            for depth in range(4):
                expanded = base + ("*/" * depth) + rest.lstrip("/")
                if fnmatch.fnmatch(rel, expanded):
                    return "yes"
        elif fnmatch.fnmatch(rel, pat):
            return "yes"

    return "no"


# ── Extracted from hook-pre-edit-gate.sh Block 2 ──────────────────────────────

def parse_frontmatter(text):
    """Parse YAML frontmatter into dict. Handles scalar values and YAML lists.
    Returns None on any parse failure (fail closed)."""
    if not text.startswith("---"):
        return None
    end = text.find("---", 3)
    if end < 0:
        return None
    result = {}
    current_key = None
    for line in text[3:end].splitlines():
        # YAML list item under current key
        if line.startswith("  - ") and current_key is not None:
            if not isinstance(result[current_key], list):
                result[current_key] = []
            result[current_key].append(line[4:].strip().strip("'\""))
            continue
        # Key: value line
        m = re.match(r'^([a-z_]+)\s*:\s*(.*)', line)
        if m:
            current_key = m.group(1)
            val = m.group(2).strip().strip("'\"")
            result[current_key] = val if val else []
            continue
        # Anything else resets list accumulation
        if line.strip():
            current_key = None
    return result


def extract_surfaces(fm):
    """Extract surfaces_affected as a list of path strings. Returns [] on failure."""
    sa = fm.get("surfaces_affected")
    if not sa:
        return []
    if isinstance(sa, str):
        return [e.strip() for e in sa.split(",") if e.strip()]
    if isinstance(sa, list):
        return [str(e).strip() for e in sa if str(e).strip()]
    return []


def find_matching_plan(tasks_dir, rel, now=None):
    """Check tasks_dir for a *-plan.md with matching surfaces_affected.

    Returns "yes" if a matching plan is found, "no" otherwise.
    Mirrors the embedded Python in hook-pre-edit-gate.sh exactly.
    """
    if now is None:
        now = time.time()
    MAX_AGE = 86400  # 24 hours

    if not os.path.isdir(tasks_dir):
        return "no"

    for fname in sorted(os.listdir(tasks_dir)):
        if not fname.endswith("-plan.md"):
            continue
        path = os.path.join(tasks_dir, fname)
        if not os.path.isfile(path):
            continue

        # 24-hour modification window
        try:
            mtime = os.path.getmtime(path)
        except OSError:
            continue
        if (now - mtime) > MAX_AGE:
            continue

        # Parse frontmatter (fail closed)
        try:
            content = open(path).read()
        except OSError:
            continue
        fm = parse_frontmatter(content)
        if fm is None:
            continue

        # Strict matching: exact path or fnmatch glob only
        for entry in extract_surfaces(fm):
            if entry == rel or fnmatch.fnmatch(rel, entry):
                return "yes"

    return "no"


# ── Fixtures ──────────────────────────────────────────────────────────────────

REAL_CONFIG = {
    "protected_globs": [
        "skills/**/*.md",
        "scripts/*_tool.py",
        "scripts/*_pipeline.py",
        ".claude/rules/*.md",
        "hooks/hook-*",
        ".claude/settings.json",
    ],
    "exempt_patterns": [
        "tasks/*",
        "docs/*",
        "tests/*",
        "config/*",
        "stores/*",
    ],
}


# ── Block 1: Protected path classification ────────────────────────────────────


class TestCheckProtected:
    """Tests for check_protected() — the path classification logic."""

    def test_self_check_always_protected(self):
        """The hook script itself is always protected, regardless of config."""
        assert check_protected("scripts/hook-pre-edit-gate.sh", {}) == "yes"
        assert check_protected("scripts/hook-pre-edit-gate.sh", None) == "yes"
        assert check_protected("scripts/hook-pre-edit-gate.sh", REAL_CONFIG) == "yes"

    def test_exempt_tasks(self):
        assert check_protected("tasks/foo.md", REAL_CONFIG) == "no"

    def test_exempt_tests(self):
        assert check_protected("tests/test_foo.py", REAL_CONFIG) == "no"

    def test_exempt_docs(self):
        assert check_protected("docs/how-it-works.md", REAL_CONFIG) == "no"

    def test_exempt_config(self):
        assert check_protected("config/debate-models.json", REAL_CONFIG) == "no"

    def test_exempt_stores(self):
        assert check_protected("stores/metrics.db", REAL_CONFIG) == "no"

    def test_exempt_checked_before_protected(self):
        """Exempt patterns take precedence over protected globs.
        tasks/* is exempt even though it could match a hypothetical glob."""
        config = {
            "exempt_patterns": ["tasks/*"],
            "protected_globs": ["tasks/*.md"],
        }
        assert check_protected("tasks/foo.md", config) == "no"

    def test_protected_hook_file(self):
        assert check_protected("hooks/hook-plan-gate.sh", REAL_CONFIG) == "yes"

    def test_protected_hook_python(self):
        assert check_protected("hooks/hook-intent-router.py", REAL_CONFIG) == "yes"

    def test_protected_skill_depth_1(self):
        """skills/**/*.md matches skills/start/SKILL.md (depth 1)."""
        assert check_protected("skills/start/SKILL.md", REAL_CONFIG) == "yes"

    def test_protected_skill_depth_2(self):
        """skills/**/*.md matches skills/deep/nested/SKILL.md (depth 2)."""
        assert check_protected("skills/deep/nested/SKILL.md", REAL_CONFIG) == "yes"

    def test_protected_skill_depth_0(self):
        """skills/**/*.md matches skills/README.md (depth 0)."""
        assert check_protected("skills/README.md", REAL_CONFIG) == "yes"

    def test_protected_skill_depth_3(self):
        """skills/**/*.md matches at depth 3 (max expansion)."""
        assert check_protected("skills/a/b/c/SKILL.md", REAL_CONFIG) == "yes"

    def test_protected_skill_depth_4_still_matches(self):
        """fnmatch * matches across /, so depth-0 expansion skills/*.md
        already matches skills/a/b/c/d/SKILL.md."""
        assert check_protected("skills/a/b/c/d/SKILL.md", REAL_CONFIG) == "yes"

    def test_protected_rules(self):
        assert check_protected(".claude/rules/security.md", REAL_CONFIG) == "yes"

    def test_protected_settings(self):
        assert check_protected(".claude/settings.json", REAL_CONFIG) == "yes"

    def test_protected_tool_script(self):
        assert check_protected("scripts/foo_tool.py", REAL_CONFIG) == "yes"

    def test_protected_pipeline_script(self):
        assert check_protected("scripts/foo_pipeline.py", REAL_CONFIG) == "yes"

    def test_not_protected_readme(self):
        assert check_protected("README.md", REAL_CONFIG) == "no"

    def test_not_protected_src(self):
        assert check_protected("src/app.py", REAL_CONFIG) == "no"

    def test_not_protected_random_script(self):
        """scripts/debate.py is not *_tool.py or *_pipeline.py."""
        assert check_protected("scripts/debate.py", REAL_CONFIG) == "no"

    def test_config_none_fail_open(self):
        """Config missing/broken → fail open (don't block all edits)."""
        assert check_protected("hooks/hook-plan-gate.sh", None) == "no"

    def test_config_empty_fail_open(self):
        """Empty config → nothing protected (except self-check)."""
        assert check_protected("hooks/hook-plan-gate.sh", {}) == "no"

    def test_config_no_exempt_patterns(self):
        """Config with protected globs but no exempt patterns."""
        config = {"protected_globs": ["hooks/hook-*"]}
        assert check_protected("hooks/hook-plan-gate.sh", config) == "yes"

    def test_config_no_protected_globs(self):
        """Config with exempt patterns but no protected globs."""
        config = {"exempt_patterns": ["tasks/*"]}
        assert check_protected("hooks/hook-plan-gate.sh", config) == "no"


# ── Block 2: parse_frontmatter() ──────────────────────────────────────────────


class TestParseFrontmatter:
    """Tests for parse_frontmatter() — YAML frontmatter parsing."""

    def test_valid_scalars(self):
        text = '---\nscope: "test scope"\nreview_tier: T1\n---\nBody text'
        result = parse_frontmatter(text)
        assert result == {"scope": "test scope", "review_tier": "T1"}

    def test_valid_list(self):
        text = (
            "---\n"
            "surfaces_affected:\n"
            "  - hooks/hook-*.py\n"
            "  - scripts/foo.py\n"
            "---\n"
        )
        result = parse_frontmatter(text)
        assert result["surfaces_affected"] == ["hooks/hook-*.py", "scripts/foo.py"]

    def test_mixed_scalars_and_lists(self):
        text = (
            "---\n"
            "scope: hooks cleanup\n"
            "surfaces_affected:\n"
            "  - hooks/hook-*.py\n"
            "  - scripts/foo.py\n"
            "review_tier: T2\n"
            "---\n"
        )
        result = parse_frontmatter(text)
        assert result["scope"] == "hooks cleanup"
        assert result["surfaces_affected"] == ["hooks/hook-*.py", "scripts/foo.py"]
        assert result["review_tier"] == "T2"

    def test_no_opening_dashes(self):
        text = "scope: test\n---\n"
        assert parse_frontmatter(text) is None

    def test_no_closing_dashes(self):
        text = "---\nscope: test\n"
        assert parse_frontmatter(text) is None

    def test_empty_frontmatter(self):
        text = "---\n---\nBody"
        result = parse_frontmatter(text)
        assert result == {}

    def test_quoted_values_stripped(self):
        text = '---\nscope: "quoted value"\n---\n'
        result = parse_frontmatter(text)
        assert result["scope"] == "quoted value"

    def test_single_quoted_values_stripped(self):
        text = "---\nscope: 'quoted value'\n---\n"
        result = parse_frontmatter(text)
        assert result["scope"] == "quoted value"

    def test_key_with_empty_value_becomes_list(self):
        """A key with no inline value (like surfaces_affected:) becomes []."""
        text = "---\nsurfaces_affected:\n---\n"
        result = parse_frontmatter(text)
        assert result["surfaces_affected"] == []

    def test_list_items_stripped(self):
        text = (
            "---\n"
            "surfaces_affected:\n"
            "  - 'hooks/hook-*.py'\n"
            "  - \"scripts/foo.py\"\n"
            "---\n"
        )
        result = parse_frontmatter(text)
        assert result["surfaces_affected"] == ["hooks/hook-*.py", "scripts/foo.py"]

    def test_non_matching_line_resets_list(self):
        """A line that's not a key or list item resets current_key."""
        text = (
            "---\n"
            "surfaces_affected:\n"
            "  - hooks/hook-*.py\n"
            "RANDOM JUNK\n"
            "  - should/not/be/added\n"
            "---\n"
        )
        result = parse_frontmatter(text)
        # "RANDOM JUNK" resets current_key to None
        # The second list item has no current_key, so it's skipped
        assert result["surfaces_affected"] == ["hooks/hook-*.py"]

    def test_body_after_closing_dashes_ignored(self):
        text = "---\nscope: test\n---\nThis is body text\nscope: wrong\n"
        result = parse_frontmatter(text)
        assert result == {"scope": "test"}

    def test_key_regex_requires_lowercase(self):
        """Only lowercase+underscore keys match the regex [a-z_]+."""
        text = "---\nMyKey: value\n---\n"
        result = parse_frontmatter(text)
        # MyKey doesn't match ^[a-z_]+, so it's a non-matching line
        assert result == {}


# ── Block 2: extract_surfaces() ───────────────────────────────────────────────


class TestExtractSurfaces:
    """Tests for extract_surfaces() — surface extraction from frontmatter."""

    def test_string_comma_separated(self):
        fm = {"surfaces_affected": "hooks/hook-*.py, scripts/foo.py"}
        assert extract_surfaces(fm) == ["hooks/hook-*.py", "scripts/foo.py"]

    def test_list(self):
        fm = {"surfaces_affected": ["hooks/hook-*.py", "scripts/foo.py"]}
        assert extract_surfaces(fm) == ["hooks/hook-*.py", "scripts/foo.py"]

    def test_missing_key(self):
        assert extract_surfaces({}) == []

    def test_empty_string(self):
        fm = {"surfaces_affected": ""}
        assert extract_surfaces(fm) == []

    def test_empty_list(self):
        fm = {"surfaces_affected": []}
        assert extract_surfaces(fm) == []

    def test_single_string(self):
        fm = {"surfaces_affected": "hooks/hook-plan-gate.sh"}
        assert extract_surfaces(fm) == ["hooks/hook-plan-gate.sh"]

    def test_whitespace_trimmed(self):
        fm = {"surfaces_affected": "  hooks/hook-*.py ,  scripts/foo.py  "}
        assert extract_surfaces(fm) == ["hooks/hook-*.py", "scripts/foo.py"]

    def test_list_with_whitespace(self):
        fm = {"surfaces_affected": ["  hooks/hook-*.py  ", "  scripts/foo.py  "]}
        assert extract_surfaces(fm) == ["hooks/hook-*.py", "scripts/foo.py"]

    def test_none_value(self):
        fm = {"surfaces_affected": None}
        assert extract_surfaces(fm) == []


# ── Block 2: find_matching_plan() (integration) ──────────────────────────────


class TestFindMatchingPlan:
    """Integration tests for find_matching_plan() using tmp_path."""

    def _write_plan(self, tasks_dir, name, content, age_seconds=0):
        """Write a plan file and optionally backdate its mtime."""
        path = os.path.join(tasks_dir, name)
        with open(path, "w") as f:
            f.write(content)
        if age_seconds > 0:
            mtime = time.time() - age_seconds
            os.utime(path, (mtime, mtime))
        return path

    def test_matching_exact_surface(self, tmp_path):
        tasks = str(tmp_path)
        self._write_plan(tasks, "foo-plan.md", (
            "---\n"
            "scope: test\n"
            "surfaces_affected:\n"
            "  - hooks/hook-plan-gate.sh\n"
            "---\n"
        ))
        assert find_matching_plan(tasks, "hooks/hook-plan-gate.sh") == "yes"

    def test_matching_fnmatch_surface(self, tmp_path):
        tasks = str(tmp_path)
        self._write_plan(tasks, "bar-plan.md", (
            "---\n"
            "scope: hooks\n"
            "surfaces_affected:\n"
            "  - hooks/hook-*\n"
            "---\n"
        ))
        assert find_matching_plan(tasks, "hooks/hook-plan-gate.sh") == "yes"

    def test_non_matching_surface(self, tmp_path):
        tasks = str(tmp_path)
        self._write_plan(tasks, "baz-plan.md", (
            "---\n"
            "scope: scripts\n"
            "surfaces_affected:\n"
            "  - scripts/foo_tool.py\n"
            "---\n"
        ))
        assert find_matching_plan(tasks, "hooks/hook-plan-gate.sh") == "no"

    def test_plan_older_than_24h(self, tmp_path):
        tasks = str(tmp_path)
        self._write_plan(tasks, "old-plan.md", (
            "---\n"
            "scope: test\n"
            "surfaces_affected:\n"
            "  - hooks/hook-plan-gate.sh\n"
            "---\n"
        ), age_seconds=90000)  # ~25 hours
        assert find_matching_plan(tasks, "hooks/hook-plan-gate.sh") == "no"

    def test_plan_just_within_24h(self, tmp_path):
        tasks = str(tmp_path)
        self._write_plan(tasks, "recent-plan.md", (
            "---\n"
            "scope: test\n"
            "surfaces_affected:\n"
            "  - hooks/hook-plan-gate.sh\n"
            "---\n"
        ), age_seconds=86000)  # Just under 24h
        assert find_matching_plan(tasks, "hooks/hook-plan-gate.sh") == "yes"

    def test_plan_without_frontmatter(self, tmp_path):
        tasks = str(tmp_path)
        self._write_plan(tasks, "nofm-plan.md", "No frontmatter here\n")
        assert find_matching_plan(tasks, "hooks/hook-plan-gate.sh") == "no"

    def test_plan_without_surfaces(self, tmp_path):
        tasks = str(tmp_path)
        self._write_plan(tasks, "nosurface-plan.md", (
            "---\n"
            "scope: test\n"
            "review_tier: T1\n"
            "---\n"
        ))
        assert find_matching_plan(tasks, "hooks/hook-plan-gate.sh") == "no"

    def test_no_plan_files(self, tmp_path):
        tasks = str(tmp_path)
        # Write a non-plan file
        with open(os.path.join(tasks, "foo-challenge.md"), "w") as f:
            f.write("---\nscope: test\n---\n")
        assert find_matching_plan(tasks, "hooks/hook-plan-gate.sh") == "no"

    def test_nonexistent_tasks_dir(self, tmp_path):
        assert find_matching_plan(str(tmp_path / "nonexistent"), "hooks/hook-plan-gate.sh") == "no"

    def test_multiple_plans_one_matches(self, tmp_path):
        tasks = str(tmp_path)
        self._write_plan(tasks, "alpha-plan.md", (
            "---\n"
            "scope: scripts\n"
            "surfaces_affected:\n"
            "  - scripts/foo_tool.py\n"
            "---\n"
        ))
        self._write_plan(tasks, "beta-plan.md", (
            "---\n"
            "scope: hooks\n"
            "surfaces_affected:\n"
            "  - hooks/hook-*\n"
            "---\n"
        ))
        assert find_matching_plan(tasks, "hooks/hook-plan-gate.sh") == "yes"

    def test_comma_separated_surfaces_match(self, tmp_path):
        tasks = str(tmp_path)
        self._write_plan(tasks, "combo-plan.md", (
            "---\n"
            "scope: mixed\n"
            "surfaces_affected: hooks/hook-*, scripts/foo_tool.py\n"
            "---\n"
        ))
        assert find_matching_plan(tasks, "hooks/hook-plan-gate.sh") == "yes"

    def test_only_plan_md_suffix_counts(self, tmp_path):
        """Files like *-proposal.md or *-challenge.md are ignored."""
        tasks = str(tmp_path)
        self._write_plan(tasks, "foo-proposal.md", (
            "---\n"
            "scope: test\n"
            "surfaces_affected:\n"
            "  - hooks/hook-*\n"
            "---\n"
        ))
        assert find_matching_plan(tasks, "hooks/hook-plan-gate.sh") == "no"

    def test_now_parameter_overrides_time(self, tmp_path):
        """Passing now= allows deterministic time testing."""
        tasks = str(tmp_path)
        path = self._write_plan(tasks, "timed-plan.md", (
            "---\n"
            "scope: test\n"
            "surfaces_affected:\n"
            "  - hooks/hook-plan-gate.sh\n"
            "---\n"
        ))
        # Get actual mtime of the file we just wrote
        mtime = os.path.getmtime(path)
        # Within 24h from the file's perspective
        assert find_matching_plan(tasks, "hooks/hook-plan-gate.sh", now=mtime + 1000) == "yes"
        # Beyond 24h
        assert find_matching_plan(tasks, "hooks/hook-plan-gate.sh", now=mtime + 90000) == "no"

    def test_frontmatter_no_closing_dashes(self, tmp_path):
        """Plan with unclosed frontmatter is skipped (fail closed)."""
        tasks = str(tmp_path)
        self._write_plan(tasks, "bad-plan.md", (
            "---\n"
            "scope: test\n"
            "surfaces_affected:\n"
            "  - hooks/hook-*\n"
        ))
        assert find_matching_plan(tasks, "hooks/hook-plan-gate.sh") == "no"
