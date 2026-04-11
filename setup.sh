#!/usr/bin/env bash
# setup.sh — Bootstrap BuildOS for a fresh clone.
# Idempotent. Safe to run multiple times. No interactive prompts.
# Exit 0 if core requirements met (python 3.11+ and git). Exit 1 otherwise.

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Helpers
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ok()   { printf "  %-16s %s \xe2\x9c\x93\n" "$1" "$2"; }
warn() { printf "  %-16s %s \xe2\x9a\xa0\n" "$1" "$2"; }
fail() { printf "  %-16s %s \xe2\x9c\x97\n" "$1" "$2"; }
info() { printf "  %-16s %s\n" "$1" "$2"; }

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. Detect platform
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

KERNEL="$(uname -s)"
ARCH="$(uname -m)"

case "$KERNEL" in
  Darwin)
    PLATFORM_LABEL="macOS ($ARCH)"
    PLATFORM_KEY="darwin-$ARCH"
    ;;
  Linux)
    PLATFORM_LABEL="Linux ($ARCH)"
    PLATFORM_KEY="linux-$ARCH"
    ;;
  *)
    PLATFORM_LABEL="$KERNEL ($ARCH)"
    PLATFORM_KEY="$(echo "$KERNEL" | tr '[:upper:]' '[:lower:]')-$ARCH"
    ;;
esac

echo ""
echo "BuildOS Setup"
echo "━━━━━━━━━━━━━━━━━━━━━"
echo ""
info "Platform:" "$PLATFORM_LABEL"
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. Find Python 3.11+
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PYTHON3=""
for candidate in python3.13 python3.12 python3.11 python3; do
  if command -v "$candidate" > /dev/null 2>&1; then
    version=$("$candidate" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || true)
    major="${version%%.*}"
    minor="${version#*.}"
    if [[ -n "$major" ]] && [[ "$major" -ge 3 ]] && [[ "$minor" -ge 11 ]]; then
      PYTHON3="$(command -v "$candidate")"
      break
    fi
  fi
done

if [[ -z "$PYTHON3" ]]; then
  fail "Python:" "3.11+ not found"
  echo ""
  echo "  Install Python 3.11+ for your platform:"
  case "$KERNEL" in
    Darwin)
      echo "    brew install python@3.12"
      echo "    # or: brew install python@3.11"
      ;;
    Linux)
      echo "    sudo apt install python3.11  # Debian/Ubuntu"
      echo "    sudo dnf install python3.11  # Fedora"
      echo "    # or use pyenv: pyenv install 3.12"
      ;;
    *)
      echo "    Install Python 3.11+ from https://python.org"
      ;;
  esac
  echo ""
  exit 1
fi

PYTHON_VERSION="$("$PYTHON3" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")"
ok "Python:" "$PYTHON3 ($PYTHON_VERSION)"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. Find ruff (optional)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RUFF=""
if command -v ruff > /dev/null 2>&1; then
  RUFF="$(command -v ruff)"
  ok "Ruff:" "$RUFF"
else
  warn "Ruff:" "not found (optional — install with: pip install ruff)"
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. Find other optional tools
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if "$PYTHON3" -m pytest --version > /dev/null 2>&1; then
  ok "Pytest:" "available"
else
  warn "Pytest:" "not found (optional — install with: pip install pytest)"
fi

if command -v litellm > /dev/null 2>&1; then
  ok "LiteLLM CLI:" "available"
else
  warn "LiteLLM CLI:" "not found (optional — install with: pip install litellm)"
fi

if command -v ollama > /dev/null 2>&1; then
  ok "Ollama:" "available"
else
  warn "Ollama:" "not found (optional — needed for local models)"
fi

echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. Install git hooks
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

HOOKS_INSTALLED=false
if [[ -d .git ]]; then
  mkdir -p .git/hooks
  ln -sf ../../hooks/pre-commit-banned-terms.sh .git/hooks/pre-commit
  HOOKS_INSTALLED=true
  ok "Git hooks:" "pre-commit installed"
else
  warn "Git hooks:" "not a git repo — skipped"
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. Initialize project files from templates
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TEMPLATES_COPIED=0
copy_template() {
  local src="$1" dst="$2"
  if [[ -f "templates/$src" ]] && [[ ! -f "$dst" ]]; then
    mkdir -p "$(dirname "$dst")"
    cp "templates/$src" "$dst"
    TEMPLATES_COPIED=$((TEMPLATES_COPIED + 1))
  fi
}

copy_template "current-state.md"    "docs/current-state.md"
copy_template "decisions.md"        "tasks/decisions.md"
copy_template "lessons.md"          "tasks/lessons.md"
copy_template "handoff.md"          "tasks/handoff.md"
copy_template "session-log.md"      "tasks/session-log.md"
copy_template "project-prd.md"      "docs/project-prd.md"
copy_template "contract-tests.md"   "docs/contract-tests.md"
copy_template "review-protocol.md"  "docs/review-protocol.md"

