#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════
# scripts/git/hooks/install_hooks.sh
# Installs proposal Git hooks into .git/hooks/
# Run once after cloning: bash scripts/git/hooks/install_hooks.sh
# ══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

# shellcheck source=../../lib/guard_cwd.sh
source "$REPO_ROOT/scripts/lib/guard_cwd.sh"
_guard_require_proposal_or_engine_root "$REPO_ROOT"

GIT_HOOKS_DIR="$(git rev-parse --git-dir)/hooks"

HOOKS=("pre-commit")

echo "Installing proposal Git hooks..."

for hook in "${HOOKS[@]}"; do
  src="$SCRIPT_DIR/$hook"
  dst="$GIT_HOOKS_DIR/$hook"

  if [ ! -f "$src" ]; then
    echo "  ⚠ Source not found: $src — skipping"
    continue
  fi

  if [ -f "$dst" ] && [ ! -L "$dst" ]; then
    echo "  ⚠ Existing hook found at $dst — backing up to $dst.bak"
    cp "$dst" "$dst.bak"
  fi

  cp "$src" "$dst"
  chmod +x "$dst"
  echo "  ✔ Installed: $hook → $dst"
done

echo ""
echo "✔ All hooks installed. Run 'git commit' to test."
