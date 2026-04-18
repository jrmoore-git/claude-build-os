---
scope: "Phase 0x (orchestration-readiness scaffold) + Phase 0a (baseline judge error rate measurement). Pre-gate the larger judge-stage Frame-reach audit — if Phase 0a yields <5 baseline errors on the Round 2 corpus, audit defers pending passive corpus growth; no synthesis. All later phases (0c, 0d, 0e, 1, 3) deferred to plan-v2 after Phase 0a outcome is known."
surfaces_affected: "scripts/judge_frame_orchestrator.py, tasks/judge-stage-frame-reach-audit-runs/, tasks/judge-stage-frame-reach-audit-results.md, tasks/lessons.md"
verification_commands: "python3.11 scripts/judge_frame_orchestrator.py --help && ls tasks/judge-stage-frame-reach-audit-runs/phase0a-baseline-*.md | wc -l"
rollback: "git revert HEAD for scripts/judge_frame_orchestrator.py; rm -rf tasks/judge-stage-frame-reach-audit-runs/ to discard research runs"
review_tier: "Tier 2"
verification_evidence: "PENDING"
related_proposal: "tasks/judge-stage-frame-reach-audit-proposal.md"
related_design: "tasks/judge-stage-frame-reach-audit-design.md"
related_challenge: "tasks/judge-stage-frame-reach-audit-challenge.md"
challenge_recommendation: "PROCEED-WITH-FIXES"
frame_structural_model: "gemini-3.1-pro"
frame_factual_model: "gpt-5.4"
specificity_floor: 0.80
aggregation_rule: "structural vetoes factual-only findings. Additionally: a finding whose only novel substantive content is a factual claim unsupported by the structural pass is discarded entirely, even if structural co-signs a different aspect."
corpus_policy: "organic-first — Round 2 frame-lens-validation proposals only. No synthesis in v1. If <5 organic baseline errors, defer 2-4 weeks for passive corpus growth."
data_egress_policy: "Corpus eligibility: Round 2 in-repo proposals only (trusted content). Results artifacts store proposal IDs + ≤200-char excerpts. Phase 0x grep-scans corpus for credential patterns before any run."
escalations_deferred:
  - "Challenge 6 (trust boundary / prompt injection) — mitigated by trusted-corpus-only scoping for v1"
  - "Challenge 9 (factual mode cost) — Phase 0c measures signal rate; decision after data"
  - "Challenge 15 (subcommand vs flag) — Phase 3 only, not this plan"
---

# Plan: Judge-Stage Frame-Reach Audit — Phase 0x + Phase 0a

## Build Order

### Phase 0x — Orchestration-Readiness Gate (blocks Phase 0a)

1. **Create `scripts/judge_frame_orchestrator.py`** (~80 LOC).
   - CLI: `--judge-output <path> --proposal <path> --challenge <path> --output <path> [--frame-structural-model <name>] [--frame-factual-model <name>]`
   - Reads judge output + proposal + challenge output.
   - Runs frame-structural (default `gemini-3.1-pro`, tools OFF) on (judge_output + proposal + challenge_output) → writes critique A.
   - Runs frame-factual (default `gpt-5.4`, tools ON with `check_code_presence` + `read_code_snippet`) on same inputs → writes critique B.
   - Applies pre-committed aggregation rule (structural vetoes factual-only) → produces final REJECT/PROCEED assessment.
   - Output: single markdown file with frontmatter (models, verdict, timing) + both critiques + final assessment.
   - Reuses `scripts/debate_common.py` for LLM dispatch. NO modification to `scripts/debate.py`.

2. **Family-overlap enforcement.** Before any run, orchestrator reads proposal author (from proposal frontmatter if present) and compares family (anthropic/openai/google) to frame-structural family. Raises SystemExit if same. Hardcoded family map in script.

3. **Corpus data-classification pre-check.** Before any run, grep target proposal + judge output for credential patterns (`AKIA[0-9A-Z]{16}`, `sk-[a-zA-Z0-9]{20,}`, `-----BEGIN [A-Z ]+PRIVATE KEY-----`). Exit with error + filename if match.

4. **Smoke test:** Run orchestrator on one Round 2 archived debate output → verify output file written, no exceptions, aggregation produces REJECT or PROCEED.

5. **Phase 0x GATE:** Smoke-test exits 0 + valid output → proceed. Any failure → stop + escalate.

### Phase 0a — Baseline Judge Error Rate Measurement

