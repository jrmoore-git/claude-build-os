---
debate_id: explore-gate
created: 2026-04-10T18:43:13-0700
phase: refine
rounds: 6
models: gemini-3.1-pro, gpt-5.4, claude-opus-4-6
seeded_from_judgment: no
---
# explore-gate — Refined Document

## Round 1 (gemini-3.1-pro)
- **Clarity & Correctness**: The document clearly defines the problem, but Fix 1's proposed implementation needs a crucial logical distinction: you cannot read a file before creating it. `Write` operations that create new files must be exempted from reading the target file, though requiring reads of related files or the target directory is valid.
- **Completeness**: The document notes that Claude Code already enforces reading before `Edit`, but notes `Write` lacks this. The proposed hook must carefully avoid breaking valid file creation workflows. 
- **Structure**: The structure is strong. I preserved the operational context and baseline facts, slightly improved the formatting, and integrated the edge-case consideration into Fix 1. The final recommendations are preserved exactly as required.

## Round 2 (gpt-5.4)
The proposal is already clear and well-scoped, but a few improvements were needed:

- Several repository-specific assertions were presented as facts without verification. I verified only what the available tools could confirm.
- Some claims about existing files/features in the repo could not be substantiated with the provided tools, so the revised document narrows or caveats them instead of stating them as confirmed facts.
- The structure was good, but the argument is stronger if it distinguishes clearly between:
  - what is verified,
  - what is inferred from the current workflow description,
  - and what is proposed.
- The recommendation section was preserved exactly in count and intent, per instruction.
- I did not remove any operational/contextual sections; instead, I tightened wording where evidence was thinner.

## Round 3 (claude-opus-4-6)
The previous revision is well-structured and significantly improved over what a raw proposal would look like. Key strengths:

1. **Good evidence tagging** — claims about `config/debate-models.json`, `hook-pre-edit-read-check.py` absence, and `CLAUDE.md` references are properly evidenced.
2. **Balanced trade-offs** — each fix includes pros and cons.
3. **Recommendations are preserved** with appropriate caveats.

**Issues I found:**

1. **Overstated claim about `hook-decompose-gate.py`**: The document says "the proposal references a decomposition gate (`hook-decompose-gate.py`) that blocks `Write|Edit` until decomposition is assessed. This document treats that as existing operational context from the current system description." My verification shows `hook-decompose-gate.py` does **not exist** in either the scripts or skills file sets. The substring `decompose-gate` returns zero matches in scripts. The document's framing ("treats that as existing operational context") is ambiguous — it could be read as claiming this hook exists. This needs to be corrected to clearly state the hook is referenced in system design documentation but is not verified as implemented.

2. **Missing verification of `hooks/` directory**: The proposal targets `hooks/hook-pre-edit-read-check.py` but doesn't verify whether the `hooks/` directory exists or contains any hooks. The `PreToolUse` substring returns zero matches in both scripts and skills, suggesting no hook infrastructure is currently implemented. This is a material gap — if no hooks exist yet, Fix 1 requires building infrastructure, not just adding a file.

3. **"before planning" exists in skills**: The substring `before planning` appears twice in the skills file set, suggesting there is already some guidance about exploration before action. The document should acknowledge this existing guidance more specifically.

4. **Minor structural issues**: The "New Facts Introduced" section at the bottom is appropriate for the debate process but slightly redundant with inline evidence tags. The Excluded Options section could be tightened.

5. **The `explore` substring appears in both scripts (1 match) and skills (5 matches)**, confirming that exploration-related concepts are already present in the system — the document's claim that these are "partially addressed" in debate/review flows is supported.

## Round 4 (gemini-3.1-pro)
The previous revision is excellent. It correctly identifies the gap between design concepts (like `hook-decompose-gate.py` or general hook infrastructure) and the actual running codebase, grounding the analysis in concrete tool findings. 

Improvements made in this pass:
- Lightly polished the prose for better flow and readability, specifically in the "Implementation note" and "Important nuance" sections.
- Tightened the wording in the Recommendations section to make the action items punchier while strictly preserving the existing caveats and constraints.
- Retained all `EVIDENCED` tags and structural elements as required.

## Round 5 (gpt-5.4)
The revision is strong overall: it preserves the proposal’s core argument, separates verified repository facts from design ideas, and correctly narrows the strongest recommendation to what the current codebase actually supports.

