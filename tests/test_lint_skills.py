import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import lint_skills  # noqa: E402


# --- Helpers ---

def _minimal_frontmatter(**overrides):
    fields = {
        'name': 'test-skill',
        'description': '"Use when testing the linter"',
        'version': '1.0.0',
    }
    fields.update(overrides)
    lines = ['---']
    for k, v in fields.items():
        lines.append(f'{k}: {v}')
    lines.append('---')
    return '\n'.join(lines) + '\n'


def _minimal_body(tier=1, **overrides):
    parts = {
        'procedure': '## Procedure\n\n1. Do the thing.\n',
        'completion': 'Report DONE when complete, or BLOCKED if stuck.\n',
    }
    if tier >= 2:
        parts['safety'] = '## Safety Rules\n\n- NEVER do bad things.\n'
        parts['output_silence'] = 'Maintain output silence between steps.\n'
        parts['output_format'] = '## Output Format\n\nReturn markdown.\n'
    parts.update(overrides)
    return '\n'.join(parts.values())


def _make_skill(tmp_path, fm_overrides=None, body_overrides=None, tier=1, dir_name='test-skill'):
    skill_dir = tmp_path / dir_name
    skill_dir.mkdir(parents=True, exist_ok=True)
    filepath = skill_dir / 'SKILL.md'
    fm = _minimal_frontmatter(**(fm_overrides or {}))
    body = _minimal_body(tier=tier, **(body_overrides or {}))
    filepath.write_text(fm + body)
    return filepath


# --- parse_frontmatter ---

class TestParseFrontmatter:

    def test_basic_fields(self):
        content = '---\nname: foo\nversion: 1.0.0\n---\nBody text.'
        fm, body = lint_skills.parse_frontmatter(content)
        assert fm['name'] == 'foo'
        assert fm['version'] == '1.0.0'
        assert body == 'Body text.'

    def test_quoted_values_stripped(self):
        content = '---\ndescription: "Use when testing"\n---\nBody.'
        fm, body = lint_skills.parse_frontmatter(content)
        assert fm['description'] == 'Use when testing'

    def test_single_quoted_values_stripped(self):
        content = "---\ndescription: 'Use when testing'\n---\nBody."
        fm, body = lint_skills.parse_frontmatter(content)
        assert fm['description'] == 'Use when testing'

    def test_list_values_parsed(self):
        content = '---\nlint-exempt: ["output-silence", "safety"]\n---\nBody.'
        fm, body = lint_skills.parse_frontmatter(content)
        assert fm['lint-exempt'] == ['output-silence', 'safety']

    def test_no_frontmatter_returns_empty(self):
        content = 'Just a body with no frontmatter.'
        fm, body = lint_skills.parse_frontmatter(content)
        assert fm == {}
        assert body == content

    def test_comments_skipped(self):
        content = '---\n# comment\nname: bar\n---\nBody.'
        fm, body = lint_skills.parse_frontmatter(content)
        assert 'name' in fm
        assert fm['name'] == 'bar'

    def test_empty_lines_skipped(self):
        content = '---\nname: baz\n\nversion: 2.0.0\n---\nBody.'
        fm, body = lint_skills.parse_frontmatter(content)
        assert fm['name'] == 'baz'
        assert fm['version'] == '2.0.0'


# --- classify_tier ---