6. **Assemble corpus:** identify 5 Round 2 frame-lens-validation archived debate outputs (autobuild, explore-intake, learning-velocity, streamline-rules, litellm-fallback). Document paths in results.md.

7. **Rerun baseline `cmd_judge`** on each of 5 debate outputs using current `judge_default` (`gpt-5.4`). Write to `tasks/judge-stage-frame-reach-audit-runs/phase0a-baseline-<slug>.md`.

8. **Tag against Round 2 ground truth.** For each proposal: compare baseline judge verdict (PROCEED/REVISE/REJECT) vs Round 2 labeled correct verdict. Record class: `correct | missed_disqualifier | false_dismiss | collapsed_defect`. Only `missed_disqualifier` counts for primary metric.

9. **Phase 0a GATE:**
   - ≥5 missed-disqualifier errors → PROCEED to plan-v2 (audit premise confirmed).
   - 2-4 errors → DEFER 2-4 weeks for passive corpus growth. Do not run Phase 0c yet.
   - 0-1 errors → DECLINE. Baseline judge reliable enough that Frame-at-judge has no room to add value on this corpus.

10. **Error-shape summary.** Qualitative description of any errors found (severity under-weighting, scope inflation, finding-collapse). Informs future audit design.

### Results + Governance

11. **Write `tasks/judge-stage-frame-reach-audit-results.md`:** corpus paths, per-proposal baseline verdicts vs ground truth, error-class tags, error-shape summary, gate outcome.

12. **Extend `tasks/lessons.md`:** add stage-specific evidence to L43 (PROCEED) OR new entry (DECLINE).

13. **If gate = PROCEED:** plan-v2 drafted in a SEPARATE `/plan` invocation after this plan closes. NOT in this plan's scope.

## Files

| File | Action | Scope |
|---|---|---|
| `scripts/judge_frame_orchestrator.py` | create | Phase 0x scaffold (~80 LOC) |
| `tasks/judge-stage-frame-reach-audit-runs/` | create | Dir for run outputs |
| `tasks/judge-stage-frame-reach-audit-runs/phase0a-baseline-*.md` | create (5) | Baseline judge rerun outputs |
| `tasks/judge-stage-frame-reach-audit-results.md` | create | Corpus + tagging + gate outcome |
| `tasks/lessons.md` | modify | L43 extension or new L46 |

## Execution Strategy

**Decision:** sequential pipeline (Phase 0x → Phase 0a → results).
**Pattern:** pipeline.
**Reason:** Phase 0a depends on Phase 0x orchestration working. Within Phase 0a, the 5 baseline judge reruns are parallelizable at API level but are one logical step.

| Subtask | Files | Depends On | Isolation |
|---|---|---|---|
| Phase 0x scaffold | `scripts/judge_frame_orchestrator.py` | — | main session |
| Phase 0x smoke test | 1 test run | Phase 0x scaffold | main session |
| Phase 0a corpus assembly | results.md | Phase 0x smoke test | main session |
| Phase 0a reruns | 5 baseline files | corpus assembly | main session (parallel Bash) |
| Phase 0a tagging | results.md | reruns | main session |
| Results + L43 | results.md + lessons.md | tagging | main session |

**Synthesis:** Main session applies Phase 0a gate to tagged corpus and writes verdict. No parallel-agent fan-out — linear research pipeline with one conditional exit.

## Verification

```bash
# Phase 0x gate
python3.11 scripts/judge_frame_orchestrator.py --help

# Phase 0a gate — file count
ls tasks/judge-stage-frame-reach-audit-runs/phase0a-baseline-*.md | wc -l
# Expected: 5

# Phase 0a gate — verdict presence
grep -E '^(VERDICT|gate_outcome):' tasks/judge-stage-frame-reach-audit-results.md
# Expected: one of: PROCEED-TO-PLAN-V2 | DEFER | DECLINE
```

## Notes

- Pre-committed values in frontmatter are LOCKED per L45. Changes void the audit and require a new plan.
- Plan is deliberately narrow. Per challenge Finding #14 (3-challenger convergence): no pre-built machinery. Phase 0c/0d/0e/1/3 live in plan-v2.
- Compute estimate: Phase 0x smoke ~30s (2 LLM calls). Phase 0a ~60s (5 parallel judge calls). Dev time for orchestrator ~45-60 min.
- Data-egress constraint operationalized by Step 3 (credential pre-check) + Step 11 (results store IDs + ≤200-char excerpts).
