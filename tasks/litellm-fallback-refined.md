---
debate_id: litellm-fallback
created: 2026-04-12T20:52:02-0700
phase: refine
rounds: 6
models: gemini-3.1-pro, gpt-5.4, claude-opus-4-6
seeded_from_judgment: yes
---
# litellm-fallback — Refined Document

## Round 1 (gemini-3.1-pro)
The original proposal correctly identified a major onboarding friction point but suffered from significant mechanical flaws in its implementation plan. It assumed credentials that aren't guaranteed to exist, proposed building a redundant HTTP client, ignored existing retry and preflight logic, and glossed over critical metadata tracking (provenance and judge independence).

The revised document addresses all accepted challenges by:
1. **Credentials & Gating:** Explicitly requiring `ANTHROPIC_API_KEY` for fallback mode and updating `debate.py` preflight checks to accept it when `LITELLM_MASTER_KEY` is missing.
2. **Transport:** Eliminating the proposed custom Anthropic HTTP client. Instead, the fallback uses the in-process `litellm` Python library (already present in the environment) to call Anthropic directly, preserving the exact same OpenAI-compatible message format.
3. **Retry Logic:** Specifying that fallback triggers *only* on `ConnectionRefusedError` for `localhost:4000`, explicitly bypassing the exponential backoff loop.
4. **Provenance & Independence:** Mandating that the actual fallback model name is written to the artifact frontmatter (e.g., `model: claude-3-5-sonnet (fallback)`), and requiring the `judge` command to emit a hard warning and record `independence: degraded_single_model` when fallback is active.

These changes make the proposal executable, maintain audit integrity, and prevent silent degradation of the review pipeline's trust model.

## Round 2 (gpt-5.4)
The revision is materially better than a generic fallback proposal because it now addresses all six accepted challenges directly:

- It no longer assumes Anthropic credentials magically exist; it requires `ANTHROPIC_API_KEY` explicitly and defines the failure message.
- It avoids adding a third transport convention by reusing in-process `litellm.completion(...)`.
- It narrows the fallback trigger to `ConnectionRefusedError` on `localhost:4000` and places it before the retry loop.
- It specifies provenance handling and requires the actual fallback model to be written into artifact metadata.
- It addresses command-level gating in `debate.py`.
- It explicitly warns on degraded judge independence and records that in metadata.

Remaining issues in the current revision:

1. **“Detects the LiteLLM proxy is unavailable” is still too broad in the opening summary.** The implementation later narrows this correctly, but the top-level framing should match the actual behavior: fallback is for local proxy unavailability, not generic LLM failure.
2. **The credential strategy is better but still incomplete operationally.** It should state that fallback is supported only when the local environment can authenticate Anthropic through `ANTHROPIC_API_KEY`; OAuth-based Claude Code auth alone does not satisfy this path.
3. **Artifact compatibility wording is slightly overstated.** If frontmatter now records `claude-3-5-sonnet-latest (fallback)` and `independence: degraded_single_model`, artifact structure is preserved, but contents differ. That should be stated precisely.
4. **Fallback scope should be explicit for each command.** The current text says `challenge`, `review`, `judge`, `refine` check prerequisites, but the expected impact section only mentions `/review` and `/challenge`. Make the supported-command set explicit and consistent.
5. **The bypass point should be described as request-time transport selection, not vague “detects unavailable.”** This makes audit and routing behavior clearer.
6. **The claim about users upgrading after seeing value is directional but unevidenced.** It is fine as rationale, but should not be presented as an assured outcome.

## Round 3 (claude-opus-4-6)
The previous revision is substantially improved over a typical first draft — it addresses all six accepted challenges and integrates them into a coherent design. However, several issues remain:

1. **Credential strategy (Challenge 1):** Well-addressed with explicit `ANTHROPIC_API_KEY` requirement and clear error messages. No regressions. Minor improvement: the proposal should state where/how `ANTHROPIC_API_KEY` is documented for onboarding users, since the whole point is reducing the onboarding cliff.

