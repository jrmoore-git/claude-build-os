#!/usr/bin/env python3.11
"""Lint SKILL.md files against the canonical sections spec.

Usage: python3.11 scripts/lint_skills.py <path-to-SKILL.md> [--all]
  --all: lint all skills in .claude/skills/*/SKILL.md

Exit 0 if all checks pass. Exit 1 with specific violations on failure.
"""

import re
import sys
from pathlib import Path

# --- Tier 2 heuristics ---
TIER2_PATTERNS = [
    re.compile(r'debate\.py'),
    re.compile(r'scripts/\w+\.py'),
    re.compile(r'\bWrite\b.*tool|\bEdit\b.*tool', re.IGNORECASE),
    re.compile(r'Agent\(|subagent', re.IGNORECASE),
    re.compile(r'--mode\b'),
    re.compile(r'tasks/\S+\.(md|json)|docs/\S+\.md'),
]

STEP_PHASE_RE = re.compile(r'^#{2,3}\s+(Step\s+\d|Phase\s+\d)', re.MULTILINE)

SEMVER_RE = re.compile(r'^\d+\.\d+\.\d+$')

DEBATE_FALLBACK_KEYWORDS = {'fallback', 'unavailable', 'fails', 'error'}


def parse_frontmatter(content):
    """Extract frontmatter dict and body from a SKILL.md file."""
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if not match:
        return {}, content

    fm_text = match.group(1)
    body = content[match.end():]
    fm = {}
    for line in fm_text.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if ':' in line:
            key, _, val = line.partition(':')
            key = key.strip()
            val = val.strip()
            if (val.startswith('"') and val.endswith('"')) or \
               (val.startswith("'") and val.endswith("'")):
                val = val[1:-1]
            if val.startswith('[') and val.endswith(']'):
                inner = val[1:-1]
                val = [v.strip().strip('"').strip("'") for v in inner.split(',') if v.strip()]
            fm[key] = val
    return fm, body


def classify_tier(fm, body):
    """Classify skill tier. Frontmatter override takes precedence."""
    if 'tier' in fm:
        try:
            return int(fm['tier'])
        except (ValueError, TypeError):
            pass

    step_count = len(STEP_PHASE_RE.findall(body))
    if step_count > 3:
        return 2

    for pattern in TIER2_PATTERNS:
        if pattern.search(body):
            return 2

    return 1


def check_debate_fallback(body):
    """Check that debate.py references have fallback language within 5 lines."""
    if 'debate.py' not in body:
        return []

    lines = body.split('\n')
    debate_lines = [i for i, line in enumerate(lines) if 'debate' in line.lower()]

    for idx in debate_lines:
        window_start = max(0, idx - 5)
        window_end = min(len(lines), idx + 6)
        window_text = ' '.join(lines[window_start:window_end]).lower()
        if any(kw in window_text for kw in DEBATE_FALLBACK_KEYWORDS):
            return []

    return [
        "Debate fallback: skill references debate.py but no fallback/unavailable/fails/error "
        "found within 5 lines of any 'debate' mention"
    ]