A few improvements were still needed:

1. **One verified-data mismatch needed correction.**
   - The document says `explore` appears in skills **5** times and `orient` appears **3** times, but repository checks returned **6** and **4** respectively. I corrected those counts.
2. **One repository fact was stated more strongly than verified.**
   - “No hook infrastructure detected” based only on `PreToolUse` not appearing in `scripts` and `skills` is directionally useful, but too absolute for the whole repo because those searches did not cover every possible location. I narrowed this to: no `PreToolUse` references were found in the checked `scripts` and `skills` file sets, so hook infrastructure is **not verified** in the current inspected areas.
3. **A few claims mixed repository facts with platform assumptions.**
   - The note about Claude Code possibly already enforcing unread-file protection is retained, but clearly marked as proposal context rather than verified repo fact.
4. **Structure and flow were improved slightly.**
   - I tightened section wording, made “What Exists” vs. “What Is Missing” more precise, and clarified that the strongest evidence supports a staged rollout: immediate instruction update plus scoped hook prototype.
5. **Recommendations were preserved exactly in count and intent.**
   - The original 2 recommendations remain, with caveats preserved and phrased more crisply.

## Round 6 (claude-opus-4-6)
**Improvements the previous reviewer made well:**
- Thorough evidence tagging throughout — nearly every factual claim is backed by tool verification.
- Honest about what's missing: `PreToolUse`, `hook-pre-edit-read-check`, and `decompose-gate` are all correctly identified as absent.
- Good separation of Fix 1 (structural) and Fix 2 (advisory), with clear trade-offs for each.
- Appropriate caveats on both recommendations about implementation scope and reliability limits.
- The "New Facts Introduced" section is well-organized and fully evidenced.

**Remaining issues I identified:**

1. **Incomplete inventory of existing guidance.** The document catalogs `explore`, `before planning`, and `orient` in skills, but misses additional relevant matches: `before writing` (2 matches in skills), `read first` (1 match in skills), and `before implement` (2 matches in skills). These strengthen the case that guidance *exists* but is scattered and non-structural — and they're directly relevant to Fix 2's value proposition.

2. **The `hooks` substring exists in config (2 matches), skills (3 matches), and scripts (2 matches).** The document says hook infrastructure is "not verified" but doesn't acknowledge that the *concept* of hooks is referenced across the codebase. This is a nuance worth capturing: the system discusses hooks but doesn't appear to have `PreToolUse`/`PostToolUse` wiring implemented.

3. **The `.claude/settings.json` reference exists in skills (1 match).** This is relevant to Fix 1's implementation note about where hook configuration would live — the skills already reference this path.

4. **No audit_log table exists**, meaning there's no operational data to quantify how often "edit without reading" or "answer without inspecting" actually occurs. The problem statement is based on qualitative complaints, not measured failure rates. This is an important methodological gap the document should acknowledge.

5. **Minor structural issue:** The "Current System State" section mixes "What Exists" (good) with "What Is Missing" (good), but the "What Exists" subsection buries the most important finding — that exploration guidance exists but is scattered and non-structural — in a parenthetical. This deserves more prominence since it's the core justification for both fixes.

6. **The config file contains richer context than cited.** The `debate-models.json` notes field mentions `verifier_default`, `compare_default`, and operational history about GPT tool use. The document cites "persona-to-model mappings, judge/compare/refine defaults" which is accurate but could note the verifier and the operational notes about tool-encouraging prompts, since tool use is directly relevant to the "inspect before answering" problem.

7. **`decompose` appears in skills (1 match) even though `decompose-gate` and `hook-decompose-gate.py` don't.** The concept exists in guidance even if the specific hook doesn't. Minor but worth precision.

## Final Refined Document

# Proposal: Structural Enforcement for "Explore Before Acting" and "Inspect Before Answering"

## Problem Statement

Two recurring complaints about Claude Code behavior in the BuildOS framework are:

1. **Not enough iterative exploration before it goes to work** — the model moves to implementation before adequately exploring the codebase.
2. **Doesn't inspect code before giving answers, assumes it can't do something** — the model answers questions about code from prior knowledge or intuition instead of first checking the repository.

