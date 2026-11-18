#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════
# scripts/rfp_shred.sh
#
# Uses Claude to read an RFP (primary + addendums + attachments), decompose it
# into a requirements matrix, identify likely subconsultant roles, pre-populate
# subconsultant_digest.md, and scaffold the subconsultant_intake/ folder —
# all in one pass.
#
# USAGE:
#   bash scripts/rfp_shred.sh                         # auto-collects all files
#                                                     #   under 00_admin/rfp_intake/
#   bash scripts/rfp_shred.sh --title "Example IFB-123"  # skip title prompt
#   bash scripts/rfp_shred.sh --file path/to/rfp.pdf     # override primary RFP
#                                                        #   (addendums/attachments
#                                                        #    still collected)
#
# REQUIRES:
#   - claude CLI  (npm install -g @anthropic-ai/claude-code)
#   - pdftotext   (for .pdf — brew install poppler / choco install poppler)
#   - pandoc      (for .docx — already a build-pipeline dependency)
#
# INPUT (drop files here before running):
#   00_admin/rfp_intake/original_rfp/   primary RFP document(s)
#   00_admin/rfp_intake/addendums/      addendums / revisions
#   00_admin/rfp_intake/attachments/    attachments, exhibits, reference specs,
#                                       standard contracts, drawings
#
# SUPPORTED FILE TYPES:
#   .pdf, .txt, .md, .docx
#   Other types are flagged as unreadable and listed at the end of the run
#   (they are NOT silently skipped — GAP-35).
#
# OUTPUT:
#   00_admin/rfp_shred_YYYYMMDD.md
#   00_admin/subconsultant_intake/subconsultant_digest.md
#   00_admin/subconsultant_intake/{role-slug}/received|resumes|project_sheets|letters/
# ══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# shellcheck source=lib/guard_cwd.sh
source "$REPO_ROOT/scripts/lib/guard_cwd.sh"
_guard_require_proposal_or_engine_root "$REPO_ROOT"

# ── Colours ───────────────────────────────────────────────────────────────────
BOLD=$(tput bold 2>/dev/null || echo "")
RESET=$(tput sgr0 2>/dev/null || echo "")
GREEN=$(tput setaf 2 2>/dev/null || echo "")
YELLOW=$(tput setaf 3 2>/dev/null || echo "")
CYAN=$(tput setaf 6 2>/dev/null || echo "")
RED=$(tput setaf 1 2>/dev/null || echo "")

info()    { echo "${CYAN}ℹ${RESET}  $*"; }
success() { echo "${GREEN}✔${RESET}  $*"; }
warn()    { echo "${YELLOW}⚠${RESET}  $*"; }
die()     { echo "${RED}✖${RESET}  $*" >&2; exit 1; }
header()  { echo ""; echo "${BOLD}${CYAN}$*${RESET}"; echo ""; }

# ── Paths ─────────────────────────────────────────────────────────────────────
OUT_DIR="$REPO_ROOT/00_admin"
RFP_INTAKE_DIR="$OUT_DIR/rfp_intake/original_rfp"
ADDENDUM_DIR="$OUT_DIR/rfp_intake/addendums"
ATTACHMENT_DIR="$OUT_DIR/rfp_intake/attachments"
INTAKE_DIR="$OUT_DIR/subconsultant_intake"
DIGEST_FILE="$INTAKE_DIR/subconsultant_digest.md"