if [[ "$TEMPLATES_COPIED" -gt 0 ]]; then
  ok "Templates:" "$TEMPLATES_COPIED files initialized"
else
  info "Templates:" "all files already exist"
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 7. Create .env from example
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ENV_STATUS=""
if [[ ! -f .env ]]; then
  if [[ -f .env.example ]]; then
    cp .env.example .env
    ENV_STATUS="created (add your API keys)"
    ok ".env:" "$ENV_STATUS"
  else
    warn ".env:" "no .env.example found — create .env manually"
    ENV_STATUS="missing"
  fi
else
  ENV_STATUS="exists"
  info ".env:" "already exists"
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 8. Create stores/ directory
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

mkdir -p stores
info "stores/:" "ready"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 9. Install design tools (optional)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if [[ -x "${DESIGN_CLI:-}" ]] && [[ -x "${BROWSE_CLI:-}" ]]; then
  ok "Design tools:" "already installed"
elif [[ -x "$PROJECT_ROOT/scripts/setup-design-tools.sh" ]]; then
  echo ""
  info "Design tools:" "installing (needed for /design-shotgun)..."
  if "$PROJECT_ROOT/scripts/setup-design-tools.sh"; then
    ok "Design tools:" "installed"
  else
    warn "Design tools:" "install failed (design skills unavailable, everything else works)"
  fi
else
  warn "Design tools:" "setup script missing"
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 10. Write .buildos-config
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SETUP_DATE="$(date +%Y-%m-%d)"

cat > .buildos-config <<CONF
# Generated by setup.sh — do not edit manually. Re-run setup.sh to regenerate.
BUILDOS_PYTHON3=$PYTHON3
BUILDOS_RUFF=$RUFF
BUILDOS_PLATFORM=$PLATFORM_KEY
BUILDOS_SETUP_DATE=$SETUP_DATE
CONF

info "Config:" ".buildos-config written"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 11. Preflight check
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo ""
echo "Preflight"
echo "━━━━━━━━━━━━━━━━━━━━━"

# Python — already verified above
ok "Python 3.11+:" "found"

# Git hooks
if [[ "$HOOKS_INSTALLED" == true ]]; then
  ok "Git hooks:" "installed"
else
  warn "Git hooks:" "skipped (not a git repo)"
fi

# .env
if [[ -f .env ]]; then
  ok ".env:" "exists"
else
  fail ".env:" "missing"
fi

# stores/
if [[ -d stores ]]; then
  ok "stores/:" "exists"
else
  fail "stores/:" "missing"
fi

# LiteLLM reachable
LITELLM_STATUS="not running (needed for /challenge, /debate, /review)"
if curl -sf --max-time 2 http://localhost:4000/health > /dev/null 2>&1; then
  LITELLM_STATUS="running"
  ok "LiteLLM:" "$LITELLM_STATUS"
else
  warn "LiteLLM:" "$LITELLM_STATUS"
fi

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 12. Summary
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo ""
echo "BuildOS Setup Complete"
echo "━━━━━━━━━━━━━━━━━━━━━"
printf "  %-16s %s\n" "Platform:" "$PLATFORM_LABEL"
printf "  %-16s %s\n" "Python:" "$PYTHON3 ($PYTHON_VERSION)"
if [[ -n "$RUFF" ]]; then
  printf "  %-16s %s\n" "Ruff:" "$RUFF"
else
  printf "  %-16s %s\n" "Ruff:" "not installed"
fi
if [[ "$HOOKS_INSTALLED" == true ]]; then
  printf "  %-16s %s\n" "Git hooks:" "installed"
else
  printf "  %-16s %s\n" "Git hooks:" "skipped"
fi
printf "  %-16s %s\n" ".env:" "$ENV_STATUS"
printf "  %-16s %s\n" "LiteLLM:" "$LITELLM_STATUS"
echo ""
echo "Next steps:"
echo "  1. Edit .env with your API keys (ANTHROPIC, OPENAI, GEMINI, LITELLM_MASTER_KEY)"
echo "  2. Start LiteLLM: litellm --config config/litellm-config.yaml"
echo "  3. Open Claude Code in this directory — all governance hooks are active"
echo "  4. See Dependencies below for optional tools"
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Dependencies
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# Required:
#   Python 3.11+          Core scripting (debate engine, hooks, toolbelt)
#   git                   Version control, worktree isolation
#
# Required for cross-model features (/challenge, /debate, /review, /refine):
#   LiteLLM proxy         pip install litellm — run with: litellm --config config/litellm-config.yaml
#   API keys              At least 2 of: ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY
#
# Optional:
#   ruff                  Python linter (hook-enforced if installed)
#   pytest                Test runner for tests/
#   ollama                Local models for semantic search
#
# No requirements.txt is provided because BuildOS uses only Python stdlib
# (sqlite3, json, subprocess, argparse, etc.) plus LiteLLM which runs as
# a separate proxy process, not an imported library.