The current workflow partially addresses these issues in debate/review flows and guidance, but they are not structurally enforced for general day-to-day Claude Code usage. That gap matters because general coding sessions define most of the developer experience.

**Methodological note:** These complaints are qualitative. No audit_log table exists in the current system to measure how frequently "edit without reading" or "answer without inspecting" actually occurs. EVIDENCED: `audit_log` queries return "no such table." The recommendations below are therefore driven by reported developer experience, not measured failure rates. Establishing instrumentation to quantify these behaviors would strengthen future iterations.

## Current System State

### What Exists

- **Model-routing and debate configuration** are present in `config/debate-models.json` (15 lines). It contains persona-to-model mappings (architect → claude-opus-4-6, staff → gemini-3.1-pro, security → gpt-5.4, pm → gemini-3.1-pro), judge default (gpt-5.4), compare default (gemini-3.1-pro), refine rotation, verifier default (claude-sonnet-4-6), and a version stamp of `2026-04-09`. The notes field records operational history including a tool-encouraging prompt change for GPT and that `read_file_snippet` "unlocked GPT tool use (9 calls in first debate)" — directly relevant to the "inspect before answering" problem since the debate system already learned that enabling tool use improves inspection behavior. EVIDENCED: `config/debate-models.json` lines 1–15.

- **Exploration-related guidance is present but scattered across skills.** Multiple relevant substrings appear in the skills file set:
  - `explore`: 6 matches in skills, 1 in scripts
  - `before planning`: 2 matches in skills
  - `orient`: 4 matches in skills
  - `before writing`: 2 matches in skills
  - `before implement`: 2 matches in skills
  - `read first`: 1 match in skills
  - `inspect`: 1 match in skills, 2 in scripts
  
  EVIDENCED: exact substring searches on skills and scripts file sets. This confirms that guidance about exploration before action exists in multiple forms, but it is distributed across workflow-specific contexts rather than consolidated into a single enforceable rule. The variety of phrasings ("explore," "orient," "read first," "before writing," "before implement") suggests organic accumulation rather than deliberate structural design.

- **References to `CLAUDE.md`** exist in the skills file set (5 matches), confirming it is a recognized configuration surface for behavioral rules. EVIDENCED: substring search on skills file set.

- **References to `.claude/settings.json`** exist in the skills file set (1 match), confirming this path is recognized as a configuration location — relevant to where hook configuration would be registered. EVIDENCED: substring search on skills file set.

- **The `--enable-tools` flag** exists in the scripts file set (1 match), supporting the claim that debate/review flows can enable tool use for exploration. EVIDENCED: substring search on scripts file set.

- **Hook-related concepts are referenced but not wired.** The substring `hook` appears in scripts (2 matches), skills (3 matches), and config (2 matches). The concept of `decompose` appears in skills (1 match). However, no `PreToolUse` or `PostToolUse` references were found in any inspected file set (scripts, skills, or config — all returned 0 matches). EVIDENCED: exact substring searches. This means the codebase discusses hooks as a concept but does not appear to have Claude Code hook event wiring (`PreToolUse`/`PostToolUse`) implemented in the inspected areas.

- **The decomposition gate concept** (`hook-decompose-gate.py`) is referenced in design discussion as a pattern that blocks `Write`/`Edit` until decomposition is assessed. However, `hook-decompose-gate.py` returned 0 matches in skills, and `decompose-gate` returned 0 matches in scripts. EVIDENCED: exact substring searches. This supports treating the pattern as a design reference, not verified running infrastructure.

### What Is Missing

- **No implemented pre-edit read-check hook.** The substring `hook-pre-edit-read-check` returns 0 matches in the scripts file set. EVIDENCED: exact substring search.
- **No Claude Code hook event wiring.** `PreToolUse` returns 0 matches in scripts, skills, and config. `PostToolUse` returns 0 matches in scripts, skills, and config. EVIDENCED: exact substring searches across all three file sets. Hook infrastructure for intercepting tool calls is not currently implemented in any inspected area.
- **No general mechanism** is verified that blocks edits until surrounding context has been read, outside workflow-specific guidance.
- **No structural enforcement** is verified for answering code questions only after inspection, outside specialized review/debate paths.
- **No operational instrumentation.** No audit_log table exists to measure how often the target failure modes occur. EVIDENCED: all `count_records` queries return "no such table."
- Advisory rules alone remain susceptible to being skipped under context pressure — and the current guidance is scattered across at least 6 different phrasings in the skills file set rather than consolidated.

