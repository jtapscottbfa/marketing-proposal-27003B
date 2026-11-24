#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════
# scripts/publish/build_docx.sh
#
# Builds ALL proposal volumes from Markdown → .docx using Pandoc.
# Output files are written to _output/
#
# USAGE:
#   bash scripts/publish/build_docx.sh                # Build all volumes
#   bash scripts/publish/build_docx.sh --clean        # Clean _output/ first
#   bash scripts/publish/build_docx.sh --volumes 1,2  # Build specific volumes only
#
# DEPENDENCIES:
#   - pandoc (https://pandoc.org)  — install: brew install pandoc / apt install pandoc
#   - yq     (YAML parser)         — install: brew install yq / snap install yq
#   - envsubst (part of gettext)   — install: brew install gettext / apt install gettext
#
# SETUP:
#   1. Generate and brand templates/docx_reference/reference.docx (see templates/docx_reference/README.md)
#   2. Fill in 00_admin/proposal_config.yml (copied from .example)
#   3. Replace assets/logos/YOUR_LOGO_PLACEHOLDER.png with your firm logo
# ══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# shellcheck source=../lib/guard_cwd.sh
source "$REPO_ROOT/scripts/lib/guard_cwd.sh"
_guard_require_proposal_or_engine_root "$REPO_ROOT"

OUTPUT_DIR="$REPO_ROOT/_output"
CONFIG_FILE="$REPO_ROOT/00_admin/proposal_config.yml"
REFERENCE_DOC="$REPO_ROOT/templates/docx_reference/reference.docx"
COVER_TEMPLATE="$REPO_ROOT/templates/cover_page/cover_page.md"

# ── Colour helpers ─────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; CYAN='\033[0;36m'; RESET='\033[0m'

info()    { echo -e "${CYAN}ℹ${RESET}  $*"; }
success() { echo -e "${GREEN}✔${RESET}  $*"; }
warn()    { echo -e "${YELLOW}⚠${RESET}  $*"; }
error()   { echo -e "${RED}✖${RESET}  $*" >&2; }
die()     { error "$*"; exit 1; }

# ── Args ──────────────────────────────────────────────────────────────────────
CLEAN=false
VOLUME_FILTER=""
STRICT_LINT=false
SKIP_LINT=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --clean)    CLEAN=true; shift ;;
    --volumes)  VOLUME_FILTER="$2"; shift 2 ;;
    --strict)   STRICT_LINT=true; shift ;;
    --no-lint)  SKIP_LINT=true; shift ;;
    -h|--help)
      grep '^# ' "$0" | sed 's/^# //'
      echo ""
      echo "Lint flags:"
      echo "  --strict   Block on placeholder hits (use for CI / Gold Team builds)"
      echo "  --no-lint  Skip post-build placeholder scan entirely"
      exit 0
      ;;
    *) die "Unknown argument: $1" ;;
  esac
done

# ── Dependency checks ─────────────────────────────────────────────────────────
check_dep() {
  command -v "$1" &>/dev/null || die "$1 is not installed. See script header for install instructions."
}
check_dep pandoc
check_dep yq
check_dep envsubst

# ── Load config ───────────────────────────────────────────────────────────────
if [ ! -f "$CONFIG_FILE" ]; then
  die "Config not found: $CONFIG_FILE\nCopy 00_admin/proposal_config.yml.example → proposal_config.yml and fill it in."
fi

info "Loading proposal config from $CONFIG_FILE"

# Export config values as environment variables for envsubst
RFP_TITLE=$(yq e '.opportunity.rfp_title' "$CONFIG_FILE");       export RFP_TITLE
RFP_NUMBER=$(yq e '.opportunity.rfp_number' "$CONFIG_FILE");     export RFP_NUMBER
CLIENT_NAME=$(yq e '.opportunity.issuing_agency' "$CONFIG_FILE"); export CLIENT_NAME
FIRM_NAME=$(yq e '.firm.name' "$CONFIG_FILE");                   export FIRM_NAME
FIRM_ADDRESS=$(yq e '.firm.address' "$CONFIG_FILE");             export FIRM_ADDRESS
CONTACT_NAME=$(yq e '.contacts.proposal_manager.name' "$CONFIG_FILE");   export CONTACT_NAME
CONTACT_EMAIL=$(yq e '.contacts.proposal_manager.email' "$CONFIG_FILE"); export CONTACT_EMAIL
CONTACT_PHONE=$(yq e '.contacts.proposal_manager.phone' "$CONFIG_FILE"); export CONTACT_PHONE
SUBMISSION_DATE=$(yq e '.opportunity.submission_date' "$CONFIG_FILE");   export SUBMISSION_DATE

# ── Output directory ──────────────────────────────────────────────────────────
if $CLEAN && [ -d "$OUTPUT_DIR" ]; then
  info "Cleaning output directory..."
  rm -rf "$OUTPUT_DIR"
fi
mkdir -p "$OUTPUT_DIR"