def lint_skill(filepath):
    """Lint a single SKILL.md. Returns list of violation strings."""
    filepath = Path(filepath)
    if not filepath.exists():
        return [f"File not found: {filepath}"]

    content = filepath.read_text()
    fm, body = parse_frontmatter(content)
    body_lower = body.lower()
    violations = []

    parent_dir = filepath.parent.name

    lint_exempt = fm.get('lint-exempt', [])
    if isinstance(lint_exempt, str):
        lint_exempt = [lint_exempt]

    # --- All-tier checks ---

    # 1. name matches parent directory
    if 'name' not in fm:
        violations.append("Frontmatter: missing 'name' field")
    elif fm['name'] != parent_dir:
        violations.append(f"Frontmatter: name '{fm['name']}' does not match directory '{parent_dir}'")

    # 2. description exists and is not a block scalar
    if 'description' not in fm:
        violations.append("Frontmatter: missing 'description' field")
    else:
        fm_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if fm_match:
            fm_raw = fm_match.group(1)
            desc_line = [l for l in fm_raw.split('\n') if l.strip().startswith('description:')]
            if desc_line:
                after_colon = desc_line[0].split(':', 1)[1].strip()
                if after_colon in ('|', '>', '|+', '>-', '|-', '>+'):
                    violations.append("Frontmatter: description uses block scalar (| or >) -- must be quoted string")

        desc = fm.get('description', '')
        if 'Use when' not in desc:
            violations.append("Frontmatter: description must contain 'Use when' trigger phrase")

    # 3. version field with semver
    if 'version' not in fm:
        violations.append("Frontmatter: missing 'version' field")
    else:
        ver = str(fm['version'])
        if not SEMVER_RE.match(ver):
            violations.append(f"Frontmatter: version '{ver}' is not valid semver (MAJOR.MINOR.PATCH)")

    # 4. Procedure heading
    has_procedure = bool(
        re.search(r'^##\s+Procedure\b', body, re.MULTILINE) or
        re.search(r'^##\s+Steps\b', body, re.MULTILINE) or
        re.search(r'^###\s+Step\s+\d', body, re.MULTILINE)
    )
    if not has_procedure:
        violations.append("Missing procedure section (need ## Procedure, ## Steps, or ### Step N)")

    # 5. Completion status codes
    if 'DONE' not in body:
        violations.append("Missing completion status: 'DONE' not found in body")
    else:
        has_secondary = any(code in body for code in ['DONE_WITH_CONCERNS', 'BLOCKED', 'NEEDS_CONTEXT'])
        if not has_secondary:
            violations.append("Missing completion status: need at least one of DONE_WITH_CONCERNS, BLOCKED, NEEDS_CONTEXT")

    # --- Tier classification ---
    tier = classify_tier(fm, body)

    if tier < 2:
        return violations

    # --- Tier 2 checks ---

    # 6. Safety Rules
    has_safety_heading = bool(re.search(r'^##\s+Safety Rules\b', body, re.MULTILINE))
    if not has_safety_heading:
        violations.append("Tier 2: missing '## Safety Rules' section")
    else:
        safety_match = re.search(
            r'^##\s+Safety Rules\b.*?\n(.*?)(?=\n##\s|\Z)',
            body, re.MULTILINE | re.DOTALL
        )
        if safety_match:
            safety_body = safety_match.group(1)
            if not ('NEVER' in safety_body or 'Do not' in safety_body):
                violations.append("Tier 2: Safety Rules section must contain 'NEVER' or 'Do not'")

    # 7. Output Silence
    if 'output-silence' not in lint_exempt:
        if not re.search(r'output\s+silence', body_lower):
            violations.append(
                "Tier 2: missing Output Silence reference "
                "(add 'Output Silence' text or lint-exempt: [\"output-silence\"] in frontmatter)"
            )

    # 8. Output Format
    has_output_fmt = bool(
        re.search(r'^##\s+Output Format\b', body, re.MULTILINE) or
        re.search(r'^##\s+Output\b', body, re.MULTILINE) or
        re.search(r'^##\s+Deliverable\b', body, re.MULTILINE)
    )
    if not has_output_fmt:
        violations.append("Tier 2: missing output format section (need ## Output Format, ## Output, or ## Deliverable)")

    # 9. Debate fallback
    violations.extend(check_debate_fallback(body))

    return violations


def main():
    args = sys.argv[1:]

    if not args:
        print("Usage: python3.11 scripts/lint_skills.py <SKILL.md> [--all]", file=sys.stderr)
        sys.exit(2)

    if '--all' in args:
        skills_dir = Path('.claude/skills')
        paths = sorted(skills_dir.glob('*/SKILL.md'))
    else:
        paths = [Path(a) for a in args if a != '--all']

    total_violations = 0
    results = []

    for path in paths:
        violations = lint_skill(path)
        skill_name = path.parent.name
        if violations:
            total_violations += len(violations)
            results.append((skill_name, violations))
            for v in violations:
                print(f"FAIL  {skill_name}: {v}")
        else:
            print(f"OK    {skill_name}")

    if total_violations:
        print(f"\n{total_violations} violation(s) in {len(results)} skill(s)")
        sys.exit(1)
    else:
        print(f"\nAll {len(paths)} skill(s) passed")
        sys.exit(0)


if __name__ == '__main__':
    main()
