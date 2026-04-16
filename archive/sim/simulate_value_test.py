#!/usr/bin/env python3
"""simulate_value_test.py — Test /simulate smoke-test mode against all skills.

Extracts bash blocks from every SKILL.md, classifies them (skip/run),
executes runnable blocks, and reports what the mode actually catches.
"""

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = PROJECT_ROOT / ".claude" / "skills"

# From /simulate SKILL.md safety filters
DENYLIST = [
    r'rm\s+-rf\b', r'rm\s+-r\b',
    r'git\s+push', r'git\s+reset\s+--hard', r'git\s+checkout\s+\.', r'git\s+clean',
    r'DROP\s+TABLE', r'DELETE\s+FROM', r'TRUNCATE',
    r'sudo\b',
    r'\beval\b', r'\bsource\b',
    r'pip\s+install', r'npm\s+install', r'brew\s+install',
]

PLACEHOLDER_PATTERNS = [
    r'<[a-z_-]+>',  # <topic>, <TOPIC>, <target>
    r'\$\{[A-Z_]*UNDEFINED[A-Z_]*\}',
    r'"query here"', r'"your query"', r'"search term"',
]

# Patterns that indicate the block needs runtime context
RUNTIME_CONTEXT = [
    r'\$TMPFILE', r'\$SIM_WORKSPACE', r'\$SCENARIO_FILE',
    r'\$EVAL_INPUT', r'\$WRAPPED_DOC', r'\$PREFLIGHT_CONTEXT',
    r'\$PROPOSAL_PATH', r'\$CONTEXT',
]


def extract_bash_blocks(content):
    """Extract fenced bash blocks from markdown."""
    blocks = []
    in_block = False
    current = []
    section = "unknown"

    for line in content.split('\n'):
        if line.startswith('## ') or line.startswith('### '):
            section = line.lstrip('#').strip()
        if line.strip() == '```bash':
            in_block = True
            current = []
        elif line.strip() == '```' and in_block:
            in_block = False
            blocks.append({'code': '\n'.join(current), 'section': section})
        elif in_block:
            current.append(line)

    return blocks


def classify_block(code):
    """Classify a bash block as skip/deny/runtime/runnable."""
    # Denylist
    for pattern in DENYLIST:
        if re.search(pattern, code):
            return 'DENIED', f'matches denylist: {pattern}'

    # Placeholder check
    for pattern in PLACEHOLDER_PATTERNS:
        if re.search(pattern, code):
            return 'PLACEHOLDER', f'unresolved placeholder: {pattern}'

    # Runtime context (variables set during skill execution)
    for pattern in RUNTIME_CONTEXT:
        if re.search(pattern, code):
            return 'RUNTIME', f'needs runtime variable: {pattern}'

    return 'RUNNABLE', None


def run_block(code, timeout=15):
    """Run a bash block and return (exit_code, stdout, stderr)."""
    # Scrub secrets
    env = os.environ.copy()
    for key in list(env.keys()):
        if any(s in key for s in ['KEY', 'SECRET', 'TOKEN', 'PASSWORD', 'CREDENTIAL', '_DSN']):
            del env[key]

    try:
        result = subprocess.run(
            ['bash', '-c', code],
            capture_output=True, text=True,
            timeout=timeout, cwd=str(PROJECT_ROOT), env=env
        )
        return result.returncode, result.stdout[-500:], result.stderr[-200:]
    except subprocess.TimeoutExpired:
        return -1, '', 'TIMEOUT'
    except Exception as e:
        return -2, '', str(e)


