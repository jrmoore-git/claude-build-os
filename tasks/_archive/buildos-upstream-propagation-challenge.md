---
debate_id: buildos-upstream-propagation
created: 2026-03-30T12:56:05-0700
mapping:
  A: gemini-3.1-pro
  B: gpt-5.4
  C: gemini-3.1-pro
---
# buildos-upstream-propagation — Challenger Reviews

## Challenger A — Challenges
## Challenges
1. RISK MATERIAL: Relying purely on directory structure to maintain clean framework files is fragile without enforcement. If a developer accidentally hardcodes a project-specific path or concept into a file in `.claude/rules/`, the dumb `buildos-sync.sh` script will blindly push proprietary or context-breaking data upstream. You need a linting step or CI check to verify framework files remain generic.
2. ASSUMPTION MATERIAL: The proposal assumes the underlying tool (Claude Code) natively understands and correctly prioritizes the proposed override directory structures (e.g., merging `.claude/rules/` and `.claude/rules/reference/` without conflicting instructions or context bloat). 
3. ALTERNATIVE ADVISORY: Instead of a custom `buildos-sync.sh`, you could manage the framework layer as a Git submodule or subtree. This would natively track upstream history, handle merges, and eliminate the need to maintain custom synchronization tooling.

## Concessions
1. Shifting from convention-based boundaries to structural (directory-based) boundaries is the correct architectural move for maintaining a clean upstream.
2. Avoiding complex AST parsing or regex-based generalization transforms drastically reduces the maintenance burden and failure rate of the sync process.
3. The layered override pattern allows downstream projects to iterate rapidly without waiting for upstream changes.

## Verdict
APPROVE, provided CI/linting checks are added to prevent project-specific leakage into the framework directories.

---

## Challenger B — Challenges
## Challenges
1. [ASSUMPTION] [MATERIAL]: The proposal assumes directory separation is sufficient to enforce the trust boundary between reusable framework content and project-specific/private content, but nothing here verifies contents. A framework file can still accidentally include project identifiers, internal URLs, credentials, customer data, or repo-specific prompts even if it lives under `.claude/rules/` or `.claude/skills/`; a blind `buildos-sync.sh` copy would then exfiltrate that upstream to GitHub.

2. [UNDER-ENGINEERED] [MATERIAL]: The sync path is a data exfiltration boundary and needs explicit guardrails. There is no mention of pre-sync scanning for secrets, internal hostnames, proprietary names, or denylisted patterns, nor of a review gate/diff check before publish. Given this copies from production-derived assets into a public/shared repo, automated scanning and human approval are important.

3. [UNDER-ENGINEERED] [MATERIAL]: “Framework files never contain project-specific references” is stated as a rule, but the enforcement mechanism is only structural, not technical. If this is meant as “structural boundary enforcement,” you likely need CI/presubmit checks that fail when framework-layer files reference project-only paths, domains, repo names, environment variables, or override directories. Without that, the boundary is aspirational.

4. [RISK] [ADVISORY]: Hooks and scripts are executable content, not just text. Syncing them upstream increases supply-chain impact if a downstream-specific hook contains unsafe shelling, broad filesystem access, or network calls. Even if intentional, publishing these scripts encourages reuse elsewhere, so a lightweight security review standard for synced executable files would reduce propagation of unsafe patterns.

5. [ASSUMPTION] [ADVISORY]: The proposal assumes upstream and downstream have compatible privilege/trust models. A rule or hook that is safe in OpenClaw’s environment may be over-privileged or data-leaky when consumed by other BuildOS users. Reusable framework components should be reviewed against the lowest-trust expected deployment, not just the originating project.

## Concessions
- The proposal correctly identifies the main failure mode: manual “generalization” across a blurry boundary is error-prone and blocks propagation.
- Separating framework vs. project customization by directory structure is a sound simplification and should reduce accidental coupling.
- Keeping project-specific customization in explicit override locations is a good pattern for minimizing contamination of reusable assets.

## Verdict
REVISE — the architecture is directionally sound, but the upstream sync boundary needs content validation and publish-time safeguards to prevent leakage of project-specific or sensitive material.

---

## Challenger C — Challenges
## Challenges
1. [RISK] [MATERIAL]: Accidental leakage of project specifics. By relying purely on developer discipline to keep framework directories "clean," you guarantee that someone moving fast will eventually hardcode an OpenClaw-specific reference or secret into a framework file. The "simple sync script" will then blindly push this to the public upstream repo. The sync process must include a validation step (e.g., grepping for known project terms or running a linter) before copying.
2. [ASSUMPTION] [ADVISORY]: Assumes the override architecture is ergonomic for daily downstream development. If overriding a framework skill requires excessive boilerplate or complex inheritance chains, developers will bypass the system and edit the framework files directly, defeating the purpose of the redesign.
3. [ALTERNATIVE] [ADVISORY]: Instead of forcing a strict physical directory separation that might complicate downstream project structure, you could use inline pragmas (e.g., `# BUILDOS-EXCLUDE-START`) within the files and have the sync script strip those sections. This might be less disruptive to the existing downstream workflow.

## Concessions
1. Correctly identifies the root cause of the sync bottleneck (intermingled framework and project code) rather than just treating the symptom.
2. Leverages an existing pattern (`.claude/rules/reference/`) rather than inventing a completely new paradigm from scratch.
3. Delivers high value to the open-source community by unlocking 4 months of battle-tested improvements.

## Verdict
REVISE to include automated validation/linting in the sync script to prevent accidental leakage of downstream proprietary code into the upstream public repository.

---
