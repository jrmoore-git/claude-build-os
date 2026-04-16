---
mode: pre-mortem
multi_model: true
created: 2026-04-15T21:43:26-0700
models: [gpt-5.4, claude-opus-4-6, gemini-3.1-pro]
synthesis_model: gpt-5.4
prompt_version: 1
mapping:
  A: gpt-5.4
  B: claude-opus-4-6
  C: gemini-3.1-pro
---
# Pre-Mortem (Multi-Model)

## Analyst A

1. **The `--critique` loop shipped, got used for a few skills, and then was abandoned because extracted directives consistently improved style/procedure but did not move hidden_truth or final shipped skill quality.**  
   - **Type:** Strategy failure  
   - **Warning sign visible today:** You already have evidence that turn-hook intervention improved procedural dimensions while **hidden_truth stayed broken with 80% failure**. This plan still converts critique into a **single injected system reminder at turn 1 only**, which is structurally similar to the intervention mode that already failed.  
   - **What would have prevented it:** Before implementation, require a **3-skill bakeoff**: for one known-good skill and two weak skills, run baseline vs `--critique` for at least 5 annotated iterations each and measure whether hidden_truth and overall judge score improve by a preset threshold, not just whether directives “look reasonable.”  
   - **Would prevention have changed the plan?** Yes. If the bakeoff failed, the team should **not build this feature as planned**; it would mean the critique-to-directive-to-hook loop is the wrong mechanism.

2. **The LLM directive extractor became a lossy translation layer: developer annotations were nuanced, but `extract_directives()` compressed them into 3–7 generic instructions that erased the actual insight, causing repeated non-improving loops.**  
   - **Type:** Execution failure  
   - **Warning sign visible today:** The plan explicitly uses **Haiku** for extraction, returns only `list[str]`, and has no schema for evidence, source quote, target failure mode, or confidence. That means rich annotations get flattened into short imperatives with no traceability.  
   - **What would have prevented it:** Change the planning-stage design so extraction returns structured items like `{directive, source_quote, rationale, target_dimension}` and require a **human approval/edit step** before applying them. Also test extractor fidelity on 20 hand-annotated examples.  
   - **Would prevention have changed the plan?** It would change the implementation materially, but not necessarily kill the project. The current plan is too lossy.

3. **Silent failure mode poisoned iteration: API or parsing failures in `extract_directives()` returned empty lists, the pipeline continued “without critique,” and the developer mistakenly interpreted no improvement as critique ineffectiveness rather than a no-op run.**  
   - **Type:** Execution failure  
   - **Warning sign visible today:** The plan says: **“On LLM failure: print error, return empty list (pipeline continues without critique)”**. That is a textbook silent-degradation path in an experiment loop.  
   - **What would have prevented it:** Make `--critique` **fail closed** by default: non-empty directives required unless `--allow-empty-critique` is explicitly passed. Also write the extracted directives to an artifact file and stamp the run metadata with `critique_applied=true/false` plus directive count.  
   - **Would prevention have changed the plan?** No, but it would change default behavior and likely save months of misleading results.

4. **The feature created a local optimization trap: the team used before/after score diffs from prior `pipeline_report.json` to steer iteration, but because the rubric and simulator were imperfect proxies, the system got better at pleasing the judge rather than improving real skill performance.**  
   - **Type:** Strategy failure  
   - **Warning sign visible today:** The project already learned that **rubric dimensions must measure product outcomes, not interaction style**. Yet this plan’s feedback loop is still centered on **sim score diffs** and transcript annotations, not external product outcomes or deployment performance.  
   - **What would have prevented it:** Define, before coding, a **promotion gate tied to real product outcomes**: e.g., a skill only “improves” if critique-driven changes raise both sim score and an external acceptance test or manual blind review score.  
   - **Would prevention have changed the plan?** Yes. It would make this a support tool for human iteration, not the primary optimization target.

5. **The project lost another 6 months because this “small” feature bypassed the challenge gate and quietly reopened V2 scope expansion under a safer name.**  
   - **Type:** Sequencing failure  
   - **Warning sign visible today:** The front matter explicitly says **`challenge_skipped: true`**, while prior decision **L27** says scope expansion requires a new challenge gate and D22 says stop V2 pipeline maintenance. This is exactly the kind of “just one more improvement” that bypasses governance.  
   - **What would have prevented it:** Enforce the challenge gate at planning time: require a written answer to “Is this maintenance of proven workflow, or a new bet on generalized critique automation?” plus a kill criterion and a one-week spike cap.  
   - **Would prevention have changed the plan?** Possibly yes. It may have reframed this as a **time-boxed experiment**, not a committed implementation.

