#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════
# scripts/github/sync_labels.sh
#
# Sync GitHub issue labels for the engine repo from labels.yml.
# Idempotent: uses `gh label create --force` so reruns update existing labels
# (color, description) without erroring.
#
# USAGE:
#   bash scripts/github/sync_labels.sh             # sync to current repo's origin
#   bash scripts/github/sync_labels.sh --repo OWNER/NAME
#   bash scripts/github/sync_labels.sh --prune     # also delete labels not in yml
#
# REQUIRES:
#   - gh CLI authenticated (run `gh auth login` first)
#   - yq (https://github.com/mikefarah/yq) for YAML parsing
# ══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$REPO_ROOT/scripts/lib/guard_cwd.sh"
_guard_require_proposal_or_engine_root "$REPO_ROOT"

LABELS_FILE="$SCRIPT_DIR/labels.yml"
REPO_FLAG=()
PRUNE=0

while [ $# -gt 0 ]; do
  case "$1" in
    --repo)
      REPO_FLAG=(--repo "$2")
      shift 2
      ;;
    --prune)
      PRUNE=1
      shift
      ;;
    -h|--help)
      sed -n '2,16p' "$0"
      exit 0
      ;;
    *)
      echo "✖ unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

command -v gh >/dev/null || { echo "✖ gh CLI not found"; exit 1; }
command -v yq >/dev/null || { echo "✖ yq not found (https://github.com/mikefarah/yq)"; exit 1; }
[ -f "$LABELS_FILE" ] || { echo "✖ labels.yml not found at $LABELS_FILE"; exit 1; }

gh auth status >/dev/null 2>&1 || { echo "✖ gh not authenticated — run: gh auth login"; exit 1; }

echo "→ syncing labels from $LABELS_FILE"

count="$(yq '. | length' "$LABELS_FILE")"
declare -a desired_names=()

for i in $(seq 0 $((count - 1))); do
  name="$(yq ".[$i].name" "$LABELS_FILE")"
  color="$(yq ".[$i].color" "$LABELS_FILE")"
  desc="$(yq ".[$i].description" "$LABELS_FILE")"
  desired_names+=("$name")

  gh label create "$name" \
    --color "$color" \
    --description "$desc" \
    --force \
    "${REPO_FLAG[@]}" >/dev/null
  echo "  ✓ $name (#$color)"
done

if [ "$PRUNE" -eq 1 ]; then
  echo "→ pruning labels not in labels.yml"
  existing="$(gh label list --json name --jq '.[].name' "${REPO_FLAG[@]}")"
  while IFS= read -r existing_name; do
    [ -z "$existing_name" ] && continue
    keep=0
    for desired in "${desired_names[@]}"; do
      if [ "$existing_name" = "$desired" ]; then
        keep=1
        break
      fi
    done
    if [ "$keep" -eq 0 ]; then
      gh label delete "$existing_name" --yes "${REPO_FLAG[@]}" >/dev/null
      echo "  ✗ deleted $existing_name"
    fi
  done <<< "$existing"
fi

echo "✓ done"
