#!/usr/bin/env bash
# scripts/git/publish_commit.sh
#
# Save state and merge to main after every publish (CLAUDE.md section 6).
#
#   1. Creates a short-lived branch  publish/<YYYYMMDD-HHMM>-<slug>  from main
#   2. Stages all changes (output/, sources, scripts) and commits them
#   3. Squash-merges the branch into main with a Conventional Commit message
#   4. Deletes the publish branch
#   5. Pushes main to origin only when --push is given
#
# Usage:
#   bash scripts/git/publish_commit.sh "docs: publish B592 peer review package v01" [--push]
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
# shellcheck source=../lib/guard_cwd.sh
source "$REPO_ROOT/scripts/lib/guard_cwd.sh"
_guard_require_proposal_or_engine_root "$REPO_ROOT"
cd "$REPO_ROOT"

MSG="${1:-}"
PUSH="${2:-}"
if [[ -z "$MSG" ]]; then
  echo "✖ publish_commit: commit message required (Conventional Commits, e.g. 'docs: publish ...')" >&2
  exit 1
fi

TRAILER="${PUBLISH_COMMIT_TRAILER:-}"

# First-ever commit: main is unborn, so there is nothing to merge into.
if ! git rev-parse --verify -q HEAD >/dev/null; then
  git add -A
  git commit -q -m "$MSG" ${TRAILER:+-m "$TRAILER"}
  echo "✔ publish_commit: initial commit on $(git symbolic-ref --short HEAD) ($(git rev-parse --short HEAD))"
  [[ "$PUSH" == "--push" ]] && git push -u origin HEAD
  exit 0
fi

CURRENT="$(git symbolic-ref --short HEAD)"
if [[ "$CURRENT" != "main" ]]; then
  echo "✖ publish_commit: start from main (currently on '$CURRENT')" >&2
  exit 1
fi

if [[ -z "$(git status --porcelain)" ]]; then
  echo "• publish_commit: nothing to commit — state already saved"
  exit 0
fi

SLUG="$(echo "$MSG" | sed -E 's/^[a-z]+(\([^)]*\))?: //; s/[^A-Za-z0-9]+/-/g; s/^-+|-+$//g' | tr 'A-Z' 'a-z' | cut -c1-40)"
BRANCH="publish/$(date +%Y%m%d-%H%M)-${SLUG}"

git switch -c "$BRANCH"
git add -A
git commit -q -m "$MSG" ${TRAILER:+-m "$TRAILER"}
git switch -q main
git merge --squash -q "$BRANCH"
git commit -q -m "$MSG" -m "Squash-merged from $BRANCH" ${TRAILER:+-m "$TRAILER"}
git branch -D -q "$BRANCH"

echo "✔ publish_commit: merged $BRANCH -> main ($(git rev-parse --short HEAD))"

if [[ "$PUSH" == "--push" ]]; then
  git push origin main
  echo "✔ publish_commit: pushed main to origin"
else
  echo "• publish_commit: not pushed (pass --push to push main to origin)"
fi
