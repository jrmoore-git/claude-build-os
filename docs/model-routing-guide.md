# Model Routing Guide

Route LLM calls by task type, not by skill name. Default to the cheapest model that handles the task reliably. BuildOS ships with LiteLLM as the routing layer (`scripts/llm_client.py`), model-to-persona mapping (`config/debate-models.json`), and per-skill model overrides in SKILL.md frontmatter. This guide documents the principles and guardrails behind that routing.

---

## 1. Model Selection Principles

Research from RouteLLM (Berkeley LMSYS), IBM Research, and production practitioners converges on four principles:

### Principle 1: Default to the cheapest model that handles the task reliably

Most tasks don't need frontier reasoning. The RouteLLM framework demonstrates 85% cost reduction on MT Bench and 45% on MMLU by routing simple queries to smaller models — while maintaining 95% of GPT-4 quality. Your cheapest capable model should be the default, not the mid-tier.

### Principle 2: Classify by task type, not by skill name

The right model depends on what the LLM is *doing*, not which skill invoked it. See the task classification table in section 2.

### Principle 3: LLMs should only do what only LLMs can do

Classification, summarization, drafting, extraction, analysis. All SQL, API calls, state transitions, routing, and audit logging must be deterministic code. Every token spent on something a Python script could do is wasted.

### Principle 4: Escalate on failure, not by default

Start with the standard-tier model. Escalate to the premium model only when the output is rejected or quality thresholds are not met. Don't preemptively use premium models "just in case."

---

## 2. Task Classification & Routing

| Task Type | Model Tier | Why |
|-----------|-----------|-----|
| **Classification** (tier assignment, urgency scoring, intent routing) | Economy | Binary/categorical output, structured prompt, no reasoning chain needed |
| **Extraction** (action items, entities, structured data from text) | Economy | Pattern matching against structured prompt |
| **Summarization** (digests, recaps, assembly of known facts) | Economy | Short summaries from single sources. Upgrade to Standard for multi-source synthesis |
| **Draft generation** (routine replies, template-based output) | Standard | Needs voice matching, tone calibration, coherent paragraphs |
| **Draft generation** (high-stakes: legal, executive, external) | Premium | Reputation risk, subtle tone requirements |
| **Complex analysis** (multi-doc synthesis, anomaly detection) | Standard | Needs reasoning across multiple inputs |
| **Strategic reasoning** (reviews, learning synthesis, pattern recognition over time) | Premium | Requires judgment, cross-temporal inference |
| **Validation** (state machine checks, schema validation, format checks) | No LLM | Deterministic code. Not an LLM task. |

### BuildOS skill routing defaults

These are the built-in routing decisions. Override per-skill via `model:` in SKILL.md frontmatter or per-persona in `config/debate-models.json`.

| Skill | Task Type | Model Tier | Rationale |
|-------|-----------|-----------|-----------|
| `/challenge`, `/debate`, `/review` | Strategic reasoning | Premium (cross-model) | Adversarial review needs frontier judgment across model families |
| `/refine` | Iterative improvement | Premium (rotating) | 6-round rotation across 3 model families |
| `/plan`, `/define` | Analysis + synthesis | Standard | Needs reasoning but not adversarial pressure |
| `/recall`, `/status` | Summarization | Standard | Assembly from multiple sources |
| `/triage` | Classification | Economy | Categorization with structured output |
| `tier_classify.py` | Classification | Economy | File tier assignment — pure categorization |
| Artifact validation | Validation | No LLM | `artifact_check.py` — deterministic checks |

---

## 3. Budget Math Framework

### Step 1: List your model pricing

| Model | Input / MTok | Output / MTok | Relative Cost |
|-------|-------------|---------------|---------------|
| Economy (e.g., Haiku) | $X | $Y | 1x (baseline) |
| Standard (e.g., Sonnet) | $X | $Y | Nx Economy |
| Premium (e.g., Opus) | $X | $Y | Nx Economy |

Prices change frequently. Update this table when you set up routing and review quarterly.

### Step 2: Estimate daily token consumption

For each skill, estimate: runs per day, tokens per run (input + output), and assigned model tier.