2. **Third calling convention (Challenge 2):** Addressed by specifying in-process `litellm.completion()` reuse. Good. But the proposal doesn't acknowledge that `litellm` the Python library must be available as a dependency (it likely already is since the proxy uses it, but this should be stated explicitly to avoid a gap).

3. **Retry bypass (Challenge 3):** Well-specified — connection refused before retry loop, narrow trigger. One gap: the proposal says "ConnectionRefusedError or equivalent" but should name the actual exception classes that will be caught, since Python HTTP libraries surface these differently (e.g., `requests.ConnectionError`, `httpx.ConnectError`, `aiohttp.ClientConnectorError`). The implementation must match whatever `llm_client.py` actually uses.

4. **Audit metadata (Challenge 4):** Addressed with explicit bypass point and provenance recording. The `(fallback)` suffix in frontmatter is concrete. Good.

5. **Command-level gating (Challenge 5):** Addressed with `debate.py` changes to `check_prerequisites()`. The specific command list is named. Good.

6. **Judge independence (Challenge 6):** Addressed with stderr warning and `independence: degraded_single_model` metadata. One improvement needed: the proposal should specify what happens if downstream pipeline stages consume independence metadata — does `degraded_single_model` cause any gate to fail, or is it advisory only? This matters for CI/hook consumers.

**Structural issues:**
- The "What changes" section partially duplicates the "Behavior" section. I'll tighten this by making "What changes" a concise file-level summary that references behavior specs rather than restating them.
- The "Expected Impact" section could be sharper about what success looks like quantitatively (even if estimated).
- The proposal lacks an explicit "Implementation Order" or sequencing, which matters because `debate.py` gating must land before or with `llm_client.py` changes.

**No regressions detected** from the previous revision — it preserved all operational context and didn't introduce factual errors.

## Round 4 (gemini-3.1-pro)
The previous revision successfully integrated all six accepted challenges with concrete, executable mechanisms. The credential strategy, retry bypass, and provenance tracking are now explicitly defined and leave no ambiguity for the implementer. The document maintains a strong, decisive posture without relying on hedge words or deferred studies. 

Minor structural refinements were made to ensure the implementation order reads as strict directives rather than descriptive steps, but the core technical design remains intact and highly actionable.

## Round 5 (gpt-5.4)
The revision is materially better and addresses all six accepted challenges directly:

- It now defines a concrete credential strategy and correctly stops assuming Claude Code OAuth/session auth is usable for fallback.
- It avoids introducing a third transport convention by reusing the existing client abstraction with in-process LiteLLM.
- It narrows fallback activation to hard local proxy unavailability and places the decision before the retry loop.
- It specifies the bypass point and records actual model provenance instead of silently preserving persona-mapped model names.
- It includes required entrypoint/preflight changes in `scripts/debate.py`.
- It handles judge independence explicitly with warning and metadata.

Remaining issues and improvements:
1. The proposal should make the precedence rule explicit when both `LITELLM_MASTER_KEY` and `ANTHROPIC_API_KEY` are present: standard proxy mode wins unless the proxy is actually unreachable.
2. The trigger language should avoid implying only `localhost:4000` is valid; some environments may configure a different local proxy address. The current text hints at this, but the rule should be framed around the configured proxy endpoint.
3. The provenance section should distinguish display labels from canonical model identifiers. Writing `claude-3-5-sonnet-latest (fallback)` into the `model` field may be convenient for humans but can break downstream consumers that expect a raw model name. Better: keep `model` canonical and add `execution_mode` / `fallback_from_model` / `transport` fields.
4. The one-time warning scope says “once per process, not per command invocation,” which is fine for a CLI process, but the implementation should key it to fallback entry, not startup, to avoid warning suppression bugs.
5. The implementation/test section can be made more executable by specifying exact scenarios around “connection refused” versus timeout/upstream error so regressions are testable.

## Round 6 (claude-opus-4-6)
The previous revision is strong. It addressed all six accepted challenges with concrete, specific solutions. My review finds:

1. **No regressions introduced.** The credential strategy, preflight gating, retry bypass, transport reuse, provenance tracking, and judge independence sections all directly resolve the accepted challenges.

