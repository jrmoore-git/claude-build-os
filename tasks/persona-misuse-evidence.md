# Evidence: Persona Misuse in review-panel Calls (L21 Drift)

## Claim Under Investigation
L21: "review-panel personas are model selectors, not system prompts -- stop defaulting to architect/security/pm for non-code evaluation."

## Evidence Collected

### E1: review-panel implementation (scripts/debate.py lines 2790-2960)
- `--personas` resolves persona names to model names via `config/debate-models.json`
- `--models` accepts model names directly, sets `direct_models_mode = True`
- **Critical finding:** In BOTH modes, the system prompt is ONLY the caller's `--prompt` or `--prompt-file` content (line 2877: `system=prompt + TOOL_INJECTION_DEFENSE`). The `PERSONA_PROMPTS` dictionary (line 607) is NOT used by review-panel. It is only used by the `challenge` subcommand (line 1046).
- The ONLY behavioral difference between `--personas` and `--models` in review-panel is: (a) which model is selected, and (b) the audit log records `"mode": "direct-models"` for `--models`.

### E2: config/debate-models.json persona-to-model mapping
- architect -> claude-opus-4-6
- staff -> gemini-3.1-pro
- security -> gpt-5.4
- pm -> gemini-3.1-pro

Note: `--personas architect,security,pm` resolves to claude-opus-4-6, gpt-5.4, gemini-3.1-pro -- the same 3 models as `--models claude-opus-4-6,gemini-3.1-pro,gpt-5.4`.

### E3: Skill-by-skill audit of review-panel invocations

| Skill | Line | Subcommand | Flag | Content Type | Correct? |
|-------|------|------------|------|--------------|----------|
| /review (code mode) | 196 | challenge | --personas architect,security,pm | Code diff | YES (challenge uses PERSONA_PROMPTS) |
| /review (doc mode) | 424 | review-panel | --models claude-opus-4-6,gemini-3.1-pro,gpt-5.4 | Non-code document | YES (fixed post-L21) |
| /investigate | 215 | review-panel | --models claude-opus-4-6,gemini-3.1-pro,gpt-5.4 | Investigation evidence | YES (built post-L21) |
| /think (Phase 5.5) | 625 | review-panel | --personas architect,security,pm | Design document | NO -- uses personas for non-code |
| /challenge | 19, 170 | challenge | --personas architect,security,pm | Proposal | N/A (challenge subcommand, not review-panel) |

### E4: The /think skill drift
`/think` Phase 5.5 "Spec Review" (line 621-635) calls:
```
review-panel --personas architect,security,pm --prompt "Review on 5 dimensions..."
```
This is reviewing a design document (non-code). It uses `--personas` instead of `--models`. While the system prompt IS the caller's prompt in both cases, the `--personas` flag:
1. Makes the intent unclear (suggests code-review framing)
2. Maps pm and staff to the SAME model (gemini-3.1-pro), losing model diversity -- only 2 unique models instead of 3
3. The text says "multi-persona review panel" and "reviewer archetypes" which reinforces the wrong mental model

### E5: Functional impact of the pm/staff model collision
With `--personas architect,security,pm`:
- architect -> claude-opus-4-6
- security -> gpt-5.4  
- pm -> gemini-3.1-pro

With `--models claude-opus-4-6,gemini-3.1-pro,gpt-5.4`:
- All three are unique models

Result: **identical** in this specific case. Both produce 3 unique models. But if someone used `--personas architect,staff,pm`, they'd get claude-opus-4-6, gemini-3.1-pro, gemini-3.1-pro -- only 2 unique models. The L21 lesson text actually mentions "architect,staff,pm" as the problematic pattern.

### E6: L21 status
L21 is still Active in tasks/lessons.md. Not promoted to a rule or hook. Not marked as resolved.

### E7: D15 decision (tasks/decisions.md line 93)
D15 established the rule: code -> `review-panel --personas`, documents -> `review-panel --models`. The /review skill correctly implements this. /think does not.

## Hypothesis Testing

### Hypothesis A: Drift is fixed -- skills now correctly use --models for non-code, --personas for code
**Verdict: MOSTLY CONFIRMED, one exception.**
- /review: Fixed. Document mode uses --models (line 424). Code mode uses challenge --personas (line 196).
- /investigate: Correct from inception. Uses --models (line 215).
- /think: STILL USES --personas for design doc review (line 625-626). This is the one remaining drift instance.
- /challenge: N/A -- uses the `challenge` subcommand which properly injects PERSONA_PROMPTS.

### Hypothesis B: Drift persists -- multiple skills still use --personas for document evaluation
**Verdict: PARTIALLY SUPPORTED.**
Only one skill (/think) still has the drift pattern. Not "multiple" -- singular. The claim that it was "repeatedly called" was about runtime behavior (the session agent defaulting to personas), not about skill definitions. The skill definitions were partially fixed.

### Hypothesis C: The distinction doesn't matter -- personas are just model selectors anyway
**Verdict: PARTIALLY TRUE, but misleading.**
- Functionally, review-panel does NOT inject persona system prompts in either mode. The caller's --prompt is always the only system prompt. So the API output is identical when the resolved models are the same.
- However: (1) `--personas architect,staff,pm` maps staff and pm to the SAME model, losing diversity. (2) The persona names create misleading intent in skill code. (3) The audit log doesn't record `"mode": "direct-models"` in personas mode, making it harder to distinguish code vs. non-code reviews in debate-log.jsonl.