# ── Args ──────────────────────────────────────────────────────────────────────
RFP_FILE_OVERRIDE=""
RFP_TITLE=""
OUTPUT_FILE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --file|-f)    RFP_FILE_OVERRIDE="$2"; shift 2 ;;
    --title|-t)   RFP_TITLE="$2"; shift 2 ;;
    --output|-o)  OUTPUT_FILE="$2"; shift 2 ;;
    -h|--help)
      echo "Usage:"
      echo "  bash scripts/rfp_shred.sh [options]"
      echo ""
      echo "Options:"
      echo "  --file, -f <path>     Override primary RFP (default: auto-detect"
      echo "                        from 00_admin/rfp_intake/original_rfp/)."
      echo "                        Addendums and attachments are still"
      echo "                        collected from their folders."
      echo "  --title, -t <title>   RFP title (default: prompted interactively)"
      echo "  --output, -o <path>   Shred output path"
      echo "                        (default: 00_admin/rfp_shred_YYYYMMDD.md)"
      echo ""
      echo "Drop files into 00_admin/rfp_intake/{original_rfp,addendums,attachments}/"
      echo "and run with no arguments."
      exit 0 ;;
    -*)  die "Unknown option: $1" ;;
    *)   die "Unexpected argument: $1 — use --file to specify an RFP path" ;;
  esac
done

command -v claude &>/dev/null || die "'claude' CLI not found.\n  Install: npm install -g @anthropic-ai/claude-code"

header "RFP Shred — Claude-Powered Requirements Decomposition"

# ── Ensure intake folders exist ───────────────────────────────────────────────
mkdir -p "$RFP_INTAKE_DIR" "$ADDENDUM_DIR" "$ATTACHMENT_DIR"

# ── Tempfile management ───────────────────────────────────────────────────────
# Bundle file is passed to Claude; raw output is Claude's response.
# Both are cleaned up on exit unless KEEP_TEMPS=true (set on validation failure
# so the user can inspect what went wrong instead of losing forensic state).
BUNDLE_FILE=""
RAW_OUTPUT=""
KEEP_TEMPS=false

_cleanup_temps() {
  if [ "$KEEP_TEMPS" = "true" ]; then
    [ -n "${BUNDLE_FILE:-}" ] && [ -f "$BUNDLE_FILE" ] && warn "Bundle preserved for inspection: $BUNDLE_FILE"
    [ -n "${RAW_OUTPUT:-}" ]  && [ -f "$RAW_OUTPUT" ]  && warn "Raw Claude output preserved: $RAW_OUTPUT"
    return
  fi
  [ -n "${BUNDLE_FILE:-}" ] && rm -f "$BUNDLE_FILE"
  [ -n "${RAW_OUTPUT:-}" ]  && rm -f "$RAW_OUTPUT"
}
trap _cleanup_temps EXIT

BUNDLE_FILE="$(mktemp /tmp/rfp_bundle_XXXXXX.txt)"

# ── File-type text extraction ─────────────────────────────────────────────────
# Usage: _extract_text <src> <dest_stream>
# Returns 0 on success, 1 on unreadable. On any failure, appends a clear
# "[unreadable — <reason>]" diagnostic line to the destination so callers
# don't need to write their own marker.
#
# GAP-34: validates that extraction tools that exit 0 also produced content.
# pdftotext / pandoc can return success while writing nothing (scanned PDFs,
# empty docx, etc.) — without the size delta check, that becomes a silent
# failure where Claude shreds an empty file and produces garbage.
_extract_text() {
  local src="$1" out="$2" ext before after
  ext="${src##*.}"
  ext="${ext,,}"
  before=$(stat --printf='%s' "$out" 2>/dev/null || echo 0)
  case "$ext" in
    txt|md)
      if ! cat "$src" >> "$out" 2>/dev/null; then
        echo "[unreadable — could not read .${ext} file (permission or I/O error)]" >> "$out"
        return 1
      fi
      ;;
    pdf)
      if ! command -v pdftotext &>/dev/null; then
        echo "[unreadable — pdftotext (poppler) not installed]" >> "$out"
        return 1
      fi
      if ! pdftotext -layout "$src" - >> "$out" 2>/dev/null; then
        echo "[unreadable — pdftotext extraction failed (corrupt or password-protected PDF)]" >> "$out"
        return 1
      fi
      ;;
    docx)
      if ! command -v pandoc &>/dev/null; then
        echo "[unreadable — pandoc not installed]" >> "$out"
        return 1
      fi
      if ! pandoc -t plain "$src" >> "$out" 2>/dev/null; then
        echo "[unreadable — pandoc extraction failed]" >> "$out"
        return 1
      fi
      ;;
    *)
      echo "[unreadable — unsupported extension: .${ext}]" >> "$out"
      return 1
      ;;
  esac
  after=$(stat --printf='%s' "$out" 2>/dev/null || echo 0)
  if [ "$after" -le "$before" ]; then
    echo "[unreadable — extraction tool returned success but produced no content (likely scanned PDF, empty file, or DRM-locked)]" >> "$out"
    return 1
  fi
  return 0
}