2. **Remaining issues:**
   - The credential strategy section says "Fallback path: `LITELLM_MASTER_KEY` absent, `ANTHROPIC_API_KEY` present" but later under "Both present" describes a different trigger. The logic is correct but the presentation makes it seem like fallback only activates when `LITELLM_MASTER_KEY` is absent, when it can also activate when both are present but the proxy is unreachable. This needs tightening.
   - The fallback trigger section (§3) describes exception classes parenthetically ("for example `requests.ConnectionError`...") which hedges what should be a specification. The implementation must catch specific exceptions; the proposal should commit to the detection mechanism rather than listing possibilities.
   - The "What Does NOT Change" section lists `refine` but the tradeoffs section mentions model diversity loss in refinement rounds. These are consistent but the `refine` entry could be clearer about what specifically doesn't change vs. what does.
   - Implementation order step 3 bundles too many concerns (transport, notice, provenance, judge warnings). These are all in `llm_client.py` and `debate.py` but the step could be decomposed for clarity.
   - The design section numbering (1-8) is fine but sections 5 and 6 could be tightened — there's some overlap between "Model Routing and Bypass Point" and "Provenance Tracking" on what metadata gets written.

3. **Structure improvements:** I'll consolidate the credential detection logic into a single clear decision table, sharpen the exception handling specification, and tighten the overlap between sections 5 and 6.

4. **Over/under-explained:** The tradeoffs and expected impact sections are well-calibrated. The transparency section (§8) is appropriately brief. No major over-explanation.

## Final Refined Document

# Proposal: LiteLLM Graceful Degradation — Single-Model Fallback

## Problem

BuildOS's most differentiated features — `/challenge` and `/review` — require a running LiteLLM proxy with multiple providers configured. When that proxy is unavailable, these features fail entirely. This is the single biggest onboarding cliff in BuildOS.

Every session where someone skips `/review` because LiteLLM isn't configured is a session where they get B-tier output from an A-tier framework. The review pipeline creates the most value over raw Claude Code, but it's gated behind the heaviest infrastructure requirement.

## Proposed Solution

When BuildOS cannot reach the configured **local LiteLLM proxy** (today typically `localhost:4000`), it falls back to single-model review using the **in-process LiteLLM Python SDK** with Anthropic as the provider. This fallback requires an explicit `ANTHROPIC_API_KEY` in the environment; Claude Code OAuth/session auth is not sufficient.

The goal is to preserve command usability, artifact generation, and structured review behavior when the local proxy is absent, while explicitly recording that the run used degraded single-model execution.

---

## Design

### 1. Credential Strategy and Mode Selection

Mode selection follows a single decision path evaluated at two points: preflight (in `debate.py`) and transport (in `llm_client.py`).

| `LITELLM_MASTER_KEY` | `ANTHROPIC_API_KEY` | Proxy reachable? | Result |
|---|---|---|---|
| Set | Any | Yes | **Standard mode.** Proxy used as today. |
| Set | Set | No (connection refused) | **Fallback mode.** In-process LiteLLM SDK with Anthropic. |
| Set | Absent | No (connection refused) | **Fail.** Key exists but proxy unreachable and no fallback credential. Error message below. |
| Absent | Set | N/A (no proxy attempted) | **Fallback mode.** In-process LiteLLM SDK with Anthropic. |
| Absent | Absent | N/A | **Fail immediately.** Error message below. |

Failure message (all failure cases):

```text
LiteLLM proxy unavailable and ANTHROPIC_API_KEY not found.
Set ANTHROPIC_API_KEY for single-model fallback, or start LiteLLM.
See docs/infrastructure.md for setup instructions.
```

**Why `ANTHROPIC_API_KEY` must be explicit:** The codebase currently loads only `LITELLM_MASTER_KEY` from the environment for LLM calls. Claude Code's OAuth/session authentication does not expose a key usable by the LiteLLM Python SDK. The fallback path therefore requires a separately provisioned `ANTHROPIC_API_KEY`. This is a new requirement that must be documented.

**Documentation requirement:** `docs/infrastructure.md` must be updated to describe the fallback credential path. The quick-start section must include:

```bash
export ANTHROPIC_API_KEY=sk-ant-...   # enables /review, /challenge without LiteLLM proxy
```

**Dependency note:** The `litellm` Python package is already a project dependency. The fallback path uses it as an in-process SDK, requiring no new dependencies.

### 2. Command-Level Preflight Gating

**Location:** `scripts/debate.py`, specifically `check_prerequisites()`.

The commands `challenge`, `review`, `judge`, and `refine` currently fail if `LITELLM_MASTER_KEY` is missing, before transport code in `llm_client.py` ever runs. This preflight must be widened:

- If `LITELLM_MASTER_KEY` is set → proceed normally (proxy reachability is checked later at transport time).
- If `LITELLM_MASTER_KEY` is missing but `ANTHROPIC_API_KEY` is set → proceed in fallback-capable mode. Set an internal flag (e.g., `fallback_eligible = True`) propagated to `llm_client.py`.
- If both are missing → fail immediately with the message above.

**Scope:** This change applies only to `challenge`, `review`, `judge`, and `refine`. Other commands retain their existing prerequisites.

**Why this is required:** Without this change, `debate.py` blocks execution before `llm_client.py` transport code runs. A transport-only fallback would never execute for onboarding users who lack `LITELLM_MASTER_KEY`.

### 3. Fallback Trigger and Retry Bypass

**Location:** `scripts/llm_client.py`, at the point where a proxy request is about to be made, **before** the exponential-backoff retry loop.

**Trigger conditions — all three must hold:**
1. The request target is the configured LiteLLM proxy endpoint (currently `localhost:4000` or equivalent local address).
2. The connection attempt raises a **connection-refused exception** — the specific class depends on the transport library in use. The implementation must catch the concrete exception that the current HTTP client raises for TCP connection refusal (e.g., if using `requests`: `requests.ConnectionError` wrapping `ConnectionRefusedError`; if using `httpx`: `httpx.ConnectError`). The implementation PR must identify and document which exception class applies to the actual transport stack.
3. `ANTHROPIC_API_KEY` is present in the environment.

**Timing:** The connection-refused check is a single probe that runs **before** entering the retry loop. A refused connection to a local proxy means the proxy process is not running; retrying with backoff cannot help. The system enters fallback immediately.

**Implementation:** Wrap the initial connection attempt in a targeted try/except for the connection-refused exception class only. On catch, check for `ANTHROPIC_API_KEY`. If present, enter fallback. If absent, raise the original error immediately (no retry — the proxy is not running and there is no fallback).

**Fallback is NOT triggered for:**
- Upstream provider errors returned through a running LiteLLM proxy (4xx/5xx with a response body)
- TCP timeouts (proxy may be starting up or under load — these enter the existing retry loop)
- Rate limits from the proxy or upstream providers
- Authentication failures against the proxy (`401`/`403` — the proxy is running; the credential is wrong)
- Malformed request errors

These cases continue through the existing retry and error-handling path because they indicate the proxy is running but experiencing a different class of problem.

### 4. Fallback Transport

The fallback path reuses the existing client abstraction in `llm_client.py`. It does **not** introduce a third calling convention (no raw `anthropic.Client()` or custom HTTP calls to the Anthropic Messages API).

The transport swap:

```python
# Standard mode: request goes to local proxy via existing HTTP transport
# Fallback mode: request goes through in-process LiteLLM SDK
litellm.completion(
    model="anthropic/claude-sonnet-4-20250514",
    messages=messages,
    api_key=os.environ["ANTHROPIC_API_KEY"],
    ...
)
```

This preserves the current message construction, response parsing, and caller interface. The `litellm` SDK already handles Anthropic's message format translation. Callers of `llm_client.py` see no interface change.

**Why not a separate Anthropic client:** `llm_client.py` already has two transport paths (proxy HTTP and direct SDK patterns exist in the codebase). Adding a raw Anthropic Messages API client would create a third calling convention with its own auth handling, error mapping, and usage extraction. Using `litellm.completion()` in-process keeps the response shape identical to what the proxy returns, minimizing new code and maintenance burden.

### 5. Model Routing, Bypass Point, and Provenance

