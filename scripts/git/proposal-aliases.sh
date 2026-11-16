#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════
# scripts/git/aliases.sh
# Proposal-specific Git aliases and helper functions
#
# USAGE:
#   source scripts/git/aliases.sh
#
# Add to your shell profile for persistent availability:
#   echo 'source /path/to/proposal/scripts/git/aliases.sh' >> ~/.bashrc
# ══════════════════════════════════════════════════════════════════════════════

# ── Colour helpers ────────────────────────────────────────────────────────────
_BOLD=$(tput bold 2>/dev/null || echo "")
_RESET=$(tput sgr0 2>/dev/null || echo "")
_GREEN=$(tput setaf 2 2>/dev/null || echo "")
_YELLOW=$(tput setaf 3 2>/dev/null || echo "")
_CYAN=$(tput setaf 6 2>/dev/null || echo "")

# ── Core Workflow ─────────────────────────────────────────────────────────────

# prop-save: Stage all changes and commit with a message
# Usage: prop-save "message"
prop-save() {
  if [ -z "$1" ]; then
    echo "${_YELLOW}Usage: prop-save \"commit message\"${_RESET}"
    return 1
  fi
  git add -A && git commit -m "$1"
  echo "${_GREEN}✔ Saved: $1${_RESET}"
}

# prop-checkpoint: Save with auto-generated timestamp message
# Usage: prop-checkpoint
prop-checkpoint() {
  local msg
  msg="checkpoint: $(date '+%Y-%m-%d %H:%M') — auto-save"
  git add -A && git commit -m "$msg"
  echo "${_GREEN}✔ Checkpoint saved${_RESET}"
}

# prop-tag: Create an annotated version tag (for review gates)
# Usage: prop-tag v1.0-pink-team "Pink Team submission"
prop-tag() {
  if [ -z "$1" ]; then
    echo "${_YELLOW}Usage: prop-tag <tag-name> [\"annotation message\"]${_RESET}"
    echo "Examples:"
    echo "  prop-tag v1.0-pink-team"
    echo "  prop-tag v2.0-red-team \"Red Team review package\""
    return 1
  fi
  local annotation="${2:-Proposal milestone: $1}"
  git tag -a "$1" -m "$annotation"
  echo "${_GREEN}✔ Tag created: $1${_RESET}"
  echo "  Push with: git push origin $1"
}

# prop-tags: List all milestone tags
prop-tags() {
  echo "${_BOLD}${_CYAN}Proposal Milestones:${_RESET}"
  git tag -l --sort=-creatordate | while read -r tag; do
    local date
    date=$(git log -1 --format="%ai" "$tag" 2>/dev/null | cut -d' ' -f1)
    local msg
    msg=$(git tag -l -n1 "$tag" | sed "s/^$tag *//" )
    printf "  %-30s %s  %s\n" "${_YELLOW}$tag${_RESET}" "$date" "$msg"
  done
}

# ── Diff & Review ─────────────────────────────────────────────────────────────

# prop-diff: Word-level diff for prose (much more readable than line diff)
# Usage: prop-diff [file]
prop-diff() {
  git diff --word-diff=color "$@"
}

# prop-diff-tag: Word diff between two milestone tags
# Usage: prop-diff-tag v1.0-pink-team v2.0-red-team [file]
prop-diff-tag() {
  if [ -z "$2" ]; then
    echo "${_YELLOW}Usage: prop-diff-tag <tag1> <tag2> [file]${_RESET}"
    return 1
  fi
  git diff --word-diff=color "$1" "$2" "${@:3}"
}

# prop-log: Clean, readable commit log
prop-log() {
  git log \
    --pretty=format:"%C(yellow)%h%Creset %C(cyan)%ad%Creset | %s%C(green)%d%Creset [%an]" \
    --date=short \
    "$@"
}