# ── Directory collection ──────────────────────────────────────────────────────
# Usage: _collect_dir <dir> <section_label> <bundle_out>
# Writes a "========== <label>: <filename> ==========" marker then extracted
# text for each file in <dir>. Adds unreadable files to the global UNREADABLE
# array. Uses sequential numbering for addendums.
UNREADABLE=()
READABLE_COUNT=0

_collect_dir() {
  local dir="$1" label="$2" out="$3" idx=0 marker
  local -a files
  mapfile -t files < <(find "$dir" -maxdepth 1 -type f ! -name '.gitkeep' 2>/dev/null | sort)
  for f in "${files[@]}"; do
    idx=$((idx + 1))
    marker="$label"
    [ "$label" = "ADDENDUM" ] && marker="ADDENDUM $idx"
    printf "\n\n========== %s: %s ==========\n\n" "$marker" "$(basename "$f")" >> "$out"
    if _extract_text "$f" "$out"; then
      READABLE_COUNT=$((READABLE_COUNT + 1))
    else
      UNREADABLE+=("$f")
    fi
  done
}

# ── Pre-flight tool check ─────────────────────────────────────────────────────
# GAP-34: warn about missing extraction tools BEFORE we run any extraction or
# call Claude. A failed extraction discovered after a billed Claude call is a
# wasted run; this prompt gives the user a chance to abort and install tools.
_pdf_in_intake=$(find "$RFP_INTAKE_DIR" "$ADDENDUM_DIR" "$ATTACHMENT_DIR" -maxdepth 1 -type f -iname "*.pdf" ! -name '.gitkeep' 2>/dev/null | head -1)
_docx_in_intake=$(find "$RFP_INTAKE_DIR" "$ADDENDUM_DIR" "$ATTACHMENT_DIR" -maxdepth 1 -type f -iname "*.docx" ! -name '.gitkeep' 2>/dev/null | head -1)

_preflight_missing=()
[ -n "$_pdf_in_intake" ]  && ! command -v pdftotext &>/dev/null && _preflight_missing+=("pdftotext (poppler) — needed for .pdf files")
[ -n "$_docx_in_intake" ] && ! command -v pandoc    &>/dev/null && _preflight_missing+=("pandoc — needed for .docx files")

