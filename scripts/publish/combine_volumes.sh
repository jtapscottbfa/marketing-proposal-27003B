#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════
# scripts/publish/combine_volumes.sh
#
# Merges all individual volume .docx files from _output/ into a single
# combined submission document using pandoc-docx-pagebreaker or python-docx.
#
# STRATEGY:
#   Option A (recommended): Merge via Markdown concatenation → single Pandoc pass
#   Option B: Use python-docx to stitch pre-built .docx files
#   This script uses Option A for clean, style-consistent output.
#
# USAGE:
#   bash scripts/publish/combine_volumes.sh
#   bash scripts/publish/combine_volumes.sh --output "MyFirm_RFP-2025-001_Proposal.docx"
# ══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# shellcheck source=../lib/guard_cwd.sh
source "$REPO_ROOT/scripts/lib/guard_cwd.sh"
_guard_require_proposal_or_engine_root "$REPO_ROOT"

OUTPUT_DIR="$REPO_ROOT/_output"
CONFIG_FILE="$REPO_ROOT/00_admin/proposal_config.yml"
REFERENCE_DOC="$REPO_ROOT/templates/docx_reference/reference.docx"
COVER_TEMPLATE="$REPO_ROOT/templates/cover_page/cover_page.md"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; CYAN='\033[0;36m'; RESET='\033[0m'
info()    { echo -e "${CYAN}ℹ${RESET}  $*"; }
success() { echo -e "${GREEN}✔${RESET}  $*"; }
warn()    { echo -e "${YELLOW}⚠${RESET}  $*"; }
error()   { echo -e "${RED}✖${RESET}  $*" >&2; }
die()     { error "$*"; exit 1; }

# ── Args ──────────────────────────────────────────────────────────────────────
OUTPUT_NAME=""
SKIP_LINT=false
STRICT=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    --output)   OUTPUT_NAME="$2"; shift 2 ;;
    --no-lint)  SKIP_LINT=true; shift ;;
    --strict)   STRICT=true; shift ;;
    -h|--help)
      echo "Usage:"
      echo "  bash scripts/publish/combine_volumes.sh"
      echo "  bash scripts/publish/combine_volumes.sh --output \"FirmName_RFP_Proposal.docx\""
      echo "  bash scripts/publish/combine_volumes.sh --no-lint"
      echo "  bash scripts/publish/combine_volumes.sh --strict"
      echo ""
      echo "Options:"
      echo "  --output <name>  Override default output filename"
      echo "  --no-lint        Skip the placeholder lint gate (use only as a"
      echo "                   deliberate emergency override — DO NOT use to"
      echo "                   bypass real placeholder hits in the final file)"
      echo "  --strict         After lint passes, run sanity_check.py and treat"
      echo "                   MAJOR findings as blocking (default sanity contract"
      echo "                   blocks only on CRITICAL). Use for final pre-submission"
      echo "                   builds."
      exit 0 ;;
    *) die "Unknown argument: $1" ;;
  esac
done

# ── Dependencies ──────────────────────────────────────────────────────────────
command -v pandoc  &>/dev/null || die "pandoc is not installed"
command -v yq      &>/dev/null || die "yq is not installed"
command -v envsubst &>/dev/null || die "envsubst is not installed"

# ── Load config ───────────────────────────────────────────────────────────────
[ ! -f "$CONFIG_FILE" ] && die "Config not found: $CONFIG_FILE"

RFP_NUMBER=$(yq e '.opportunity.rfp_number' "$CONFIG_FILE");      export RFP_NUMBER
RFP_TITLE=$(yq e '.opportunity.rfp_title' "$CONFIG_FILE");        export RFP_TITLE
CLIENT_NAME=$(yq e '.opportunity.issuing_agency' "$CONFIG_FILE"); export CLIENT_NAME
FIRM_NAME=$(yq e '.firm.name' "$CONFIG_FILE");                    export FIRM_NAME
FIRM_ADDRESS=$(yq e '.firm.address' "$CONFIG_FILE");              export FIRM_ADDRESS
CONTACT_NAME=$(yq e '.contacts.proposal_manager.name' "$CONFIG_FILE");   export CONTACT_NAME
CONTACT_EMAIL=$(yq e '.contacts.proposal_manager.email' "$CONFIG_FILE"); export CONTACT_EMAIL
CONTACT_PHONE=$(yq e '.contacts.proposal_manager.phone' "$CONFIG_FILE"); export CONTACT_PHONE
SUBMISSION_DATE=$(yq e '.opportunity.submission_date' "$CONFIG_FILE");   export SUBMISSION_DATE
export VOLUME_LABEL="Complete Proposal"

# ── Output filename ───────────────────────────────────────────────────────────
if [ -z "$OUTPUT_NAME" ]; then
  # Auto-generate: FirmShortName_RFPNumber_Proposal_YYYYMMDD.docx
  FIRM_SHORT=$(yq e '.firm.short_name' "$CONFIG_FILE" | tr ' ' '_')
  RFP_SAFE=$(echo "$RFP_NUMBER" | tr '/ ' '--')
  DATE_STAMP=$(date '+%Y%m%d')
  OUTPUT_NAME="${FIRM_SHORT}_${RFP_SAFE}_Proposal_${DATE_STAMP}.docx"
fi

COMBINED_OUT="$OUTPUT_DIR/$OUTPUT_NAME"
mkdir -p "$OUTPUT_DIR"

