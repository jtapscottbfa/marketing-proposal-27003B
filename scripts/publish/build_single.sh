#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════
# scripts/publish/build_single.sh
#
# Builds a SINGLE Markdown file → .docx for rapid iteration during drafting.
# Useful for reviewing formatting on one section without rebuilding everything.
#
# USAGE:
#   bash scripts/publish/build_single.sh <path/to/file.md>
#   bash scripts/publish/build_single.sh 02_technical_volume/technical_approach.md
#   bash scripts/publish/build_single.sh 02_technical_volume/technical_approach.md --open
# ══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# shellcheck source=../lib/guard_cwd.sh
source "$REPO_ROOT/scripts/lib/guard_cwd.sh"
_guard_require_proposal_or_engine_root "$REPO_ROOT"

OUTPUT_DIR="$REPO_ROOT/_output"
REFERENCE_DOC="$REPO_ROOT/templates/docx_reference/reference.docx"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; RESET='\033[0m'
success() { echo -e "${GREEN}✔${RESET}  $*"; }
warn()    { echo -e "${YELLOW}⚠${RESET}  $*"; }
die()     { echo -e "${RED}✖${RESET}  $*" >&2; exit 1; }

# ── Args ──────────────────────────────────────────────────────────────────────
INPUT_FILE="${1:-}"
OPEN_AFTER=false

[ -z "$INPUT_FILE" ] && die "Usage: bash build_single.sh <file.md> [--open]"

shift
while [[ $# -gt 0 ]]; do
  case "$1" in
    --open) OPEN_AFTER=true; shift ;;
    *) die "Unknown argument: $1" ;;
  esac
done

[ ! -f "$REPO_ROOT/$INPUT_FILE" ] && [ ! -f "$INPUT_FILE" ] && \
  die "File not found: $INPUT_FILE"

# Resolve to absolute path
INPUT_ABS="$(cd "$(dirname "$INPUT_FILE")" && pwd)/$(basename "$INPUT_FILE")"

# ── Output filename ───────────────────────────────────────────────────────────
mkdir -p "$OUTPUT_DIR"
BASENAME=$(basename "$INPUT_FILE" .md)
OUT_FILE="$OUTPUT_DIR/${BASENAME}.docx"

# ── Reference doc ─────────────────────────────────────────────────────────────
if [ ! -f "$REFERENCE_DOC" ]; then
  warn "Reference doc not found — generating unstyled default"
  pandoc --print-default-data-file reference.docx > "$REFERENCE_DOC"
fi

# ── Build ─────────────────────────────────────────────────────────────────────
echo "Building: $INPUT_FILE → $OUT_FILE"

pandoc \
  --from=markdown+smart+yaml_metadata_block \
  --to=docx \
  --reference-doc="$REFERENCE_DOC" \
  --table-of-contents \
  --toc-depth=3 \
  --resource-path="$REPO_ROOT" \
  --output="$OUT_FILE" \
  "$INPUT_ABS"

success "→ $OUT_FILE ($(du -h "$OUT_FILE" | cut -f1))"

# ── Optionally open in Word / LibreOffice ─────────────────────────────────────
if $OPEN_AFTER; then
  if command -v open &>/dev/null; then
    open "$OUT_FILE"
  elif command -v xdg-open &>/dev/null; then
    xdg-open "$OUT_FILE"
  else
    warn "--open: No file opener found (tried 'open' and 'xdg-open')"
  fi
fi