if [ ${#_preflight_missing[@]} -gt 0 ]; then
  warn "Pre-flight: missing extraction tools:"
  for w in "${_preflight_missing[@]}"; do
    echo "    ${YELLOW}·${RESET} $w"
  done
  warn "Affected files will be flagged as unreadable in the shred output."
  read -rp "  Continue anyway? [y/N]: " _confirm
  [[ "${_confirm,,}" == "y" ]] || die "Aborted. Install missing tools and re-run."
fi

# ── Primary RFP override handling ─────────────────────────────────────────────
# If --file is passed, collect that one file as primary (instead of the
# auto-scan of original_rfp/). Addendums and attachments are still scanned
# from their folders.
declare -a PRIMARY_FILES=()
if [ -n "$RFP_FILE_OVERRIDE" ]; then
  [ ! -f "$RFP_FILE_OVERRIDE" ] && die "File not found: $RFP_FILE_OVERRIDE"
  PRIMARY_FILES=("$(cd "$(dirname "$RFP_FILE_OVERRIDE")" && pwd)/$(basename "$RFP_FILE_OVERRIDE")")
else
  mapfile -t PRIMARY_FILES < <(find "$RFP_INTAKE_DIR" -maxdepth 1 -type f ! -name '.gitkeep' 2>/dev/null | sort)
  [ ${#PRIMARY_FILES[@]} -eq 0 ] && die "No primary RFP files found in $RFP_INTAKE_DIR
  Drop your RFP there and re-run, or use --file path/to/rfp.pdf"
fi

# ── Collect content from all three folders ────────────────────────────────────
info "Collecting content from rfp_intake/..."

# Primary RFPs — loop manually so we share file-by-file extraction
_primary_idx=0
for f in "${PRIMARY_FILES[@]}"; do
  _primary_idx=$((_primary_idx + 1))
  marker="PRIMARY RFP"
  [ ${#PRIMARY_FILES[@]} -gt 1 ] && marker="PRIMARY RFP $_primary_idx"
  printf "\n\n========== %s: %s ==========\n\n" "$marker" "$(basename "$f")" >> "$BUNDLE_FILE"
  if _extract_text "$f" "$BUNDLE_FILE"; then
    READABLE_COUNT=$((READABLE_COUNT + 1))
  else
    UNREADABLE+=("$f")
  fi
done

_collect_dir "$ADDENDUM_DIR"    "ADDENDUM"   "$BUNDLE_FILE"
_collect_dir "$ATTACHMENT_DIR"  "ATTACHMENT" "$BUNDLE_FILE"

# Counts for the user-facing report
PRIMARY_COUNT=${#PRIMARY_FILES[@]}
ADDENDUM_COUNT=$(find "$ADDENDUM_DIR"    -maxdepth 1 -type f ! -name '.gitkeep' 2>/dev/null | wc -l)
ATTACHMENT_COUNT=$(find "$ATTACHMENT_DIR" -maxdepth 1 -type f ! -name '.gitkeep' 2>/dev/null | wc -l)

info "Collected: ${PRIMARY_COUNT} primary, ${ADDENDUM_COUNT} addendum(s), ${ATTACHMENT_COUNT} attachment(s)"
[ $READABLE_COUNT -eq 0 ] && die "No readable content extracted — aborting shred."
[ ${#UNREADABLE[@]} -gt 0 ] && warn "${#UNREADABLE[@]} file(s) unreadable — listed at end of run."

# ── RFP title ─────────────────────────────────────────────────────────────────
if [ -z "$RFP_TITLE" ]; then
  echo ""
  read -rp "  RFP title (e.g. Agency IFB-2025-001): " RFP_TITLE
  if [ -z "$RFP_TITLE" ]; then
    # Derive from primary RFP filename as fallback
    _first_primary="$(basename "${PRIMARY_FILES[0]}")"
    RFP_TITLE="${_first_primary%.*}"
    warn "No title entered — using filename: $RFP_TITLE"
  fi
fi

# ── Output path ───────────────────────────────────────────────────────────────
TODAY="$(date '+%Y-%m-%d')"
DATESTAMP="$(date '+%Y%m%d')"
[ -z "$OUTPUT_FILE" ] && OUTPUT_FILE="${OUT_DIR}/rfp_shred_${DATESTAMP}.md"

# ── Build Claude prompt ───────────────────────────────────────────────────────
echo ""
info "Calling Claude to shred the bundle... (this may take 30–90 seconds)"
echo ""

READ_INSTRUCTION="Read the consolidated RFP content bundle at: $BUNDLE_FILE

The bundle contains the primary RFP document(s), followed by any addendums and
attachments, each separated by a section marker like
'========== PRIMARY RFP: filename ==========' or
'========== ADDENDUM 1: filename ==========' or
'========== ATTACHMENT: filename =========='.

Apply addendum changes chronologically to the primary RFP — if an addendum
modifies a requirement, use the addendum's version. Include any binding
requirements that appear only in attachments (reference contracts, exhibits,
specifications). Flag any conflicts between primary, addendums, and
attachments in the Red Flags / Compliance Risks section.

If you see '[unreadable — content not extracted]' under a marker, note that
file in the Red Flags section — it means manual review is required."

PROMPT=$(cat <<ENDOFPROMPT
You are a federal/SLED proposal compliance analyst. Your job is to shred (decompose) an RFP into a structured requirements matrix, and identify the subconsultant disciplines this pursuit will likely require.

$READ_INSTRUCTION

Produce the following document exactly. Replace every PLACEHOLDER with real content from the RFP. Add as many rows as needed — one row per discrete requirement.

Rules:
- Extract every 'shall', 'must', 'will', and 'should' statement into Section L or Technical Requirements.
- Capture every evaluation factor and its stated weight/priority in Section M.
- Capture all format and submission requirements (page limits, font, file format, margins, etc.).
- Flag unusual, restrictive, or risky requirements in Red Flags.
- Draft questions worth submitting during the Q&A period.
- Use short RFP references like 'L.4.2' or 'M.1' based on the document structure.
- Assign sequential IDs: REQ-001, REQ-002 ... for Section L; EVAL-001 ... for Section M; TECH-001 ... for Technical.
- For each Section L row, populate 'Location in Proposal' with the volume/tab/section that will address it (e.g., 'Volume I — Technical Approach') and set 'Compliant?' to '☐'.
- Populate Key Facts at a Glance from the RFP; leave a cell blank if the value is not found.
- List every explicit pass/fail disqualifier in Minimum Qualifications; leave the table empty if none are stated. Set Status to 'TBD' for each row.
- For the Addendum Change Log: populate one row per addendum present in the bundle, with the sections affected, the change summary, and the impact on the proposal. If no addendums are present, leave the table empty.
- At the very end of your output, append two fenced code blocks:

  1. A block tagged 'roles' listing each subconsultant discipline on its own line — title case, no bullets, no numbering. Only include disciplines genuinely required or strongly implied by the scope.

  2. A block tagged 'config' with these fields extracted from the RFP (use empty string if not found):
     rfp_number:
     issuing_agency:
     submission_date: (YYYY-MM-DD)
     submission_time: (HH:MM TZ)
     submission_method: (e.g. Email / Portal / Physical)
     contract_type: (e.g. Fixed-Price / T&M / IDIQ)
     contract_value: (e.g. \$1,200,000)
     period_of_performance: (e.g. 3 years)
     page_limit_technical:
     page_limit_management:
     page_limit_past_performance:
     font:
     file_format:

Output ONLY the markdown document and the two code blocks — no preamble, no explanation.

---

# RFP Shred / Requirements Decomposition

> **RFP:** $RFP_TITLE
> **Source:** Primary RFP + ${ADDENDUM_COUNT} addendum(s) + ${ATTACHMENT_COUNT} attachment(s)
> **Shred Date:** $TODAY
> **Shredded By:** Claude (AI-assisted — verify all entries)

---

## How to Use This Document

1. Read the RFP front-to-back and paste every **shall**, **must**, **will**, and **should** statement into the table below.
2. Assign each requirement a unique ID (\`REQ-XXX\`).
3. Map each requirement to the proposal section that will respond to it.
4. Flag compliance risks (page limits, font, attachment requirements).
5. Use the Compliance Matrix (\`compliance_matrix.md\`) for the final cross-reference.

---

## Key Facts at a Glance

| Client | Procurement Number | Contract Type | Contract Value | Issue Date | Due Date | Submission Portal/Method | Page Limit | Evaluation Structure | MBE/DBE/SBE Goal |
|---|---|---|---|---|---|---|---|---|---|
| | | | | | | | | | |

---

## Pass/Fail Minimum Qualifications

> _Complete before scoring the bid/no-bid._

| Requirement | Source | Status |
|---|---|---|

---

## Section L — Instructions to Offerors

| ID | RFP Ref | Requirement / Instruction | Proposal Section | Location in Proposal | Compliant? | Notes / Risk |
|---|---|---|---|---|---|---|

---

## Section M — Evaluation Criteria

| ID | RFP Ref | Evaluation Factor | Weight / Priority | Proposal Section | Notes |
|---|---|---|---|---|---|

---

## Technical / Scope Requirements

| ID | RFP Ref | Requirement | Proposal Section | SME Owner | Notes |
|---|---|---|---|---|---|

---

## Format & Submission Requirements

| Requirement | Value | Complied? |
|---|---|---|
| Page limit (Technical) | | [ ] |
| Page limit (Management) | | [ ] |
| Page limit (Past Performance) | | [ ] |
| Font / size | | [ ] |
| Margin requirements | | [ ] |
| File format | | [ ] |
| File naming convention | | [ ] |
| Submission portal / method | | [ ] |
| Number of copies | | [ ] |

---

## Questions for Amendments / Q&A Period

| # | Question | Submitted? | Answer Received |
|---|---|---|---|

---

## Red Flags / Compliance Risks

-

---

## Addendum Change Log

| Addendum # | Date | Section Affected | Change Summary | Impact on Proposal |
|---|---|---|---|---|

\`\`\`roles
MEP Engineering
Civil Engineering
\`\`\`

\`\`\`config
rfp_number: RFP-2025-001
issuing_agency: Example Agency
submission_date: 2025-06-01
submission_time: 2:00 PM ET
submission_method: Portal
contract_type: Fixed-Price
contract_value: \$1,200,000
period_of_performance: 3 years
page_limit_technical: 20
page_limit_management: 10
page_limit_past_performance: 5
font: Times New Roman 12pt
file_format: PDF
\`\`\`
ENDOFPROMPT
)

# ── Call Claude → raw output ──────────────────────────────────────────────────
mkdir -p "$OUT_DIR" "$INTAKE_DIR"

RAW_OUTPUT="$(mktemp /tmp/rfp_raw_XXXXXX.md)"
claude --print -p "$PROMPT" > "$RAW_OUTPUT" || {
  KEEP_TEMPS=true
  die "Claude CLI returned non-zero. Check API key, rate limits, and bundle content."
}

# ── Validate Claude output (GAP-34) ──────────────────────────────────────────
# Catch the silent-failure case where Claude returns success but the output
# is empty or missing the required structural anchors.
if [ ! -s "$RAW_OUTPUT" ]; then
  KEEP_TEMPS=true
  die "Claude returned empty output. Possible causes: rate limit, network error, or empty bundle."
fi

_missing=()
grep -q "^# RFP Shred"      "$RAW_OUTPUT" || _missing+=("# RFP Shred heading")
grep -q '^```roles'         "$RAW_OUTPUT" || _missing+=("\`\`\`roles block")
grep -q '^```config'        "$RAW_OUTPUT" || _missing+=("\`\`\`config block")
if [ ${#_missing[@]} -gt 0 ]; then
  warn "Claude output is missing expected structure:"
  for m in "${_missing[@]}"; do
    echo "    ${YELLOW}·${RESET} $m"
  done
  KEEP_TEMPS=true
  die "Aborting — review the raw output and bundle, then re-run."
fi

# ── Split: shred doc (strip roles + config blocks) ───────────────────────────
awk '/^`{3,}roles$/,/^`{3,}$/ { next } /^`{3,}config$/,/^`{3,}$/ { next } { print }' "$RAW_OUTPUT" > "$OUTPUT_FILE"
[ ! -s "$OUTPUT_FILE" ] && { KEEP_TEMPS=true; die "Shred output empty after stripping code blocks — see raw output."; }
success "Shred written: $OUTPUT_FILE"

# ── Extract blocks helper ─────────────────────────────────────────────────────
extract_block() {
  local tag="$1" file="$2"
  local in_block=false
  while IFS= read -r line; do
    if [[ "$line" =~ ^\`{3,}"$tag"$ ]]; then in_block=true; continue; fi
    if [[ "$line" =~ ^\`{3,}$ ]] && $in_block; then in_block=false; continue; fi
    $in_block && [[ -n "$line" ]] && echo "$line"
  done < "$file"
}

# ── Extract roles list ────────────────────────────────────────────────────────
mapfile -t ROLES < <(extract_block "roles" "$RAW_OUTPUT")

# ── Extract config fields ─────────────────────────────────────────────────────
declare -A CFG=()
CFG_POPULATED=false
while IFS= read -r line; do
  key="${line%%:*}"
  val="${line#*: }"
  val="${val#"${val%%[![:space:]]*}"}"  # ltrim
  CFG["$key"]="$val"
  CFG_POPULATED=true
done < <(extract_block "config" "$RAW_OUTPUT")

if [ ${#ROLES[@]} -eq 0 ]; then
  warn "No roles extracted — digest and folders not created."
  warn "Add roles manually to $DIGEST_FILE"
else
  echo ""
  info "Roles identified: ${#ROLES[@]}"
  for role in "${ROLES[@]}"; do
    echo "    ${YELLOW}·${RESET} $role"
  done
fi

# ── Backfill proposal_config.yml ─────────────────────────────────────────────
CONFIG_YML="$OUT_DIR/proposal_config.yml"
if $CFG_POPULATED && [ -f "$CONFIG_YML" ]; then
  echo ""
  info "Backfilling proposal_config.yml from RFP data..."

  # Map config block keys → yml field names
  declare -A KEY_MAP=(
    [rfp_number]="rfp_number"
    [issuing_agency]="issuing_agency"
    [submission_date]="submission_date"
    [submission_time]="submission_time"
    [submission_method]="submission_method"
    [contract_type]="contract_type"
    [contract_value]="contract_value"
    [period_of_performance]="period_of_performance"
  )

  for cfg_key in "${!KEY_MAP[@]}"; do
    yml_key="${KEY_MAP[$cfg_key]}"
    val="${CFG[$cfg_key]:-}"
    [ -z "$val" ] && continue
    sed -i "s|^\([[:space:]]*${yml_key}:[[:space:]]*\).*|\1\"${val}\"|" "$CONFIG_YML"
    # GAP-34: verify the substitution actually happened. sed silently no-ops
    # if the key isn't found (renamed, typo, malformed yml).
    if grep -q "^[[:space:]]*${yml_key}:[[:space:]]*\"${val}\"" "$CONFIG_YML"; then
      success "  ${yml_key}: ${val}"
    else
      warn "  ${yml_key}: backfill failed — key '${yml_key}' not found in $CONFIG_YML"
    fi
  done

  sed -i "s|^\([[:space:]]*rfp_title:[[:space:]]*\).*|\1\"${RFP_TITLE}\"|" "$CONFIG_YML"
  if grep -q "^[[:space:]]*rfp_title:[[:space:]]*\"${RFP_TITLE}\"" "$CONFIG_YML"; then
    success "  rfp_title: ${RFP_TITLE}"
  else
    warn "  rfp_title: backfill failed — key 'rfp_title' not found in $CONFIG_YML"
  fi

elif [ ! -f "$CONFIG_YML" ]; then
  warn "proposal_config.yml not found — skipping backfill. Run new_proposal.sh first."
fi

# ── Populate subconsultant_digest.md ─────────────────────────────────────────
if [ ${#ROLES[@]} -gt 0 ]; then

  # Guard: if digest exists and has firm names filled in, don't overwrite
  if [ -f "$DIGEST_FILE" ]; then
    filled=$(awk -F'|' '/^\|/ && !/---/ && !/Firm Name/ && $2 !~ /^[[:space:]]*$/ { count++ } END { print count+0 }' "$DIGEST_FILE")
    if [ "$filled" -gt 0 ]; then
      warn "subconsultant_digest.md already has $filled firm(s) filled in — skipping overwrite."
      warn "Edit $DIGEST_FILE manually to add new roles, or delete it and re-run to regenerate."
      filled_digest=true
    else
      filled_digest=false
    fi
  else
    filled_digest=false
  fi

  if ! $filled_digest; then
    {
      echo "# Subconsultant Intake Digest"
      echo ""
      echo "> **RFP:** $RFP_TITLE"
      echo "> **Last Updated:** $TODAY"
      echo ""
      echo "| Firm Name | Role | POC Name | POC Email | MBE Status | Documents Received | Status |"
      echo "| --- | --- | --- | --- | --- | --- | --- |"
      for role in "${ROLES[@]}"; do
        echo "|  | ${role} |  |  |  |  | Pending |"
      done
      echo ""
    } > "$DIGEST_FILE"
    success "Digest pre-populated: $DIGEST_FILE"
  fi

  # ── Scaffold intake folders (always runs — additive, safe to re-run) ──────
  echo ""
  info "Scaffolding subconsultant_intake/ folders..."
  for role in "${ROLES[@]}"; do
    slug=$(echo "$role" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-//;s/-$//')
    mkdir -p "$INTAKE_DIR/$slug/received" "$INTAKE_DIR/$slug/resumes" \
             "$INTAKE_DIR/$slug/project_sheets" "$INTAKE_DIR/$slug/letters"
    success "  subconsultant_intake/$slug/"
  done
fi

# ── Unreadable files report ──────────────────────────────────────────────────
# Loud, not silent — the whole point of GAP-35.
if [ ${#UNREADABLE[@]} -gt 0 ]; then
  echo ""
  header "Unreadable Files (NOT shredded)"
  warn "${#UNREADABLE[@]} file(s) could not be extracted:"
  for f in "${UNREADABLE[@]}"; do
    echo "    ${RED}·${RESET} ${f#"$REPO_ROOT"/}"
  done
  echo ""
  warn "Possible reasons:"
  warn "  - Missing tool: install 'pdftotext' (poppler) for .pdf, 'pandoc' for .docx"
  warn "  - Unsupported format: current shred supports .pdf, .txt, .md, .docx"
  warn "  - File corrupted or password-protected"
  warn ""
  warn "Review these files manually and add requirements to the shred before"
  warn "proceeding to compliance mapping."
fi

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
header "Shred Complete"
echo "  ${BOLD}Shred doc:${RESET}  $OUTPUT_FILE"
echo "  ${BOLD}Config:${RESET}     $CONFIG_YML"
echo "  ${BOLD}Digest:${RESET}     $DIGEST_FILE"
echo "  ${BOLD}Intake:${RESET}     $INTAKE_DIR"
echo "  ${BOLD}Bundle:${RESET}     ${PRIMARY_COUNT} primary + ${ADDENDUM_COUNT} addendum(s) + ${ATTACHMENT_COUNT} attachment(s)"
if [ ${#UNREADABLE[@]} -gt 0 ]; then
  echo "  ${RED}${BOLD}Unreadable:${RESET} ${#UNREADABLE[@]} file(s) — see list above"
fi
echo ""
echo "${BOLD}Next steps:${RESET}"
echo "  1. Review $OUTPUT_FILE — verify all requirements, add any Claude missed"
echo "  2. Review $CONFIG_YML — confirm backfilled values, fill remaining PLACEHOLDERs"
echo "  3. Open $DIGEST_FILE — fill in Firm Name, POC Name, POC Email, MBE Status as you lock in your team"
echo "  4. Drop received docs into subconsultant_intake/{role}/received/"
echo "  5. Assign SME owners to TECH-* rows in the shred"
echo "  6. Submit Q&A questions before the deadline"
if [ ${#UNREADABLE[@]} -gt 0 ]; then
  echo "  7. ${YELLOW}Manually shred the unreadable files listed above${RESET}"
fi
echo ""
