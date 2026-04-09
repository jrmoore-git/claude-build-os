# Infrastructure

What each dependency does and why the Build OS needs it.

---

## Required Dependencies

### Python 3

All Build OS scripts are Python. `debate.py`, `tier_classify.py`, `recall_search.py`, `finding_tracker.py`, `enrich_context.py`, `artifact_check.py`, `multi_model_debate.py`, and `model_conversation.py` all require Python 3.

Any recent Python 3 (3.9+) works. No third-party Python packages are required for the pipeline skills themselves.

### gh CLI

The GitHub CLI (`gh`) is used by review workflows for pull request integration. Install from [cli.github.com](https://cli.github.com/).

After installing, authenticate with `gh auth login`.

### LiteLLM

The cross-model debate engine (`/challenge`, `/debate`, `/review`) calls models from multiple provider families through a single API. LiteLLM is the routing layer that makes this possible.

```bash
pip install litellm
litellm --config config/litellm-config.yaml
```

Copy `config/litellm-config.example.yaml` to `config/litellm-config.yaml` and fill in your API keys. LiteLLM runs as a local proxy on port 4000 by default.

Why a proxy instead of direct API calls: `debate.py` and `multi_model_debate.py` call multiple model families in a single pipeline. LiteLLM normalizes the API surface so the scripts don't need provider-specific client code.

### API Keys (at least two model families)

The debate engine uses adversarial review across model families. Models from the same family agree with each other too easily (self-preference bias). Cross-family disagreement produces stronger review signals.

You need API keys for at least two of:

- **Anthropic** (Claude) — [console.anthropic.com](https://console.anthropic.com/)
- **OpenAI** (GPT) — [platform.openai.com](https://platform.openai.com/)
- **Google AI** (Gemini) — [aistudio.google.com](https://aistudio.google.com/)

All three families are recommended for best results. Copy `.env.example` to `.env` and fill in your keys.

---

## Optional Dependencies

### Ollama + nomic-embed-text

Enables semantic search in the `/recall` skill. Without Ollama, `/recall` falls back to BM25 keyword search, which still works well but misses conceptually related results that don't share exact terms.

```bash
brew install ollama    # or see https://ollama.ai/ for other platforms
ollama pull nomic-embed-text
```

Ollama runs locally. No data leaves your machine. The `nomic-embed-text` model is small (~274MB) and fast.

---

## Verifying Your Setup

### Scripts

```bash
# Check debate engine is available
python3 scripts/debate.py --help

# Check recall search works
python3 scripts/recall_search.py "test query" --files lessons

# Check tier classification
python3 scripts/tier_classify.py scripts/debate.py

# Check artifact validation
python3 scripts/artifact_check.py --help

# Check multi-model debate
python3 scripts/multi_model_debate.py --help
```

### LiteLLM

```bash
# Start LiteLLM
litellm --config config/litellm-config.yaml

# In another terminal, verify it responds
curl http://localhost:4000/health
```

### Ollama (optional)

```bash
# Check Ollama is running
ollama list

# Verify embedding model is available
ollama show nomic-embed-text
```

---

## Architecture Notes

**Why cross-model review matters:** When three models from different families all flag the same concern, it is almost certainly real. When only one flags something, it may be model-specific bias. Cross-model agreement is a stronger signal than single-model confidence.

**Why LiteLLM over direct calls:** The debate scripts rotate models through different roles (challenger, judge, author). LiteLLM lets the scripts address models by alias (`claude-opus`, `gpt-latest`, `gemini-pro`) without embedding provider-specific client code. Swapping a model is a config change, not a code change.

**Why local embeddings:** Semantic search over governance files (lessons, decisions, PRD) finds conceptually related context that keyword search misses. Running embeddings locally via Ollama means no data leaves your machine and no API costs for retrieval.
