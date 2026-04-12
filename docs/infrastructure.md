# Infrastructure

What each dependency does and why the Build OS needs it.

---

## Required Dependencies

### Python 3

All Build OS scripts are Python. `debate.py`, `tier_classify.py`, `recall_search.py`, `finding_tracker.py`, `enrich_context.py`, and `artifact_check.py` all require Python 3.

Any recent Python 3 (3.9+) works. No third-party Python packages are required for the pipeline skills themselves.

### LiteLLM

The cross-model debate engine (`/challenge`, `/challenge --deep`, `/check`) calls models from multiple provider families through a single API. LiteLLM is the routing layer that makes this possible. Scripts call LiteLLM's OpenAI-compatible API at `http://localhost:4000` via stdlib `urllib.request` — no pip install needed in your project.

```bash
# Copy and configure
cp config/litellm-config.example.yaml config/litellm-config.yaml

# Docker (recommended)
docker run -d -p 4000:4000 --name litellm \
  --env-file .env \
  -v $(pwd)/config/litellm-config.yaml:/app/config.yaml \
  ghcr.io/berriai/litellm:main-latest \
  --config /app/config.yaml

# Or standalone (in its own venv)
pip install litellm
litellm --config config/litellm-config.yaml
```

Why a proxy instead of direct API calls: `debate.py` calls multiple model families in a single pipeline. LiteLLM normalizes the API surface so the scripts don't need provider-specific client code. Swapping a model is a config change in `litellm-config.yaml` + `config/debate-models.json`, not a code change.

**Important:** The `model_name` fields in `litellm-config.yaml` must match the model names in `config/debate-models.json`. The example config ships with matching names. If you change one, change both.

### API Keys (at least two model families)

The debate engine uses adversarial review across model families. Models from the same family agree with each other too easily (self-preference bias). Cross-family disagreement produces stronger review signals.

You need API keys for at least two of (all three recommended):

| Provider | Role in debate | Get a key |
|----------|---------------|-----------|
| **Anthropic** (Claude) | Author + PM challenger + refiner | [console.anthropic.com](https://console.anthropic.com/) |
| **OpenAI** (GPT) | Judge + security challenger | [platform.openai.com](https://platform.openai.com/) |
| **Google AI** (Gemini) | Architect + staff challenger | [aistudio.google.com](https://aistudio.google.com/) |

Copy `.env.example` to `.env` and fill in your keys. Model-to-role assignments are in `config/debate-models.json`.

---

## Optional Dependencies

### Ollama + nomic-embed-text

Enables semantic search in the `/start` skill. Without Ollama, `/start` falls back to BM25 keyword search, which still works well but misses conceptually related results that don't share exact terms.

```bash
brew install ollama    # or see https://ollama.ai/ for other platforms
ollama pull nomic-embed-text
```

Ollama runs locally. No data leaves your machine. The `nomic-embed-text` model is small (~274MB) and fast.

### Perplexity Sonar API

Enables web research in skills that need external context — `/research` (deep async research), `/explore` (pre-flight enrichment), `/think discover` (competitive landscape), and `/design consult` (competitive design research). `scripts/research.py` wraps the Perplexity Sonar API with sync and async modes.

```bash
# Get an API key at https://docs.perplexity.ai/
# Add to .env:
PERPLEXITY_API_KEY=pplx-...
```

Without it, skills fall back to Claude's built-in WebSearch tool. If that's also unavailable, they skip web research and proceed with training knowledge only. The core debate pipeline does not require it.

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

# Verify debate engine
python3 scripts/debate.py check-models
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

**Why LiteLLM over direct calls:** The debate scripts rotate models through different roles (challenger, judge, author). LiteLLM lets the scripts address models by alias (`claude-opus-4-6`, `gpt-5.4`, `gemini-3.1-pro`) without embedding provider-specific client code. Swapping a model is a config change, not a code change.

**Why local embeddings:** Semantic search over governance files (lessons, decisions, PRD) finds conceptually related context that keyword search misses. Running embeddings locally via Ollama means no data leaves your machine and no API costs for retrieval.