| Category | Runs/Day | Tokens/Run | Model Tier | Daily Cost |
|----------|----------|-----------|-----------|-----------|
| Classification skills | N | ~50K | Economy | $X |
| Synthesis skills | N | ~100K | Standard | $X |
| Draft generation | N | ~50K | Standard/Premium | $X |
| Analysis skills | N | ~100K | Standard | $X |
| **TOTAL** | | | | **$X** |

### Step 3: Verify the math works

The budget only holds if:
1. Classification and extraction tasks use the Economy tier, not Standard/Premium
2. Token counts per run stay under the ceilings you set (section 4)
3. No skill is accidentally hitting a more expensive model version than intended
4. Context sizes are controlled (section 5)

**Watch for model version drift.** A single version mismatch (e.g., a legacy premium model at 3x the current premium price) can blow your budget. Audit which model version each skill actually calls, not just which one is configured.

---

## 4. Guardrails Checklist

### Per-run token ceiling

Set a default maximum input token count (e.g., 200K) and output token count (e.g., 50K). Allow explicit overrides for skills that genuinely need more context (multi-source synthesis, weekly reviews). Set a hard ceiling that nothing can exceed without manual override.

If a skill hits the ceiling, it should fail loudly (log + alert), not silently truncate.

### Per-day budget cap

Configure LiteLLM with a hard daily budget limit and budget duration. Verify it is actually enforced — a configured limit that doesn't fire is worse than no limit (false confidence).

### Model routing enforcement

Routing is configured in `config/debate-models.json` (persona-to-model mapping) and SKILL.md frontmatter (`model:` field). `scripts/llm_client.py` routes all calls through LiteLLM. The default model should be Economy tier. Skills explicitly opt into Standard or Premium.

### Alerting thresholds

| Trigger | Action |
|---------|--------|
| Single run exceeds default token ceiling | Log warning |
| Single run exceeds hard ceiling | Alert + pause skill |
| Daily spend exceeds 66% of budget | Warning notification |
| Daily spend exceeds 100% of budget | Pause non-essential skills |
| Skill errors 3 consecutive times | Pause skill + alert |

### Prompt caching

Enable prompt caching for skills that run repeatedly with the same system prompt. A classification skill running 30x/day with a 3,000-token system prompt saves significant input costs when subsequent reads hit the cache at 10% of the base rate.

---

## 5. Context Size Discipline

The biggest cost lever is not model selection — it is **how much context you feed in**.

**Classification does not need full documents.** For classifying emails, messages, or tickets: feed sender, subject, first 200 characters, metadata. That is ~500 tokens per item, not 5,000.

**Extraction should process deltas, not full history.** Feed only content since the last successful run. Delta processing, not full replay.

**Synthesis should pull targeted context.** Don't dump entire records from application databases. Pull: last relevant notes, open items related to this entity, role/context metadata, and the specific agenda or query.

**No skill should approach 1M tokens.** If you are in the 200K+ range, you are either hitting long-context pricing tiers (often 2x rates) or doing something wrong with context management. Investigate before accepting the cost.

**The diagnostic question:** If a skill consumes more tokens than expected, ask: "What is in the context that the LLM does not need to produce the output?" Strip everything that does not directly contribute to the task.

---

## 6. Implementation Roadmap

1. **Audit current state.** Identify which model each skill is actually calling (not just configured). Check for version mismatches.
2. **Build your routing table.** Map every skill to a task type and model tier using the template in section 2.
3. **Set the default to Economy.** Skills that need Standard or Premium must explicitly opt in.
4. **Add token ceilings and budget caps.** Configure in LiteLLM with real alerting.
5. **Shrink context.** Audit the input fed to each skill. Apply the discipline from section 5.
6. **Monitor and tune.** Review daily spend, adjust routing as quality data comes in.

### When to consider a dynamic router

A static routing table (skill to model) with escalation triggers is the right architecture when you have a known set of skills with predictable task types. Consider a dynamic ML-based router when:
- You have 50+ skills with ambiguous complexity
- User-facing queries arrive with unpredictable difficulty
- You are spending enough that optimizing the last 20% justifies the complexity

For most BuildOS projects, the static table plus escalation triggers is sufficient.