def main():
    skills = sorted(p.parent.name for p in SKILLS_DIR.glob("*/SKILL.md"))
    print(f"Testing /simulate smoke-test against {len(skills)} skills\n", file=sys.stderr)

    totals = {'skills': 0, 'blocks': 0, 'DENIED': 0, 'PLACEHOLDER': 0,
              'RUNTIME': 0, 'RUNNABLE': 0, 'PASS': 0, 'FAIL': 0, 'TIMEOUT': 0}
    findings = []  # Actual issues found
    skill_details = []

    for skill_name in skills:
        skill_path = SKILLS_DIR / skill_name / "SKILL.md"
        content = skill_path.read_text()
        blocks = extract_bash_blocks(content)

        totals['skills'] += 1
        totals['blocks'] += len(blocks)

        skill_result = {
            'skill': skill_name,
            'total_blocks': len(blocks),
            'classified': {'DENIED': 0, 'PLACEHOLDER': 0, 'RUNTIME': 0, 'RUNNABLE': 0},
            'run_results': {'PASS': 0, 'FAIL': 0, 'TIMEOUT': 0},
            'failures': [],
        }

        for i, block in enumerate(blocks):
            category, reason = classify_block(block['code'])
            skill_result['classified'][category] = skill_result['classified'].get(category, 0) + 1
            totals[category] += 1

            if category == 'RUNNABLE':
                exit_code, stdout, stderr = run_block(block['code'])
                if exit_code == 0:
                    skill_result['run_results']['PASS'] += 1
                    totals['PASS'] += 1
                elif exit_code == -1:
                    skill_result['run_results']['TIMEOUT'] += 1
                    totals['TIMEOUT'] += 1
                    skill_result['failures'].append({
                        'block': i + 1, 'section': block['section'],
                        'code': block['code'][:100], 'error': 'TIMEOUT'
                    })
                else:
                    skill_result['run_results']['FAIL'] += 1
                    totals['FAIL'] += 1
                    skill_result['failures'].append({
                        'block': i + 1, 'section': block['section'],
                        'code': block['code'][:100], 'error': stderr[:150]
                    })
                    findings.append({
                        'skill': skill_name, 'block': i + 1,
                        'section': block['section'],
                        'code': block['code'][:80],
                        'error': stderr[:100],
                    })

        skill_details.append(skill_result)

        # Progress
        passed = skill_result['run_results']['PASS']
        failed = skill_result['run_results']['FAIL']
        skipped = skill_result['classified']['DENIED'] + skill_result['classified']['PLACEHOLDER'] + skill_result['classified']['RUNTIME']
        print(f"  /{skill_name}: {len(blocks)} blocks, {passed} pass, {failed} fail, {skipped} skip",
              file=sys.stderr)

    # Summary
    runnable_pct = (totals['RUNNABLE'] / totals['blocks'] * 100) if totals['blocks'] else 0
    skip_pct = 100 - runnable_pct

    print(f"\n{'='*60}", file=sys.stderr)
    print(f"RESULTS: /simulate smoke-test value assessment", file=sys.stderr)
    print(f"{'='*60}", file=sys.stderr)
    print(f"Skills tested:    {totals['skills']}", file=sys.stderr)
    print(f"Total bash blocks: {totals['blocks']}", file=sys.stderr)
    print(f"", file=sys.stderr)
    print(f"Classification:", file=sys.stderr)
    print(f"  DENIED (denylist):    {totals['DENIED']:>4}  ({totals['DENIED']/max(totals['blocks'],1)*100:.0f}%)", file=sys.stderr)
    print(f"  PLACEHOLDER:         {totals['PLACEHOLDER']:>4}  ({totals['PLACEHOLDER']/max(totals['blocks'],1)*100:.0f}%)", file=sys.stderr)
    print(f"  RUNTIME context:     {totals['RUNTIME']:>4}  ({totals['RUNTIME']/max(totals['blocks'],1)*100:.0f}%)", file=sys.stderr)
    print(f"  RUNNABLE:            {totals['RUNNABLE']:>4}  ({runnable_pct:.0f}%)", file=sys.stderr)
    print(f"", file=sys.stderr)
    print(f"Execution (of {totals['RUNNABLE']} runnable):", file=sys.stderr)
    print(f"  PASS:    {totals['PASS']:>4}", file=sys.stderr)
    print(f"  FAIL:    {totals['FAIL']:>4}", file=sys.stderr)
    print(f"  TIMEOUT: {totals['TIMEOUT']:>4}", file=sys.stderr)
    print(f"", file=sys.stderr)
    print(f"Actual issues found: {len(findings)}", file=sys.stderr)

    if findings:
        print(f"\nIssues:", file=sys.stderr)
        for f in findings:
            print(f"  /{f['skill']} block {f['block']} ({f['section']}): {f['error'][:80]}", file=sys.stderr)

    # Verdict
    print(f"\n{'='*60}", file=sys.stderr)
    print(f"VERDICT:", file=sys.stderr)
    if skip_pct > 70:
        print(f"  {skip_pct:.0f}% of blocks are SKIPPED (placeholders/runtime/denied).", file=sys.stderr)
        print(f"  Smoke-test mode exercises <{100-skip_pct:.0f}% of skill bash content.", file=sys.stderr)
    if len(findings) == 0:
        print(f"  Zero real issues found across {totals['skills']} skills.", file=sys.stderr)
        print(f"  The skill provides no value that a basic linter wouldn't catch.", file=sys.stderr)
    elif len(findings) <= 2:
        print(f"  {len(findings)} issue(s) found — marginal value.", file=sys.stderr)
    else:
        print(f"  {len(findings)} issues found — has some value for catching broken commands.", file=sys.stderr)

    # JSON output
    print(json.dumps({
        'totals': totals,
        'skip_pct': round(skip_pct, 1),
        'findings': findings,
        'skill_details': skill_details,
    }, indent=2))


if __name__ == "__main__":
    main()