class TestClassifyTier:

    def test_frontmatter_override_tier2(self):
        fm = {'tier': '2'}
        assert lint_skills.classify_tier(fm, 'simple body') == 2

    def test_frontmatter_override_tier1(self):
        fm = {'tier': '1'}
        body = 'uses debate.py and scripts/thing.py'
        assert lint_skills.classify_tier(fm, body) == 1

    def test_frontmatter_invalid_tier_falls_through(self):
        fm = {'tier': 'invalid'}
        assert lint_skills.classify_tier(fm, 'simple body') == 1

    def test_debate_py_pattern(self):
        assert lint_skills.classify_tier({}, 'Run debate.py challenge') == 2

    def test_scripts_py_pattern(self):
        assert lint_skills.classify_tier({}, 'Call scripts/enrich.py') == 2

    def test_agent_call_pattern(self):
        assert lint_skills.classify_tier({}, 'Spawn Agent( with prompt') == 2

    def test_subagent_pattern(self):
        assert lint_skills.classify_tier({}, 'Launch a subagent for this') == 2

    def test_mode_flag_pattern(self):
        assert lint_skills.classify_tier({}, 'Pass --mode discover') == 2

    def test_tasks_file_pattern(self):
        assert lint_skills.classify_tier({}, 'Write to tasks/plan.md') == 2

    def test_docs_file_pattern(self):
        assert lint_skills.classify_tier({}, 'Read docs/project-prd.md') == 2

    def test_write_tool_pattern(self):
        assert lint_skills.classify_tier({}, 'Use the Write tool to save') == 2

    def test_edit_tool_pattern(self):
        assert lint_skills.classify_tier({}, 'Use the Edit tool to modify') == 2

    def test_step_count_over_3_triggers_tier2(self):
        body = '\n'.join([
            '## Step 1', 'Do a.',
            '## Step 2', 'Do b.',
            '## Step 3', 'Do c.',
            '## Step 4', 'Do d.',
        ])
        assert lint_skills.classify_tier({}, body) == 2

    def test_step_count_at_3_stays_tier1(self):
        body = '\n'.join([
            '## Step 1', 'Do a.',
            '## Step 2', 'Do b.',
            '## Step 3', 'Do c.',
        ])
        assert lint_skills.classify_tier({}, body) == 1

    def test_plain_body_is_tier1(self):
        assert lint_skills.classify_tier({}, 'Just do the thing.') == 1

    def test_phase_count_over_3_triggers_tier2(self):
        body = '\n'.join([
            '## Phase 1', 'a.',
            '## Phase 2', 'b.',
            '## Phase 3', 'c.',
            '## Phase 4', 'd.',
        ])
        assert lint_skills.classify_tier({}, body) == 2


# --- Check 1: name matches parent directory ---

class TestCheckName:

    def test_missing_name(self, tmp_path):
        fp = _make_skill(tmp_path, fm_overrides={'name': None})
        # Remove the name field by rewriting
        content = fp.read_text()
        content = content.replace('name: None\n', '')
        fp.write_text(content)
        vs = lint_skills.lint_skill(fp)
        assert any("missing 'name'" in v for v in vs)

    def test_name_mismatch(self, tmp_path):
        fp = _make_skill(tmp_path, fm_overrides={'name': 'wrong-name'}, dir_name='correct-name')
        vs = lint_skills.lint_skill(fp)
        assert any("does not match directory" in v for v in vs)

    def test_name_matches(self, tmp_path):
        fp = _make_skill(tmp_path, dir_name='my-skill', fm_overrides={'name': 'my-skill'})
        vs = lint_skills.lint_skill(fp)
        assert not any("name" in v.lower() and "match" in v.lower() for v in vs)
        assert not any("missing 'name'" in v for v in vs)


# --- Check 2: description ---

class TestCheckDescription:

    def test_missing_description(self, tmp_path):
        fp = _make_skill(tmp_path)
        content = fp.read_text()
        content = content.replace('description: "Use when testing the linter"\n', '')
        fp.write_text(content)
        vs = lint_skills.lint_skill(fp)
        assert any("missing 'description'" in v for v in vs)

    def test_block_scalar_pipe(self, tmp_path):
        fp = _make_skill(tmp_path)
        content = fp.read_text()
        content = content.replace(
            'description: "Use when testing the linter"',
            'description: |\n  Use when testing the linter'
        )
        fp.write_text(content)
        vs = lint_skills.lint_skill(fp)
        assert any("block scalar" in v for v in vs)

    def test_block_scalar_gt(self, tmp_path):
        fp = _make_skill(tmp_path)
        content = fp.read_text()
        content = content.replace(
            'description: "Use when testing the linter"',
            'description: >\n  Use when testing the linter'
        )
        fp.write_text(content)
        vs = lint_skills.lint_skill(fp)
        assert any("block scalar" in v for v in vs)

    def test_missing_use_when(self, tmp_path):
        fp = _make_skill(tmp_path, fm_overrides={'description': '"Does stuff"'})
        vs = lint_skills.lint_skill(fp)
        assert any("Use when" in v for v in vs)

    def test_valid_description(self, tmp_path):
        fp = _make_skill(tmp_path)
        vs = lint_skills.lint_skill(fp)
        assert not any("description" in v.lower() for v in vs)