**Bypass point:** Transport selection in `llm_client.py`, after command preflight passes and before a proxy request would enter retries.

**In fallback mode:**
- Persona/model routing from `config/debate-models.json` is **not used** to select different providers. All requests go to `anthropic/claude-sonnet-4-20250514`.
- The requested persona (PM, Security, Architecture) remains part of the prompt structure — persona-specific review lenses still apply via system/user message content.
- The **actual execution model** is recorded in all output, not the original persona-mapped model name.

**Artifact metadata:**

| Field | Standard mode | Fallback mode |
|---|---|---|
| `model` | Actual model used (as today) | `anthropic/claude-sonnet-4-20250514` |
| `execution_mode` | `standard` | `fallback_single_model` |
| `transport` | (not emitted, or `litellm_proxy`) | `in_process_litellm` |
| `fallback_from_model` | (not emitted) | Original persona-mapped model name, if one existed |

**Logs and run metadata** must also reflect fallback mode and the actual model used.

Artifacts must never claim a persona-mapped model such as `gpt-4o` or `gemini-pro` was used when the actual execution was the fallback model. This prevents silent provenance misstatement that would mislead governance consumers.

### 6. Judge Independence

Fallback mode collapses author and judge onto one model family, which weakens the review pipeline's trust model. The codebase already treats author/judge model overlap as meaningful (independence-check logic exists). This must not be bypassed silently.

**When `judge` runs in fallback mode:**

1. **Emit a warning** to stderr:
   ```text
   WARNING: Judge independence degraded — using same model family for author and judge.
   Results may have correlated blind spots. For independent judging, enable LiteLLM.
   ```

2. **Record in artifact metadata:**
   ```yaml
   independence: degraded_single_model
   ```

3. **Integrate with existing independence checks:** If the pipeline's existing independence-validation logic checks author/judge model separation, fallback mode must set the appropriate state through that logic's existing interface (e.g., by passing the actual model identity for both roles) rather than bypassing the check. The existing logic will then correctly detect the overlap and produce the right downstream signals.

**Gate behavior:** `independence: degraded_single_model` is advisory by default. It does not cause CI gates or hooks to fail unless gate owners explicitly check for it. Blocking the judge command entirely in fallback mode would defeat the purpose of the fallback for onboarding users.

### 7. Transparency

Upon entering fallback mode for the first time in a process, print exactly once to stderr:

```text
LiteLLM proxy unavailable — running single-model review.
For cross-model review, see docs/infrastructure.md
```

This message is emitted on first actual fallback activation, not at startup and not once per request. Subsequent calls within the same process that use fallback do so silently (the provenance metadata on each artifact is sufficient).

---

## File Changes

| File | Change |
|---|---|
| `scripts/debate.py` | Widen `check_prerequisites()` to accept `ANTHROPIC_API_KEY` as fallback credential for `challenge`, `review`, `judge`, `refine`. Set fallback-eligible flag. For `judge`, ensure fallback context is propagated so independence metadata is set correctly. |
| `scripts/llm_client.py` | Add pre-retry connection-refused detection for the configured local proxy endpoint. On connection refusal with `ANTHROPIC_API_KEY` available, activate fallback via in-process `litellm.completion()` within the existing client abstraction. Return provenance metadata including `execution_mode`, actual `model`, `transport`, and `fallback_from_model`. Emit one-time fallback notice. Emit judge independence warning and set `independence: degraded_single_model` when applicable. |
| `docs/infrastructure.md` | Document `ANTHROPIC_API_KEY` as the single-credential fallback path. Add quick-start export example. Clarify that OAuth/session auth is insufficient. Describe what fallback mode provides and what it does not. |
| `config/debate-models.json` | No changes. Persona definitions remain; they are not used for provider routing in fallback mode. |

---

## Implementation Order

1. **Document the fallback path.** Update `docs/infrastructure.md` so users and reviewers have immediate context for the credential requirement.

2. **Widen preflight gating.** Update `check_prerequisites()` in `scripts/debate.py` so `challenge`, `review`, `judge`, and `refine` are not blocked when `LITELLM_MASTER_KEY` is absent but `ANTHROPIC_API_KEY` is present.