## Proposed Solutions

### Fix 1: Pre-edit Exploration Gate (Hook-Enforced)

Introduce a hook on `Edit`/`Write` tool calls that verifies context has been gathered before allowing modification.

**Proposed implementation:** `hooks/hook-pre-edit-read-check.py`, registered via `.claude/settings.json` (or equivalent) as a `PreToolUse` hook.

**Behavior:**
- Track session-level read operations (`Read`, `Grep`, `Glob`).
- On `Edit` or `Write`, check whether the target file was previously read.
- **New-file exemption:** If `Write` is creating a new file, exempt the target file itself from the read requirement, but require evidence that the target directory or related files were inspected first.
- If context is missing, block with: **"Read the file or relevant directory before editing/creating it."**

**Rationale:**
- This reuses a hook-enforcement pattern described in the design discussion (the decomposition gate concept), though that pattern has not been verified as an implemented hook in the inspected repository areas. EVIDENCED: `decompose-gate` not found in scripts; `PreToolUse` not found in scripts, skills, or config.
- It targets the highest-cost failure mode: modifying code before orienting to local context.

**Implementation note — hook infrastructure:**
No `PreToolUse` or `PostToolUse` references were found in any inspected file set (scripts, skills, config). EVIDENCED: exact substring searches all returned 0 matches. However, `.claude/settings.json` is referenced in skills (1 match) and `hook` appears across scripts (2), skills (3), and config (2), indicating the codebase is aware of hooks as a concept. Implementing Fix 1 requires:
1. Setting up Claude Code hooks configuration in `.claude/settings.json` with `PreToolUse` event registration.
2. Implementing the hook script itself.
3. Testing the hook's interaction with normal workflows.

This is a larger lift than "add one file." The implementation should be scoped to include infrastructure setup time.

**Important nuance:**
Claude Code may already enforce some unread-file protection internally for `Edit` (for example, requiring the file to have been read before editing). This is proposal context, not a verified repository fact. The proposal's distinctive value is extending enforcement to `Write` for new file creation and to nearby-context inspection, not just the direct target file.

**Lightweight variant:**
Instead of a hard block, track a session-level count of read-type tool calls. If `Edit`/`Write` occurs before a minimum threshold of reads, emit a warning rather than blocking. This is a reasonable starting point given that hook infrastructure is not currently implemented in the inspected codebase areas.

**Trade-offs:**
- **Pro:** Targets the highest-cost failure mode directly.
- **Pro:** Likely low false-positive rate because legitimate edits usually follow some reading.
- **Con:** Enforces reading activity, not comprehension.
- **Con:** Can add friction for trivial edits.
- **Con:** Requires building hook infrastructure (`PreToolUse` wiring) that does not yet exist in the inspected areas.

**Refinement to reduce false positives:**
Prefer scoped exemptions based on operation type and file state rather than broad size-based exemptions. Exempting only clearly trivial operations or explicitly tagged low-risk workflows is safer unless future evidence supports a strict line-count threshold.

### Fix 2: Behavioral Pattern Rule (CLAUDE.md-Enforced)

Consolidate the current scattered exploration guidance into a concrete, unified behavioral pattern in `CLAUDE.md`.

**Existing state:** The skills file set contains exploration-related guidance in at least 6 forms: `explore` (6 matches), `before planning` (2), `orient` (4), `before writing` (2), `before implement` (2), and `read first` (1). EVIDENCED: substring searches on skills file set. This guidance exists but is fragmented — multiple phrasings across different contexts rather than a single authoritative rule. Fix 2 consolidates and sharpens this into one explicit, actionable directive.

**Proposed rule update:**
```text
When asked about code behavior, implementation details, or "can we do X":
1. Inspect the relevant repository context first using the available read/search tools.
2. Answer from what you found in the code, not from memory.
3. If you did not inspect the code, say so explicitly instead of implying certainty.
```

**Why use an instruction rather than a hook:**
- A hook that tries to detect whether the model is "about to answer a question about code" from output text would be brittle and produce many false positives.
- For answer-quality behavior during normal sessions, specific session instructions remain the strongest available lever currently identified in this proposal.