# --- Check 3: version ---

class TestCheckVersion:

    def test_missing_version(self, tmp_path):
        fp = _make_skill(tmp_path)
        content = fp.read_text()
        content = content.replace('version: 1.0.0\n', '')
        fp.write_text(content)
        vs = lint_skills.lint_skill(fp)
        assert any("missing 'version'" in v for v in vs)

    def test_invalid_semver_two_parts(self, tmp_path):
        fp = _make_skill(tmp_path, fm_overrides={'version': '1.0'})
        vs = lint_skills.lint_skill(fp)
        assert any("not valid semver" in v for v in vs)

    def test_invalid_semver_text(self, tmp_path):
        fp = _make_skill(tmp_path, fm_overrides={'version': 'latest'})
        vs = lint_skills.lint_skill(fp)
        assert any("not valid semver" in v for v in vs)

    def test_valid_semver(self, tmp_path):
        fp = _make_skill(tmp_path, fm_overrides={'version': '2.3.1'})
        vs = lint_skills.lint_skill(fp)
        assert not any("version" in v.lower() for v in vs)


# --- Check 4: Procedure section ---

class TestCheckProcedure:

    def test_missing_procedure(self, tmp_path):
        fp = _make_skill(tmp_path, body_overrides={'procedure': 'Just some text.\n'})
        vs = lint_skills.lint_skill(fp)
        assert any("procedure section" in v.lower() for v in vs)

    def test_procedure_heading(self, tmp_path):
        fp = _make_skill(tmp_path, body_overrides={'procedure': '## Procedure\n\nDo it.\n'})
        vs = lint_skills.lint_skill(fp)
        assert not any("procedure section" in v.lower() for v in vs)

    def test_steps_heading(self, tmp_path):
        fp = _make_skill(tmp_path, body_overrides={'procedure': '## Steps\n\n1. Do it.\n'})
        vs = lint_skills.lint_skill(fp)
        assert not any("procedure section" in v.lower() for v in vs)

    def test_step_n_heading(self, tmp_path):
        fp = _make_skill(tmp_path, body_overrides={'procedure': '### Step 1\n\nDo it.\n'})
        vs = lint_skills.lint_skill(fp)
        assert not any("procedure section" in v.lower() for v in vs)


# --- Check 5: Completion status codes ---

class TestCheckCompletion:

    def test_missing_done(self, tmp_path):
        fp = _make_skill(tmp_path, body_overrides={'completion': 'Finish and report.\n'})
        vs = lint_skills.lint_skill(fp)
        assert any("'DONE' not found" in v for v in vs)

    def test_done_without_secondary(self, tmp_path):
        fp = _make_skill(tmp_path, body_overrides={'completion': 'Report DONE.\n'})
        vs = lint_skills.lint_skill(fp)
        assert any("DONE_WITH_CONCERNS" in v for v in vs)

    def test_done_with_blocked(self, tmp_path):
        fp = _make_skill(tmp_path, body_overrides={'completion': 'Report DONE or BLOCKED.\n'})
        vs = lint_skills.lint_skill(fp)
        assert not any("completion" in v.lower() for v in vs)

    def test_done_with_needs_context(self, tmp_path):
        fp = _make_skill(tmp_path, body_overrides={'completion': 'Report DONE or NEEDS_CONTEXT.\n'})
        vs = lint_skills.lint_skill(fp)
        assert not any("completion" in v.lower() for v in vs)

    def test_done_with_concerns(self, tmp_path):
        fp = _make_skill(tmp_path, body_overrides={'completion': 'Report DONE or DONE_WITH_CONCERNS.\n'})
        vs = lint_skills.lint_skill(fp)
        assert not any("completion" in v.lower() for v in vs)