# ── Collect all volume Markdown files ─────────────────────────────────────────
info "Collecting Markdown sources..."

VOLUME_DIRS=(
  "01_executive_summary"
  "02_technical_volume"
  "03_management_volume"
  "04_past_performance"
  "05_price_volume"
)

TMP_DIR=$(mktemp -d /tmp/proposal_combine_XXXXXX)
trap 'rm -rf "$TMP_DIR"' EXIT

ALL_FILES=()

# Cover page
TMP_COVER="$TMP_DIR/00_cover.md"
envsubst < "$COVER_TEMPLATE" > "$TMP_COVER"
ALL_FILES+=("$TMP_COVER")

# Volume separator page inserted between volumes
make_separator() {
  local label="$1"
  local sep_file
  sep_file="$TMP_DIR/sep_$(echo "$label" | tr ' ' '_').md"
  cat > "$sep_file" << EOF

---

\newpage

# $label

\newpage

EOF
  echo "$sep_file"
}

# Gather files
for vol_dir in "${VOLUME_DIRS[@]}"; do
  vol_path="$REPO_ROOT/$vol_dir"
  if [ ! -d "$vol_path" ]; then
    warn "Volume dir not found: $vol_dir — skipping"
    continue
  fi

  md_files=$(find "$vol_path" -maxdepth 2 -name "*.md" | sort)
  if [ -z "$md_files" ]; then
    warn "No .md files in $vol_dir — skipping"
    continue
  fi

  info "  + $vol_dir ($(echo "$md_files" | wc -l | tr -d ' ') files)"
  while IFS= read -r f; do
    ALL_FILES+=("$f")
  done <<< "$md_files"
done

if [ "${#ALL_FILES[@]}" -eq 0 ]; then
  die "No Markdown files found. Run authoring first."
fi

# ── Reference doc ─────────────────────────────────────────────────────────────
if [ ! -f "$REFERENCE_DOC" ]; then
  warn "Reference doc not found — generating unstyled default"
  pandoc --print-default-data-file reference.docx > "$REFERENCE_DOC"
fi

# ── Pandoc build ──────────────────────────────────────────────────────────────
info "Building combined proposal document..."
info "  Output: $COMBINED_OUT"

pandoc \
  --from=markdown+smart+yaml_metadata_block \
  --to=docx \
  --reference-doc="$REFERENCE_DOC" \
  --table-of-contents \
  --toc-depth=3 \
  --resource-path="$REPO_ROOT" \
  --output="$COMBINED_OUT" \
  "${ALL_FILES[@]}"

FILE_SIZE=$(du -h "$COMBINED_OUT" | cut -f1)
echo ""
success "Combined proposal built successfully"
echo ""
echo -e "  ${CYAN}File:${RESET} $COMBINED_OUT"
echo -e "  ${CYAN}Size:${RESET} $FILE_SIZE"
echo ""

# ── Placeholder lint gate (GAP-45) ────────────────────────────────────────────
# Hard block: combine_volumes is the final submission step. If unresolved
# placeholders or [VERIFY] tokens are in the output, this is the last chance
# to catch them before delivery (DISC-05 burned us once — won't happen again).
if $SKIP_LINT; then
  warn "──────────────────────────────────────────────────────────────"
  warn "  PLACEHOLDER LINT SKIPPED (--no-lint)"
  warn "  You are responsible for verifying the output by hand."
  warn "──────────────────────────────────────────────────────────────"
else
  info "Running placeholder lint gate on combined output..."
  if bash "$REPO_ROOT/scripts/publish/check_output_pdf.sh" "$COMBINED_OUT"; then
    success "Lint gate passed — combined proposal is clear of unresolved placeholders."
  else
    echo ""
    error "──────────────────────────────────────────────────────────────"
    error "  COMBINED PROPOSAL HAS UNRESOLVED PLACEHOLDERS — DO NOT SUBMIT"
    error "──────────────────────────────────────────────────────────────"
    error "  See list above. Resolve every entry, rebuild, and re-run."
    error "  To intentionally bypass (emergency only): --no-lint"
    exit 1
  fi
fi

# ── Sanity-check gate (--strict only) (issue #9 / ARCH-05) ────────────────────
# scripts/publish/sanity_check.py runs the full check inventory (verify-residue,
# placeholder-residue, markdown-as-text, prohibited-content, proof-points,
# addendum-acknowledgement, form-existence). Default contract blocks only on
# CRITICAL; --strict promotes MAJOR findings to blocking too.
if $STRICT; then
  echo ""
  info "Running sanity_check.py in strict mode..."
  if python "$REPO_ROOT/scripts/publish/sanity_check.py" \
        --repo-root "$REPO_ROOT" --strict; then
    success "Sanity check passed — package is submission-ready."
  else
    rc=$?
    echo ""
    error "──────────────────────────────────────────────────────────────"
    error "  SANITY CHECK FAILED (exit $rc) — DO NOT SUBMIT"
    error "──────────────────────────────────────────────────────────────"
    error "  Address the BLOCKING items above and re-run."
    exit "$rc"
  fi
fi

echo ""
warn "Before submission (manual checks the lint can't cover):"
echo "  1. Open in Word and verify all styles, headers, footers"
echo "  2. Check page counts against RFP limits (compliance_matrix.md)"
echo "  3. Get Gold Team sign-off (00_admin/color_team_reviews.md)"