## The Structural Pattern

These failures share one assumption: that the value from `eval_intake.py`’s 17 manual iterations can be captured by a lightweight translation layer that converts annotations into reusable system directives inside the existing sim pipeline. That assumption appears repeatedly: critique is treated as compressible, transferrable, and measurable through the simulator. The pattern is mostly a **sequencing problem with strategy implications**: the team is trying to productize the critique loop before proving that the specific mechanism—annotation → extraction → turn-1 directive—actually reproduces the benefits of human watching-and-fixing. This should **change the plan**: downgrade from implementation commitment to gated experiment, add hard monitoring for no-op runs and proxy-vs-reality divergence, and be willing to kill the effort quickly.

## The One Test

Run a **one-week, 3-skill prospective bakeoff** next week:

- Pick 3 skills: one strong baseline, one medium, one with known hidden_truth weakness.
- For each, do 5 runs baseline and 5 runs with `--critique`.
- Use real annotated transcripts from the developer, not synthetic annotations.
- Require the extractor output to be reviewed and frozen before each critique run.
- Measure:
  1. overall sim score,
  2. hidden_truth specifically,
  3. external/manual blind rating of the resulting skill revision,
  4. rate of empty/low-quality directives.

**Pass condition:** critique must improve hidden_truth and overall quality on at least 2 of 3 skills without degrading manual blind review. If it fails, do not proceed with this plan.

---

## Analyst B

# Pre-Mortem: Iterative Critique Loop (D22)

---

## Failure Scenario 1: "Critique Laundering" — LLM extraction flattens developer insight into generic directives

**What happened:** `extract_directives()` using Haiku consistently converts specific, nuanced developer annotations like "> The executor ignored the user's emotional state here and jumped to solution mode" into generic directives like "Be attentive to user emotions." These laundered directives, injected at turn 1 as system reminders, produce no measurable change in executor behavior. After 4 critique iterations, scores remain at 3.70. The developer concludes the critique loop doesn't work and abandons it.

**Type:** Execution failure.

**Warning sign visible today:** The 17 iterations that made eval_intake score 4.73 involved direct prompt edits to the skill itself — not injected system reminders to the executor at runtime. The plan assumes directives-as-system-reminders approximate what prompt-editing accomplished. No evidence supports this assumption. You can check: compare what changed between eval_intake iterations (prompt text diffs) vs. what `critique_hook` would inject (runtime context).

**Prevention:** Before building steps 3-5, run a manual test: hand-write 5 specific directives based on a real transcript, inject them via the existing turn_hook interface, and measure whether scores move. If they don't, the entire extraction pipeline is moot.

**Would prevention change the plan?** Yes — if injected directives don't move scores, the plan's core mechanism is wrong. The critique loop should modify the skill prompt or persona config, not inject runtime reminders.

---

## Failure Scenario 2: "Hidden_truth stays broken at 80% failure regardless of critique"

**What happened:** hidden_truth failures stem from the persona not revealing information the executor needs to discover — a structural property of persona prompt formatting. Developer annotations correctly identify the problem ("the persona should have hinted at X here") but directives targeting the executor can't fix persona behavior. After months, hidden_truth remains the dominant quality gap, and overall scores plateau at ~4.0.

**Type:** Strategy failure.

**Warning sign visible today:** Session 17 data explicitly shows hidden_truth at 80% failure while procedural dims hit 5.0. The plan only modifies executor behavior via critique_hook. No mechanism in the plan touches persona behavior. L30 already says "persona format + mid-loop interventions resist generalization."

**Prevention:** Scope the critique loop to include persona directives — a second hook or persona config modifications — or explicitly descope hidden_truth and set a target ceiling (e.g., 4.2/5 without hidden_truth improvement).

**Would prevention change the plan?** It would expand it. The plan as written cannot close the gap it was designed to close.

---

## Failure Scenario 3: "Solo developer never actually iterates"

**What happened:** The workflow requires: run sim → read markdown → annotate with blockquotes → run extract_directives → run sim again → compare scores. The solo developer does this twice, finds it tedious (each cycle is 5-10 minutes of reading + annotating + waiting for sim runs), and never builds the habit. The --critique flag ships, tests pass, and it's used 3 times total before being forgotten. Six months later, new skills still ship at V1 quality.

**Type:** Execution failure.

**Warning sign visible today:** eval_intake's 17 iterations happened with direct prompt editing — a tight feedback loop (edit → run → see result). The proposed loop adds two intermediate steps (annotate markdown, extract directives). The developer's actual iteration pattern is visible in git history. Check: how long did each of the 17 eval_intake iterations take? If it was <2 min each, and this loop is >5 min each, adoption will fail.