# --- Check 6: Safety Rules (Tier 2) ---

class TestCheckSafetyRules:

    def test_missing_safety_section(self, tmp_path):
        fp = _make_skill(tmp_path, fm_overrides={'tier': '2'}, tier=2,
                         body_overrides={'safety': ''})
        vs = lint_skills.lint_skill(fp)
        assert any("Safety Rules" in v for v in vs)

    def test_safety_without_never_or_donot(self, tmp_path):
        fp = _make_skill(tmp_path, fm_overrides={'tier': '2'}, tier=2,
                         body_overrides={'safety': '## Safety Rules\n\nBe careful.\n'})
        vs = lint_skills.lint_skill(fp)
        assert any("NEVER" in v and "Do not" in v for v in vs)

    def test_safety_with_never(self, tmp_path):
        fp = _make_skill(tmp_path, fm_overrides={'tier': '2'}, tier=2,
                         body_overrides={'safety': '## Safety Rules\n\n- NEVER break things.\n'})
        vs = lint_skills.lint_skill(fp)
        assert not any("Safety Rules" in v and "must contain" in v for v in vs)

    def test_safety_with_do_not(self, tmp_path):
        fp = _make_skill(tmp_path, fm_overrides={'tier': '2'}, tier=2,
                         body_overrides={'safety': '## Safety Rules\n\n- Do not break things.\n'})
        vs = lint_skills.lint_skill(fp)
        assert not any("Safety Rules" in v and "must contain" in v for v in vs)

    def test_tier1_skips_safety_check(self, tmp_path):
        fp = _make_skill(tmp_path, tier=1, body_overrides={'safety': ''})
        vs = lint_skills.lint_skill(fp)
        assert not any("Safety Rules" in v for v in vs)


# --- Check 7: Output Silence (Tier 2) ---

class TestCheckOutputSilence:

    def test_missing_output_silence(self, tmp_path):
        fp = _make_skill(tmp_path, fm_overrides={'tier': '2'}, tier=2,
                         body_overrides={'output_silence': ''})
        vs = lint_skills.lint_skill(fp)
        assert any("Output Silence" in v for v in vs)

    def test_output_silence_present(self, tmp_path):
        fp = _make_skill(tmp_path, fm_overrides={'tier': '2'}, tier=2)
        vs = lint_skills.lint_skill(fp)
        assert not any("Output Silence" in v for v in vs)

    def test_lint_exempt_skips_output_silence(self, tmp_path):
        fp = _make_skill(tmp_path, fm_overrides={
            'tier': '2',
            'lint-exempt': '["output-silence"]',
        }, tier=2, body_overrides={'output_silence': ''})
        vs = lint_skills.lint_skill(fp)
        assert not any("Output Silence" in v for v in vs)

    def test_tier1_skips_output_silence_check(self, tmp_path):
        fp = _make_skill(tmp_path, tier=1, body_overrides={'output_silence': ''})
        vs = lint_skills.lint_skill(fp)
        assert not any("Output Silence" in v for v in vs)


# --- Check 8: Output Format (Tier 2) ---