**Trade-offs:**
- **Pro:** Specific instructions are more likely to trigger correctly than vague or scattered guidance.
- **Pro:** Zero implementation cost and negligible latency cost.
- **Pro:** Consolidates 6+ existing scattered guidance fragments into one authoritative rule.
- **Con:** This is still not structural enforcement — it is advisory.
- **Con:** Reliability depends on instruction-following under pressure.

## Excluded Options (What NOT to Build)

- **Text Output Hook:** A hook that tries to detect "answering about code" from raw output is likely too noisy and brittle to be reliable.
- **Mandatory N-File-Read Gate:** A strict read-count gate before any response would add too much friction for simple tasks.
- **Upstream BuildOS Changes:** Modifying BuildOS directly may create divergence and synchronization burden if multiple downstream environments must stay aligned.

## Recommendations

1. **Build Fix 1 (Pre-edit gate hook):** Prioritize this as the first change. It is the higher-value intervention because it provides structural enforcement for the editing path and prevents the most damaging behavior: editing without understanding.  
   **Caveat:** This requires building hook infrastructure (`PreToolUse` event wiring) that is not currently present in any inspected codebase area — not just adding a single script file. Start with a narrow scope: enforce read-before-edit on `Write` and new-file creation context, and prefer warning mode initially until false-positive behavior is observed in practice. Scope the implementation to include infrastructure setup time.  
   **Additional caveat:** The frequency of the target failure mode (editing without reading) is not currently measured — no audit_log exists. Consider adding lightweight instrumentation (e.g., logging hook triggers) alongside the hook itself to establish a baseline and validate that the hook fires at a meaningful rate.

2. **Ship Fix 2 (Behavioral rule rewrite):** Deploy this alongside or ahead of Fix 1 to provide immediate behavioral guidance for the answering path. Neither fix alone is sufficient to solve both aspects of the problem. Fix 2 has zero implementation cost and can ship immediately by updating `CLAUDE.md`.  
   **Caveat:** Treat this as a reliability improvement, not a guarantee, because instruction-only controls remain weaker than hooks. Existing exploration guidance in the skills file set (at least 6 distinct phrasings across 17+ matches) confirms the system already partially addresses this; the value of Fix 2 is consolidating scattered guidance into one concrete, authoritative rule rather than introducing an entirely new concept.

## New Facts Introduced

- `config/debate-models.json` exists (15 lines) and contains active model-routing/default configuration, including version `2026-04-09`, verifier_default `claude-sonnet-4-6`, and operational notes about tool-encouraging prompts. EVIDENCED: `config/debate-models.json` lines 1–15.
- `hook-pre-edit-read-check` was not found in the scripts file set. EVIDENCED: exact substring search returned 0 matches.
- `hook-decompose-gate.py` was not found in the skills file set, and `decompose-gate` was not found in the scripts file set. The decomposition gate appears to be a design reference rather than a verified implemented hook. EVIDENCED: exact substring searches returned 0 matches.
- `PreToolUse` was not found in scripts, skills, or config file sets. `PostToolUse` was not found in scripts, skills, or config file sets. Hook event wiring is not implemented in any inspected area. EVIDENCED: exact substring searches returned 0 matches across all file sets.
- `hook` appears in scripts (2 matches), skills (3 matches), and config (2 matches) — the concept is referenced but not wired to Claude Code events. EVIDENCED: exact substring searches.
- `.claude/settings.json` is referenced in skills (1 match), confirming it is a recognized configuration path. EVIDENCED: exact substring search.
- References to `CLAUDE.md` exist in the skills file set (5 matches). EVIDENCED: exact substring search.
- Exploration-related guidance in skills is more extensive than initially cataloged: `explore` (6 matches), `before planning` (2), `orient` (4), `before writing` (2), `before implement` (2), `read first` (1), `inspect` (1). Total: 18 matches across 7 phrasings. In scripts: `explore` (1), `inspect` (2). EVIDENCED: exact substring searches.
- `enable-tools` appears in the scripts file set (1 match). EVIDENCED: exact substring search.
- No `audit_log` table exists. All `count_records` and `get_recent_costs` queries return "no such table." EVIDENCED: tool query results. No operational data is available to quantify the frequency of the target failure modes.
