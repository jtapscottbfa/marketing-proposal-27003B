#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════
# scripts/publish/check_output_pdf.sh
#
# Scans all .docx files in _output/ for unresolved placeholder text before
# upload. Works by extracting word/document.xml from each docx (which is a
# zip archive) and grepping the content — no external tools required.
#
# USAGE:
#   bash scripts/publish/check_output_pdf.sh
#   bash scripts/publish/check_output_pdf.sh path/to/specific.docx
#
# EXIT CODES:
#   0 — no placeholders found (safe to submit)
#   1 — placeholders found (do not submit)
#   2 — no output files found
# ══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# shellcheck source=../lib/guard_cwd.sh
source "$REPO_ROOT/scripts/lib/guard_cwd.sh"
_guard_require_proposal_or_engine_root "$REPO_ROOT"

OUTPUT_DIR="$REPO_ROOT/_output"

# ── Colour helpers ─────────────────────────────────────────────────────────────
BOLD=$'\033[1m'; RED=$'\033[0;31m'; GREEN=$'\033[0;32m'
YELLOW=$'\033[0;33m'; CYAN=$'\033[0;36m'; RESET=$'\033[0m'

header()  { echo "${BOLD}${CYAN}$*${RESET}"; }
success() { echo "${GREEN}✔${RESET}  $*"; }
warn()    { echo "${YELLOW}⚠${RESET}  $*"; }
# shellcheck disable=SC2329  # die() kept for consistency with other scripts; may be wired up later
die()     { echo "${RED}✖${RESET}  $*" >&2; exit 1; }

# ── Determine target files ────────────────────────────────────────────────────
if [ $# -gt 0 ]; then
  TARGET_FILES=("$@")
else
  mapfile -t TARGET_FILES < <(find "$OUTPUT_DIR" -maxdepth 1 \( -name "*.docx" -o -name "*.pdf" \) 2>/dev/null | sort)
fi

if [ ${#TARGET_FILES[@]} -eq 0 ]; then
  warn "No .docx or .pdf files found in _output/. Build first:"
  warn "  bash scripts/publish/build_docx.sh"
  exit 2
fi

# ── Placeholder patterns ──────────────────────────────────────────────────────
# Add patterns here as new placeholder conventions are introduced.
# GAP-45: [VERIFY], [FIXME], [TODO], [XX] added — these were leaking through.
# GAP-28: *End of draft*, [INTERNAL], [DRAFT] added — same retro source.
PATTERNS=(
  "PLACEHOLDER"
  "\[NUMBER\]"
  "\[TBD\]"
  "\[INSERT"
  "\[CONFIRM"
  "\[PENDING"
  "\[VERIFY"
  "\[NEEDS_VERIFICATION"
  "\[FIXME"
  "\[TODO"
  "\[XX\]"
  "\[XXX\]"
  "\[INTERNAL"
  "\[DRAFT\]"
  "\*End of draft\*"
  "End of draft"
)

# ── Scan function ─────────────────────────────────────────────────────────────
scan_docx() {
  local file="$1"
  local tmp
  tmp=$(mktemp /tmp/docx_check_XXXXXX.xml)
  trap 'rm -f "$tmp"' RETURN

  # Extract document body text from docx zip
  if ! unzip -p "$file" word/document.xml > "$tmp" 2>/dev/null; then
    warn "  Could not extract document.xml from $(basename "$file") — skipping" >&2
    echo 0; return
  fi

  # Strip XML tags to get plain text
  local text
  text=$(sed 's/<[^>]*>//g' "$tmp" | tr -s ' \t\n' ' ')

  local file_hits=0
  for pattern in "${PATTERNS[@]}"; do
    if echo "$text" | grep -qE "$pattern"; then
      # Print matches to stderr so they display without being captured by $()
      echo "$text" | grep -oE ".{0,40}${pattern}.{0,40}" | while IFS= read -r match; do
        echo "  ${RED}✖${RESET}  ...${match}..." >&2
      done
      file_hits=$((file_hits + 1))
    fi
  done

  echo "$file_hits"
}

scan_pdf() {
  local file="$1"
  if ! command -v pdfgrep &>/dev/null; then
    warn "  pdfgrep not found — cannot scan PDF. Install: brew install pdfgrep / apt install pdfgrep"
    echo "0"
    return
  fi

  local file_hits=0
  for pattern in "${PATTERNS[@]}"; do
    hits=$(pdfgrep -c "$pattern" "$file" 2>/dev/null || true)
    if [ "${hits:-0}" -gt 0 ]; then
      pdfgrep -n "$pattern" "$file" 2>/dev/null | while IFS= read -r match; do
        echo "  ${RED}✖${RESET}  $match"
      done
      file_hits=$((file_hits + hits))
    fi
  done
  echo "$file_hits"
}

# ── Main scan loop ────────────────────────────────────────────────────────────
echo ""
header "Output File Placeholder Audit"
echo ""

TOTAL_HITS=0

for file in "${TARGET_FILES[@]}"; do
  [ -f "$file" ] || { warn "File not found: $file — skipping"; continue; }
  echo "${BOLD}$(basename "$file")${RESET}"

  ext="${file##*.}"
  if [ "$ext" = "docx" ]; then
    file_hits=$(scan_docx "$file")
  elif [ "$ext" = "pdf" ]; then
    file_hits=$(scan_pdf "$file")
  else
    warn "  Unsupported file type: $ext — skipping"
    file_hits=0
  fi

  if [ "$file_hits" -eq 0 ]; then
    success "No placeholders found"
  fi

  TOTAL_HITS=$((TOTAL_HITS + file_hits))
  echo ""
done

# ── Result ────────────────────────────────────────────────────────────────────
if [ "$TOTAL_HITS" -eq 0 ]; then
  success "${BOLD}All clear — no unresolved placeholders found. Safe to upload.${RESET}"
  exit 0
else
  echo "${RED}${BOLD}✖  Unresolved placeholder(s) found — DO NOT SUBMIT.${RESET}"
  echo "   Resolve all items above, rebuild, and re-run this check."
  exit 1
fi