class TestCheckOutputFormat:

    def test_missing_output_format(self, tmp_path):
        fp = _make_skill(tmp_path, fm_overrides={'tier': '2'}, tier=2,
                         body_overrides={'output_format': ''})
        vs = lint_skills.lint_skill(fp)
        assert any("output format section" in v.lower() for v in vs)

    def test_output_format_present(self, tmp_path):
        fp = _make_skill(tmp_path, fm_overrides={'tier': '2'}, tier=2)
        vs = lint_skills.lint_skill(fp)
        assert not any("output format" in v.lower() for v in vs)

    def test_output_heading(self, tmp_path):
        fp = _make_skill(tmp_path, fm_overrides={'tier': '2'}, tier=2,
                         body_overrides={'output_format': '## Output\n\nMarkdown.\n'})
        vs = lint_skills.lint_skill(fp)
        assert not any("output format" in v.lower() for v in vs)

    def test_deliverable_heading(self, tmp_path):
        fp = _make_skill(tmp_path, fm_overrides={'tier': '2'}, tier=2,
                         body_overrides={'output_format': '## Deliverable\n\nMarkdown.\n'})
        vs = lint_skills.lint_skill(fp)
        assert not any("output format" in v.lower() for v in vs)

    def test_tier1_skips_output_format_check(self, tmp_path):
        fp = _make_skill(tmp_path, tier=1)
        vs = lint_skills.lint_skill(fp)
        assert not any("output format" in v.lower() for v in vs)


# --- Check 9: Debate fallback ---

class TestCheckDebateFallback:

    def test_debate_without_fallback(self, tmp_path):
        body_with_debate = '## Procedure\n\nRun debate.py challenge on the proposal.\n'
        fp = _make_skill(tmp_path, fm_overrides={'tier': '2'}, tier=2,
                         body_overrides={'procedure': body_with_debate})
        vs = lint_skills.lint_skill(fp)
        assert any("Debate fallback" in v for v in vs)

    def test_debate_with_fallback_within_5_lines(self, tmp_path):
        body_with_debate = (
            '## Procedure\n\n'
            'Run debate.py challenge on the proposal.\n'
            'If debate.py is unavailable, skip and proceed manually.\n'
        )
        fp = _make_skill(tmp_path, fm_overrides={'tier': '2'}, tier=2,
                         body_overrides={'procedure': body_with_debate})
        vs = lint_skills.lint_skill(fp)
        assert not any("Debate fallback" in v for v in vs)

    def test_debate_with_error_keyword(self, tmp_path):
        body_with_debate = (
            '## Procedure\n\n'
            'Run debate.py challenge.\n'
            'If there is an error, proceed with single-model review.\n'
        )
        fp = _make_skill(tmp_path, fm_overrides={'tier': '2'}, tier=2,
                         body_overrides={'procedure': body_with_debate})
        vs = lint_skills.lint_skill(fp)
        assert not any("Debate fallback" in v for v in vs)

    def test_debate_with_fails_keyword(self, tmp_path):
        body_with_debate = (
            '## Procedure\n\n'
            'Run debate.py challenge.\n'
            'If it fails, proceed manually.\n'
        )
        fp = _make_skill(tmp_path, fm_overrides={'tier': '2'}, tier=2,
                         body_overrides={'procedure': body_with_debate})
        vs = lint_skills.lint_skill(fp)
        assert not any("Debate fallback" in v for v in vs)

    def test_no_debate_reference_passes(self, tmp_path):
        fp = _make_skill(tmp_path, fm_overrides={'tier': '2'}, tier=2)
        vs = lint_skills.lint_skill(fp)
        assert not any("Debate fallback" in v for v in vs)

    def test_debate_fallback_too_far_away(self, tmp_path):
        lines = [
            '## Procedure\n',
            'Run debate.py challenge.\n',
        ]
        # Add 10 lines of filler so fallback is out of window
        for i in range(10):
            lines.append(f'Step {i}: do something unrelated.\n')
        lines.append('If unavailable, skip.\n')
        body_with_debate = '\n'.join(lines)
        fp = _make_skill(tmp_path, fm_overrides={'tier': '2'}, tier=2,
                         body_overrides={'procedure': body_with_debate})
        vs = lint_skills.lint_skill(fp)
        assert any("Debate fallback" in v for v in vs)


# --- check_debate_fallback standalone ---

class TestCheckDebateFallbackFunction:

    def test_no_debate_returns_empty(self):
        assert lint_skills.check_debate_fallback('No mentions here.') == []

    def test_debate_with_nearby_fallback(self):
        body = 'Run debate.py\nIf fallback needed, skip.'
        assert lint_skills.check_debate_fallback(body) == []

    def test_debate_without_fallback(self):
        body = 'Run debate.py\nThen continue normally.'
        result = lint_skills.check_debate_fallback(body)
        assert len(result) == 1
        assert "Debate fallback" in result[0]


