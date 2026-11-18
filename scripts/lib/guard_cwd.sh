#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════
# scripts/lib/guard_cwd.sh
#
# Sourceable guard helper for ae-proposal-engine scripts.
# Verifies a resolved REPO_ROOT is either the engine repo or a scaffolded
# proposal repo. Aborts with a clear error otherwise.
#
# This is a safety net for ARCH-16 (agent/script cwd guardrail): shell scripts
# already self-locate via $BASH_SOURCE, but a copied-out script or a path
# resolution bug could still run in the wrong directory. This guard rejects
# those cases before any destructive operation.
#
# USAGE (from any script):
#   SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
#   REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"          # adjust depth as needed
#   source "$SCRIPT_DIR/<relpath>/lib/guard_cwd.sh"
#   _guard_require_proposal_or_engine_root "$REPO_ROOT"
# ══════════════════════════════════════════════════════════════════════════════

_guard_require_proposal_or_engine_root() {
  local root="${1:-}"

  if [ -z "$root" ]; then
    echo "✖ guard_cwd: no root path provided to _guard_require_proposal_or_engine_root" >&2
    exit 1
  fi

  if [ ! -d "$root" ]; then
    echo "✖ guard_cwd: resolved REPO_ROOT does not exist: $root" >&2
    exit 1
  fi

  # Engine repo marker
  if [ -f "$root/scripts/scaffold/new_proposal.sh" ]; then
    return 0
  fi

  # Scaffolded proposal repo marker (live config or example fallback)
  if [ -f "$root/00_admin/proposal_config.yml" ] || \
     [ -f "$root/00_admin/proposal_config.yml.example" ]; then
    return 0
  fi

  echo "✖ Refusing to run: $root does not look like a proposal or engine repo." >&2
  echo "  Expected one of:" >&2
  echo "    $root/scripts/scaffold/new_proposal.sh   (engine repo)" >&2
  echo "    $root/00_admin/proposal_config.yml       (scaffolded proposal)" >&2
  echo "    $root/00_admin/proposal_config.yml.example" >&2
  echo "" >&2
  echo "  If you copied this script out of the repo, run it from inside the repo instead." >&2
  exit 1
}

_guard_path_inside() {
  # Usage: _guard_path_inside <candidate> <container>
  # Exits 0 if candidate is inside container (including equality).
  # Exits 1 otherwise. Does not abort the caller — caller decides.
  local candidate container candidate_abs container_abs
  candidate="${1:-}"
  container="${2:-}"

  [ -z "$candidate" ] && return 1
  [ -z "$container" ] && return 1

  # Resolve absolute paths. If candidate doesn't exist yet, resolve its parent.
  if [ -e "$candidate" ]; then
    candidate_abs="$(cd "$candidate" 2>/dev/null && pwd)" || \
      candidate_abs="$(cd "$(dirname "$candidate")" && pwd)/$(basename "$candidate")"
  else
    candidate_abs="$(cd "$(dirname "$candidate")" 2>/dev/null && pwd)/$(basename "$candidate")" || return 1
  fi

  container_abs="$(cd "$container" 2>/dev/null && pwd)" || return 1

  case "$candidate_abs/" in
    "$container_abs/"*) return 0 ;;
    *) return 1 ;;
  esac
}