**Prevention:** Cut the annotation→extraction steps. Instead, let the developer pass directives directly: `--critique "don't jump to solutions" "probe emotional state"`. Add the markdown/extraction path later if the direct path proves useful.

**Would prevention change the plan?** Yes — it simplifies steps 3-4 significantly and ships a usable tool faster.

---

## Failure Scenario 4: "Score comparison gives false confidence"

**What happened:** Step 5's before/after diff shows improvement (3.70→4.20), but the variance across runs is ±0.5 due to LLM non-determinism. The developer interprets noise as signal, "validates" ineffective directives, and bakes bad patterns into skill prompts. Quality degrades on dimensions that aren't measured by the current rubric.

**Type:** Execution failure.

**Warning sign visible today:** Session 17 ran only 5 trials. No confidence intervals were reported. The plan's score comparison shows single-run deltas with no statistical framing.

**Prevention:** Require minimum 3 runs per critique iteration and display mean ± std. Flag deltas smaller than 1 standard deviation as "inconclusive."

**Would prevention change the plan?** Minor addition to Step 5. Easy fix.

---

## The Structural Pattern

These failures share one assumption: **that the quality gap between eval_intake (4.73) and V2 (3.70) can be closed by modifying executor runtime behavior through injected directives, rather than by modifying the artifacts themselves (skill prompts, persona configs, rubric definitions).** Eval_intake's 17 iterations changed the prompt text directly. This plan interposes an extraction layer and a runtime injection layer between developer insight and the artifact, diluting the signal at each step. This is fundamentally a strategy problem — the mechanism of action is misidentified. The plan should either (a) make the critique loop modify skill/persona prompts directly, or (b) prove that runtime directive injection moves scores before building extraction infrastructure.

## The One Test

**Hand-craft 5 specific directives from an existing low-scoring transcript. Inject them manually via the existing turn_hook interface (no new code). Run 3 trials with directives and 3 without. Compare mean scores per dimension.** If the delta on hidden_truth is <0.5 and overall delta is <0.3, runtime injection doesn't work and the plan needs a different mechanism. This takes one afternoon and zero new code.

---

## Analyst C

### 1. Haiku Annotation Extraction Yields Generic Directives
**Classification:** Execution failure.
**Warning Sign visible TODAY:** Step 3 specifies "Default model: haiku (cheap, classification-grade task)". Converting human inline frustration (e.g., "> Why didn't it ask about the API key here?") into a generalized, reusable system prompt directive is a complex reasoning task, not a classification task.
**Prevention:** Hardcode the default extraction model to Sonnet 3.5, or bypass the LLM extraction entirely by requiring the developer to write the final directives in a specific YAML block at the top of the markdown file.
**Would prevention change the plan?** Yes. It removes Step 3 entirely, replacing LLM extraction with direct developer input, saving complexity and reducing unpredictability.

### 2. Turn 1 Directives Fade Before Late-Stage Failures
**Classification:** Strategy failure.
**Warning Sign visible TODAY:** Step 2 states: "Injects all directives as a single system reminder at turn 1 only." The context notes that the primary failing dimension is `hidden_truth` (80% failure rate). `hidden_truth` failures typically occur late in a conversation when the agent prematurely concludes. A Turn 1 reminder will likely fall out of the model's active attention window by Turn 5.
**Prevention:** Change the injection mechanism. Instead of a Turn 1 system reminder, append the critique directives to the system prompt for *every* turn, or use a persistent scratchpad.
**Would prevention change the plan?** Yes. Step 2's hook logic must be rewritten to modify the persistent system context rather than injecting a one-time simulated turn.

### 3. Workflow Friction Leads to Abandonment After 3 Skills
**Classification:** Execution failure.
**Warning Sign visible TODAY:** The workflow requires exporting to markdown, manually typing `> ` blockquotes between specific turns, saving, and running a CLI command with specific file paths (`--critique annotated.md`). For a solo developer managing 23 skills, this file-juggling loop is too slow compared to just editing the core system prompt directly.
**Prevention:** Build a simple interactive CLI review mode instead of relying on external file editing. After a sim fails, the CLI prompts: "Review transcript? [Y/n]", prints turns sequentially, and allows typing a critique right then, saving directly to a `skill_critiques.json` file.
**Would prevention change the plan?** Yes, it entirely scraps the markdown export/import file IO in favor of an interactive terminal loop.

***