# prop-log-files: Show commits with the files changed
prop-log-files() {
  git log \
    --pretty=format:"%C(yellow)%h%Creset %C(cyan)%ad%Creset | %s" \
    --date=short \
    --stat \
    "$@"
}

# ── Status & Hygiene ──────────────────────────────────────────────────────────

# prop-status: Clean status view
prop-status() {
  echo "${_BOLD}${_CYAN}Proposal Repository Status${_RESET}"
  echo "Branch: $(git branch --show-current)"
  echo "Latest commit: $(git log -1 --pretty=format:'%h %s (%ad)' --date=short)"
  echo ""
  git status -s
}

# prop-wc: Word count across all Markdown narrative files
prop-wc() {
  echo "${_BOLD}${_CYAN}Word Count by Volume${_RESET}"
  local total=0
  for vol in 01_executive_summary 02_technical_volume 03_management_volume \
             04_past_performance 05_price_volume; do
    if ls "$vol"/*.md &>/dev/null; then
      local count
      count=$(cat "$vol"/*.md | wc -w)
      printf "  %-35s %6d words\n" "$vol" "$count"
      total=$((total + count))
    fi
  done
  printf "  ${_BOLD}%-35s %6d words${_RESET}\n" "TOTAL" "$total"
}

# prop-pages: Estimate page count (rough: ~250 words/page)
prop-pages() {
  echo "${_BOLD}${_CYAN}Estimated Page Count (250 words/page)${_RESET}"
  for vol in 01_executive_summary 02_technical_volume 03_management_volume \
             04_past_performance 05_price_volume; do
    if ls "$vol"/*.md &>/dev/null; then
      local words
      words=$(cat "$vol"/*.md | wc -w)
      local pages=$(( (words + 249) / 250 ))
      printf "  %-35s ~%d pages\n" "$vol" "$pages"
    fi
  done
}

# ── Undo Helpers ──────────────────────────────────────────────────────────────

# prop-undo: Undo last commit but keep changes staged
prop-undo() {
  git reset --soft HEAD~1
  echo "${_YELLOW}✔ Last commit undone. Changes are staged.${_RESET}"
}

# prop-discard: Discard all unstaged changes (DESTRUCTIVE — asks for confirmation)
prop-discard() {
  echo "${_YELLOW}⚠️  This will discard ALL unstaged changes. Type 'yes' to confirm:${_RESET}"
  read -r confirm
  if [ "$confirm" = "yes" ]; then
    git checkout -- .
    echo "${_GREEN}✔ Unstaged changes discarded${_RESET}"
  else
    echo "Cancelled."
  fi
}

# ── Help ──────────────────────────────────────────────────────────────────────

prop-help() {
  echo "${_BOLD}${_CYAN}Proposal Git Aliases${_RESET}"
  echo ""
  echo "${_BOLD}Workflow:${_RESET}"
  echo "  prop-save \"message\"           Stage all and commit"
  echo "  prop-checkpoint               Auto-timestamped commit"
  echo "  prop-tag <name> [\"msg\"]       Tag a review gate milestone"
  echo "  prop-tags                     List all milestone tags"
  echo ""
  echo "${_BOLD}Review / Diff:${_RESET}"
  echo "  prop-diff [file]              Word-level diff (unstaged)"
  echo "  prop-diff-tag <t1> <t2>       Word diff between two tags"
  echo "  prop-log                      Pretty commit log"
  echo "  prop-log-files                Log with file stats"
  echo ""
  echo "${_BOLD}Status:${_RESET}"
  echo "  prop-status                   Repo status summary"
  echo "  prop-wc                       Word count by volume"
  echo "  prop-pages                    Estimated page count"
  echo ""
  echo "${_BOLD}Undo:${_RESET}"
  echo "  prop-undo                     Undo last commit (keep changes)"
  echo "  prop-discard                  Discard all unstaged changes"
}

echo "${_GREEN}✔ Proposal Git aliases loaded. Type 'prop-help' to see available commands.${_RESET}"