# ── Volume definitions ────────────────────────────────────────────────────────
# Format: "folder_path|Volume Label|output_filename"
declare -a VOLUMES=(
  "01_executive_summary|Executive Summary|vol_00_executive_summary"
  "02_technical_volume|Volume I – Technical Approach|vol_01_technical"
  "03_management_volume|Volume II – Management Approach|vol_02_management"
  "04_past_performance|Volume III – Past Performance|vol_03_past_performance"
  "05_price_volume|Volume IV – Price|vol_04_price"
)

# ── Reference doc check ───────────────────────────────────────────────────────
if [ ! -f "$REFERENCE_DOC" ]; then
  info "Reference doc not found — generating branded reference.docx from firm styles..."
  node "$REPO_ROOT/scripts/publish/generate_reference_docx.js" \
    --rfp "$RFP_NUMBER" 2>&1 | sed 's/^/  /'
  if [ ! -f "$REFERENCE_DOC" ]; then
    warn "generate_reference_docx.js failed — falling back to Pandoc default (unstyled)"
    pandoc --print-default-data-file reference.docx > "$REFERENCE_DOC"
  fi
fi

# ── Node.js check for table post-processing ───────────────────────────────────
NODE_AVAILABLE=false
command -v node &>/dev/null && NODE_AVAILABLE=true

# ── Build function ────────────────────────────────────────────────────────────
build_volume() {
  local vol_folder="$1"
  local vol_label="$2"
  local out_name="$3"

  local vol_path="$REPO_ROOT/$vol_folder"
  local out_file="$OUTPUT_DIR/${out_name}.docx"
  local tmp_cover
  tmp_cover=$(mktemp /tmp/cover_XXXXXX.md)

  info "Building: $vol_label"

  # Gather all .md files in the volume folder (sorted)
  local md_files
  md_files=$(find "$vol_path" -maxdepth 2 -name "*.md" | sort)

  if [ -z "$md_files" ]; then
    warn "  No Markdown files found in $vol_folder — skipping"
    rm -f "$tmp_cover"
    return
  fi

  # Build cover page from template (substitutes env vars)
  # tr -d '\r' strips Windows CRLF injected by yq/envsubst on Windows hosts
  export VOLUME_LABEL="$vol_label"
  envsubst < "$COVER_TEMPLATE" | tr -d '\r' > "$tmp_cover"

  # Build with Pandoc
  # shellcheck disable=SC2086
  pandoc \
    --from=markdown+smart+yaml_metadata_block \
    --to=docx \
    --reference-doc="$REFERENCE_DOC" \
    --table-of-contents \
    --toc-depth=3 \
    --resource-path="$REPO_ROOT" \
    --output="$out_file" \
    "$tmp_cover" \
    $md_files

  rm -f "$tmp_cover"
  success "  → $out_file"

  # ── Post-process: fix table styles ─────────────────────────────────────────
  if $NODE_AVAILABLE; then
    local tmp_postproc="${out_file%.docx}_raw.docx"
    mv "$out_file" "$tmp_postproc"
    node "$REPO_ROOT/scripts/publish/post_process_tables.js" \
      "$tmp_postproc" "$out_file" 2>&1 | sed 's/^/    /'
    rm -f "$tmp_postproc"
  else
    warn "  node.js not found — skipping table post-processing (install Node.js for branded tables)"
  fi
}

# ── Main loop ─────────────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}══════════════════════════════════════════${RESET}"
echo -e "${CYAN}  Proposal Build  │  $RFP_NUMBER${RESET}"
echo -e "${CYAN}══════════════════════════════════════════${RESET}"
echo ""

BUILT=0
for entry in "${VOLUMES[@]}"; do
  IFS='|' read -r folder label outname <<< "$entry"
  vol_num="${folder%%_*}"

  # Filter by volume number if --volumes flag provided
  if [ -n "$VOLUME_FILTER" ]; then
    if ! echo ",$VOLUME_FILTER," | grep -q ",$vol_num,"; then
      continue
    fi
  fi

  build_volume "$folder" "$label" "$outname"
  BUILT=$((BUILT + 1))
done

echo ""
if [ "$BUILT" -gt 0 ]; then
  success "Build complete — $BUILT volume(s) written to _output/"
  echo ""
  ls -lh "$OUTPUT_DIR"/*.docx 2>/dev/null || true
else
  warn "No volumes built. Check --volumes filter: '$VOLUME_FILTER'"
fi

# ── Placeholder lint scan (GAP-45) ────────────────────────────────────────────
# Per-volume builds happen during authoring iteration, so the scan is warn-only
# by default — it surfaces issues early without blocking iteration. Use
# --strict to make it block (CI / Gold Team builds). Use --no-lint to skip.
if [ "$BUILT" -gt 0 ] && ! $SKIP_LINT; then
  echo ""
  info "Running placeholder lint scan..."
  if bash "$REPO_ROOT/scripts/publish/check_output_pdf.sh"; then
    success "Lint scan clear."
  else
    if $STRICT_LINT; then
      error "Lint scan found unresolved placeholders (--strict mode → blocking)."
      exit 1
    else
      warn "Lint scan found unresolved placeholders. Resolve them before"
      warn "running combine_volumes.sh — that script blocks on lint hits."
    fi
  fi
fi

echo ""
info "Next step: Run 'bash scripts/publish/combine_volumes.sh' to merge into a single submission file."
