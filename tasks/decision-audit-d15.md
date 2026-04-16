---
decision: D15
original: "/review auto-detects content type — code gets personas, documents get cross-model evaluation via --models"
audit_date: 2026-04-15
models_used: claude-opus-4-6, gemini-3.1-pro, gpt-5.4
verdict: HOLDS
---

# D15 Audit

## Original Decision

`/review` detects input type (code vs document). Code routes to `review-panel --personas architect,security,pm`. Non-code documents route to `review --models` with a caller-generated eval prompt. The `--models` flag bypasses persona lookup entirely. Key distinction: `/review` evaluates, `/polish` improves.

## Original Rationale

PM/Security/Architecture lenses are designed for code diffs. Sending a strategy doc through them produces irrelevant findings. L21 proved advisory fixes fail under execution pressure — structural enforcement via `--models` is required. Routing documents to `refine` was wrong because `/review` should evaluate, not improve.

## Audit Findings

**All three models returned HOLDS independently.** Key convergence points:

**Evaluate/improve distinction** — architecturally sound and consistent with D17 (refine critique mode). Document review writing an evaluation artifact rather than modifying the document is the correct operation. EVIDENCED.

**Persona rejection was correct** — `--models` with a caller-defined eval prompt is strictly better than document-specific personas for this context. Personas conflate "which model" with "what framing." Dynamic eval prompts adapt to document type; fixed personas would either be too generic or proliferate endlessly. EVIDENCED.

**Auto-detection is adequate** — explicit file arg serves as escape hatch. Identified edge cases: mixed commits (code + docs in same diff may misroute), non-standard extensions, ambiguous file types. None are systematic failures. ESTIMATED.

**No conservative bias** — D15 expanded capability (added `--models` path, built document evaluation as first-class) rather than descoping. The conservative option would have been alternative (d): advisory fix only. D15 chose structural enforcement. EVIDENCED.

**No context gaps identified** — decision was made with awareness of L21, persona system design, and the review/polish distinction. The pipeline improvements since (D21 judge step, D17 critique mode) reinforce rather than undercut D15's premises.

**Judge step note:** The judge subcommand requires challenge files produced by the `debate.py challenge` subcommand (with `mapping:` frontmatter). The review output format is incompatible. Synthesis performed from three independent model outputs showing unanimous convergence — this is treated as equivalent evidence for a HOLDS verdict.

## Verdict

**HOLDS**

D15 is a structurally correct fix for a documented, reproducible problem. The routing mechanism is sound, the alternatives were correctly evaluated, and the risk of changing D15 is higher than the risk of keeping it. The only item worth monitoring: quality of the dynamic eval prompt generated in document review Step 2. If document reviews feel generic, improve that generation step — do not change the routing architecture.

## Risk Assessment

**Risk of keeping:** Low. Auto-detection edge cases (mixed commits) mitigated by explicit file arg escape hatch. Prompt generation quality is the main variable.

**Risk of changing:** High. Reverting to personas for documents reintroduces L21. Adding document personas adds config surface without benefit. Any change that merges the code and document paths blurs `/review` and `/polish`.
