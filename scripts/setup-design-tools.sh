#!/usr/bin/env bash
# Install the design CLI and browser CLI used by /design-shotgun.
# Adds DESIGN_CLI and BROWSE_CLI to your shell profile.

set -euo pipefail

INSTALL_DIR="$HOME/.claude/skills/gstack"
DESIGN_BIN="$INSTALL_DIR/design/dist/design"
BROWSE_BIN="$INSTALL_DIR/browse/dist/browse"

if [ -x "$DESIGN_BIN" ] && [ -x "$BROWSE_BIN" ]; then
  echo "Design tools already installed."
else
  echo "Installing design tools..."
  git clone --single-branch --depth 1 https://github.com/garrytan/gstack.git "$INSTALL_DIR"
  cd "$INSTALL_DIR" && ./setup
  echo "Design tools installed."
fi

# Add env vars to shell profile if not already present
SHELL_RC="$HOME/.zshrc"
[ -f "$HOME/.bashrc" ] && [ ! -f "$HOME/.zshrc" ] && SHELL_RC="$HOME/.bashrc"

if ! grep -q 'DESIGN_CLI' "$SHELL_RC" 2>/dev/null; then
  cat >> "$SHELL_RC" <<'EOF'

# Design tooling (used by /design-shotgun)
export DESIGN_CLI="$HOME/.claude/skills/gstack/design/dist/design"
export BROWSE_CLI="$HOME/.claude/skills/gstack/browse/dist/browse"
EOF
  echo "Added DESIGN_CLI and BROWSE_CLI to $SHELL_RC"
  echo "Run: source $SHELL_RC"
else
  echo "Shell profile already configured."
fi