## The Structural Pattern
These failures share a core assumption: **that static text interventions can reliably steer dynamic, multi-turn LLM behavior without friction.** The plan assumes an LLM (Haiku) can perfectly translate human inline notes into prompt engineering, and that injecting those notes once at the start will fix late-conversation drift. This is fundamentally a **strategy problem (wrong bet)**. The team correctly identified that automation can't replace human iteration (L30), but they are still trying to automate the *translation* of that iteration via Step 3, and relying on weak prompt-injection mechanisms (Turn 1 only). This pattern suggests the plan should be simplified: remove the LLM middleman and let the developer write the persistent prompt directives directly.

## The One Test
**The Turn 1 Fade Spike:** Before building the extraction pipeline, manually write 5 highly specific directives designed to fix the `hidden_truth` failure in the V2 pipeline. Hardcode these directives into a Turn 1 injection (simulating Step 2). Run 5 simulations. If the agent still fails `hidden_truth` at the end of the transcript because it "forgot" the Turn 1 directives, the entire injection architecture is flawed, and building the markdown extraction tooling (Steps 1, 3, 4, 5) is a waste of time.

---

## Synthesis

**Agreements — high-confidence risks**

1. **Core mechanism likely won’t move the right outcomes.**  
   All three analysts independently question the plan’s main path: *annotation → extracted directives → one-time Turn 1 system reminder*.  
   - A: this is “structurally similar” to prior turn-hook intervention that improved style/procedure but not `hidden_truth`.  
   - B: eval_intake gains came from **editing prompts/artifacts directly**, not runtime reminders.  
   - C: Turn 1 directives likely “fade” before late-stage failures.  
   This is the strongest finding because it is grounded in the proposal itself: Step 2 injects once at turn 1; Step 3 only targets executor instructions; the known weak dimension is `hidden_truth`.

2. **Directive extraction is too lossy / generic.**  
   A, B, and C all say the LLM extraction step may flatten nuanced annotations into bland advice. Evidence is strong: Step 3 returns only `list[str]`, targets 3–7 directives, and defaults to **Haiku**. There’s no traceability, schema, rationale, or approval gate.

3. **Workflow friction may kill adoption.**  
   B and C both identify the manual markdown annotation loop as likely too cumbersome for a solo developer versus just editing prompts directly. This is plausible because the proposed loop adds export/edit/re-run/extract/compare steps.

**Disagreements**

1. **Should extraction use a stronger model or be removed entirely?**  
   - C: switch from Haiku to Sonnet or require developer-authored YAML directives.  
   - A: keep extraction but add structure and human approval.  
   - B: don’t build extraction yet; test manual directives first.  
   **Stronger evidence:** B/A. The bigger risk isn’t model quality alone; it’s whether extracted runtime directives work at all. Upgrading Haiku may improve fidelity, but doesn’t solve the mechanism problem.

2. **Can the plan be salvaged by better injection, or is the whole direction wrong?**  
   - C: rewrite Step 2 so directives persist every turn.  
   - B: probably wrong mechanism; should modify skill/persona artifacts instead.  
   **Stronger evidence:** B. The proposal explicitly affects only `sim_driver.py`/`sim_pipeline.py`, not skill/persona artifacts, while prior success came from artifact edits and `hidden_truth` appears persona-linked.

**Unique findings — blind spots only one analyst caught**

1. **Silent no-op failure mode** — only A.  
   Step 3 says on LLM failure: “print error, return empty list (pipeline continues without critique).” That could poison experimentation by making failed extraction look like ineffective critique. This is a very valuable catch.

2. **Score-comparison noise / false confidence** — only B.  
   Step 5 prints before/after deltas from prior `pipeline_report.json`, but single-run score changes may just be variance. This is a concrete measurement-risk blind spot.

3. **Governance / challenge gate bypass** — only A.  
   The front matter says `challenge_skipped: true`. A argues this may be disguised scope expansion. This is credible process risk, though less central than the mechanism issue.

**Likely false positives / weaker claims**

- A’s “lost another 6 months” framing is speculative; the proposal is only ~120 lines. The governance concern is fair, but the magnitude claim isn’t supported.
- C’s “falls out of active attention window by Turn 5” is plausible but mechanistic speculation; the stronger point is simply that late failures may not be fixed by one-time early reminders.
- B/C’s “abandonment after 3 skills” is plausible but unsupported by direct usage data in the proposal.

**Overall assessment — top 3 risks**

1. **Wrong intervention target:** the plan steers executor runtime behavior, but the known gap (`hidden_truth`) may be rooted in persona/prompt/artifact design.  
2. **Weak translation layer:** nuanced developer critique gets compressed into generic, untraceable directives, especially with `list[str]` + Haiku.  
3. **Misleading experimentation loop:** silent no-op extraction and noisy single-run score diffs could make the team draw false conclusions about whether critique helps.