# --- lint-exempt mechanism ---

class TestLintExempt:

    def test_single_string_exempt(self, tmp_path):
        # lint-exempt as a single string value (not a list)
        skill_dir = tmp_path / 'test-skill'
        skill_dir.mkdir()
        filepath = skill_dir / 'SKILL.md'
        content = (
            '---\n'
            'name: test-skill\n'
            'description: "Use when testing"\n'
            'version: 1.0.0\n'
            'tier: 2\n'
            'lint-exempt: output-silence\n'
            '---\n'
            '## Procedure\n\n1. Do it.\n\n'
            'Report DONE or BLOCKED.\n\n'
            '## Safety Rules\n\n- NEVER break things.\n\n'
            '## Output Format\n\nMarkdown.\n'
        )
        filepath.write_text(content)
        vs = lint_skills.lint_skill(filepath)
        assert not any("Output Silence" in v for v in vs)


# --- File not found ---

class TestFileNotFound:

    def test_nonexistent_file(self, tmp_path):
        fp = tmp_path / 'nonexistent' / 'SKILL.md'
        vs = lint_skills.lint_skill(fp)
        assert any("File not found" in v for v in vs)


# --- Full clean pass ---

class TestCleanPass:

    def test_tier1_clean(self, tmp_path):
        fp = _make_skill(tmp_path, tier=1)
        vs = lint_skills.lint_skill(fp)
        assert vs == []

    def test_tier2_clean(self, tmp_path):
        fp = _make_skill(tmp_path, fm_overrides={'tier': '2'}, tier=2)
        vs = lint_skills.lint_skill(fp)
        assert vs == []


# --- Tier misclassification edge cases ---

class TestTierMisclassification:

    def test_tier_override_suppresses_tier2_checks(self, tmp_path):
        # Skill body has tier2 patterns but frontmatter says tier 1
        fp = _make_skill(tmp_path, fm_overrides={'tier': '1'}, tier=1,
                         body_overrides={'procedure': '## Procedure\n\nRun debate.py challenge.\n'})
        vs = lint_skills.lint_skill(fp)
        # Should NOT have tier 2 violations since frontmatter override says 1
        assert not any("Tier 2" in v for v in vs)

    def test_tier_override_enables_tier2_checks(self, tmp_path):
        # Simple body but frontmatter says tier 2 -- tier 2 checks should fire
        fp = _make_skill(tmp_path, fm_overrides={'tier': '2'}, tier=1)
        vs = lint_skills.lint_skill(fp)
        # Missing tier 2 sections should be flagged
        assert any("Tier 2" in v for v in vs)

    def test_heuristic_debate_triggers_tier2(self, tmp_path):
        # No tier override; debate.py in body should trigger tier 2
        fp = _make_skill(tmp_path, tier=1,
                         body_overrides={'procedure': '## Procedure\n\nRun debate.py.\n'})
        vs = lint_skills.lint_skill(fp)
        # Should get tier 2 violations since heuristic kicked in
        assert any("Tier 2" in v for v in vs)

    def test_heuristic_step_count_triggers_tier2(self, tmp_path):
        steps = '\n'.join([f'## Step {i}\n\nDo step {i}.\n' for i in range(1, 5)])
        fp = _make_skill(tmp_path, tier=1,
                         body_overrides={'procedure': steps})
        vs = lint_skills.lint_skill(fp)
        assert any("Tier 2" in v for v in vs)

    def test_heuristic_agent_triggers_tier2(self, tmp_path):
        fp = _make_skill(tmp_path, tier=1,
                         body_overrides={'procedure': '## Procedure\n\nSpawn Agent( with task.\n'})
        vs = lint_skills.lint_skill(fp)
        assert any("Tier 2" in v for v in vs)
