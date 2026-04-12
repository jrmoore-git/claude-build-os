# Explore Intake — Validation Log

Extracted from explore-intake-refined.md during the 4/5 -> 5/5 rewrite. This is the test history, not the protocol.

## Round 1 (6 personas)
6-persona simulated test. Tested all 3 non-skip clarity tiers across engineering, career, product strategy, organizational, startup, and M&A domains.

**Aggregate score: 4.7/5.** 10 protocol amendments (A1-A10) applied. Key validated strengths: assumption challenge, push-once rule, one-question-per-message pacing, context block template. Post-test tone pass: stripped therapy/coaching patterns, rewrote to match observed user text features only.

## Pass 1: Realism (9 personas, product-building-focused)
9-persona test against the amended protocol. Focused on actual audience: product builders, founders, VCs, engineers, CTOs. De novo products, feature scoping, enhancement/rebuild, portfolio strategy, research.

**Result: 9/9 "would come back."** Scores: challenge 4.9/5, Q count 5.0/5, register 4.3/5 (-> 4.5 after Voice & Register section), flow 4.4/5. 22 additional amendments applied. Key additions: binary decision classification (SP1), risk variant (S2-1), stakeholder/alignment/clock probes (P1/P5/P3), stuck/exploring distinction (A3), bomb rule (SP2), recap anti-pattern examples (R1), hypothetical exemption (SP3), relative progress cues (SP4).

## Pass 2: End-to-End (3 tests -- intake through explore output)
Verified that intake quality produces genuinely divergent, actionable explore directions.

**Result: 3/3 "would show to board/team."** Scores: intake 4.7/5, register 4.0/5, context block 5.0/5, direction divergence 5.0/5, direction quality 4.0/5, synthesis 4.3/5. Added 5 Direction & Synthesis Quality Rules. Key finding: "who disagrees" was the highest-rated synthesis row in every test.

## Pass 3: Adversarial (3 edge cases)
Tested contradiction, mid-intake bail, and solution-seeking.

| Test | Score | Outcome |
|------|-------|---------|
| Contradictory inputs | 3.9/5 -> fixed | Added direct contradiction handling (Delivery Rule #8). |
| Skip-signal/bail | 3.0/5 -> fixed | Added sufficiency gate to skip path. |
| Solution-seeker | 4.6/5 | Anti-solutioning held. Fixed question backbone IS the redirect. |

Key insight: edge cases reveal structural gaps in data quality and composition, not personality management issues.

## Pass 4: Delta Proof (2 A/B tests -- with vs. without intake)
Same prompt run with full intake vs. raw input only, scored by blind evaluator.

| Criterion | Without intake | With intake | Delta |
|-----------|---------------|-------------|-------|
| Direction relevance | 1.5/5 | 5.0/5 | +3.25 |
| Actionability | 1.5/5 | 4.5/5 | +3.0 |
| Dimension coverage | 2.0/5 | 4.5/5 | +2.5 |
| Assumption surfacing | 2.5/5 | 5.0/5 | +2.5 |
| User-specific framing | 2.5/5 | 4.5/5 | +2.0 |
| **Average** | **2.0/5** | **4.7/5** | **+2.67** |

**Verdict:** "The intake is not a nice-to-have. It is the difference between output a founder skims and output a founder acts on."

## Pass 5: Cross-Model Evaluation + Persona Simulations

**Cross-model evaluation (Rounds 12-17):**
- Register: 3/3 consensus at 4/5 (Claude, GPT, Gemini) -- Rounds 15-16
- Flow: 2/3 consensus at 4/5 (Claude + Gemini; GPT oscillated 3-4) -- Rounds 15-17
- GPT's flow dissent: wants radically simpler protocol (one rule, zero sub-rules). Design-taste difference, not a fixable bug.

**5-persona simulation results:**

| Persona | Problem | Register | Flow | Failure mode |
|---------|---------|----------|------|-------------|
| Elena, 38, Series B CEO | SMB-to-enterprise GTM pivot | 4/5 | 5/5 | One filler word missed in uncertain territory |
| Raj, 44, CTO | Monolith-to-microservices timing | 5/5 | 5/5 | -- |
| Kenji, 31, solo founder | Take VC or stay bootstrapped | 4/5 | 5/5 | Interviewer slightly too clean for the input |
| Maya, 50, VP Product | Developer ecosystem vs. first-party features | 4/5 | 4/5 | One question too many -- sufficiency should have fired earlier |
| Dara, 27, first-time PM | Kill underperforming feature or iterate | 4/5 | 5/5 | One question slightly too polished for the input |
| **Average** | | **4.2/5** | **4.8/5** | |

## Sources

### Questioning techniques
- Socratic questioning: PMC4449800 (CBT outcome data), PMC4174386 (educational outcomes)
- Motivational Interviewing: PMC8200683 (meta-analysis OR=1.55), NCBI NBK571068 (OARS)
- JTBD: Dscout (Four Forces), IDEO U (empathy interviews)
- GROW coaching: Simply.Coach, ICF competency framework
- CBT downward arrow: Therapist Aid
- Journalism funnel: NNg, GIJN, FBI elicitation (CDSE)
- Clean Language: Businessballs
- Mom Test: TianPan.co summary, ReadingGraphics summary
- Cognitive interview: Simply Psychology (35-50% more correct recall)

### LLM prompt design
- Context rot: Chroma Research (performance degrades with length)
- Hidden in the Haystack: arXiv 2505.18148 (smaller gold context = worse performance)
- Lost in the Middle: Stanford/MIT TACL (U-shaped attention)
- Focused CoT: arXiv 2511.22176 (structured input > CoT instruction)
- Structured vs. narrative: ImprovingAgents (YAML > XML > JSON), Lamarr Institute (Story of Thought)
- Persona prompting: arXiv 2603.18507 PRISM study (personas improve writing, damage factual accuracy)
- Instruction following: arXiv 2507.11538 (threshold/linear/exponential decay patterns)
- Anthropic Claude 4 best practices, OpenAI GPT-4.1/5 guides

### AI product patterns
- OpenAI Deep Research: 3-6 pivotal unknowns, separate clarification model
- Typeform: 47.3% completion (3.5x standard forms), <6 question ceiling
- "Curiosity by Design": arXiv 2507.21285 (82% preferred clarified output, Cohen's d > 0.8)
- "Ask or Assume?": arXiv 2603.26233 (69.4% vs 61.2% resolve rate, 3.06 avg queries)
- HBR 2026: AI over-asks investigative, under-asks productive/subjective (1,600 executives, 13 LLMs)
- Google Research 2025: RLHF bias toward "complete but presumptuous answers"
- Question-Behavior Effect: meta-analysis g=0.14 across 116 studies