3. **Implement transport fallback.** Update `scripts/llm_client.py`:
   - Add connection-refused detection before the retry loop for the local proxy endpoint.
   - On trigger, route through in-process `litellm.completion()` with `ANTHROPIC_API_KEY`.
   - Emit the one-time fallback notice to stderr.
   - Return provenance metadata (`execution_mode`, `model`, `transport`, `fallback_from_model`).

4. **Implement judge independence handling.** In the same `llm_client.py` change (or coordinated with it):
   - Detect when `judge` runs in fallback mode.
   - Emit the independence warning to stderr.
   - Set `independence: degraded_single_model` in artifact metadata.
   - Pass actual model identity through existing independence-check interfaces.

5. **Integration tests.** Verify all of the following:
   - (a) Proxy running + `LITELLM_MASTER_KEY` set → standard mode, no behavior change.
   - (b) Proxy absent + `ANTHROPIC_API_KEY` set → fallback activates, artifacts have `execution_mode: fallback_single_model` and correct `model`.
   - (c) Both credentials absent → immediate failure with actionable message.
   - (d) `judge` in fallback → warning emitted, `independence: degraded_single_model` in artifact.
   - (e) Proxy returns upstream error (5xx with response body) → no fallback, existing retry/error path.
   - (f) Proxy request times out without connection refusal → no fallback, existing retry path.
   - (g) Both credentials present, proxy reachable → standard mode.
   - (h) Both credentials present, proxy connection refused → fallback activates immediately, no retry backoff.
   - (i) `LITELLM_MASTER_KEY` set, `ANTHROPIC_API_KEY` absent, proxy connection refused → immediate failure, no retry.

**Ordering constraint:** Steps 2 and 3 must land together or in immediate sequence. A widened preflight without transport fallback would allow commands to start and then fail at LLM call time. A transport fallback without widened preflight would never execute for users lacking `LITELLM_MASTER_KEY`.

---

## What Does NOT Change

- Hook behavior (all hooks work the same)
- Artifact structure (same YAML/frontmatter layout and finding structure)
- Skill interfaces (skills read artifacts, not transport internals)
- Full multi-model path (when LiteLLM proxy is available, everything works as before)
- The `refine` command's core logic (iterative improvement continues; in fallback mode it uses a single model, losing cross-model diversity but retaining structured iteration)
- `config/debate-models.json` (persona definitions remain; they are not used for provider routing in fallback)

---

## Tradeoffs

**What you lose in fallback mode:**
- Cross-family disagreement (Claude, GPT, Gemini catch different failure classes)
- Independent evaluation (single model has correlated blind spots; judge independence is explicitly degraded and recorded in metadata)
- Model diversity in refinement rounds
- Exact parity with standard provenance values — fallback artifacts record different metadata because they report the truth about execution

**What you keep:**
- Structured review through PM/Security/Architecture lenses
- Artifact generation for hooks and gates
- Accurate audit metadata reflecting exact model provenance and execution mode
- Judge functionality with explicit degradation marking
- Command usability for `challenge`, `review`, `judge`, `refine` when the local proxy is absent

**Why this is acceptable:**
A single-model review through three structured lenses is better than no review. The gap between "no review" and "single-model review" is larger than the gap between "single-model review" and "cross-model review" for onboarding use cases. Provenance and degraded independence are recorded explicitly, so no downstream consumer is misled.

---

## Expected Impact

- **New users:** Can run `/challenge`, `/review`, `/judge`, `/refine` with only `ANTHROPIC_API_KEY`. Onboarding path becomes: clone → setup → `/think` → `/plan` → build → `/review` — no proxy required.
- **Existing users:** Zero change when LiteLLM proxy is running.
- **Upgrade path:** The fallback message directs users to `docs/infrastructure.md` for full cross-model setup. The fallback is a ramp, not a destination.
- **Audit consumers:** Artifacts in fallback mode are clearly marked with `execution_mode: fallback_single_model` and actual model identity. Judge artifacts additionally carry `independence: degraded_single_model`. No silent degradation.
