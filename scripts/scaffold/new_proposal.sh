#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════
# scripts/scaffold/new_proposal.sh
#
# Scaffolds a new proposal repo from scratch.
# Generates folder structure, placeholder .md files, and proposal_config.yml
# based on either an interactive prompt or a YAML preset.
#
# USAGE:
#   Interactive:   bash scripts/scaffold/new_proposal.sh
#   From preset:   bash scripts/scaffold/new_proposal.sh --type sled_full
#   List presets:  bash scripts/scaffold/new_proposal.sh --list
#
# OUTPUT:
#   Creates a new proposal folder at the path you specify, fully structured
#   and ready to open in VS Code and push to GitHub.
# ══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TYPES_DIR="$SCRIPT_DIR/proposal_types"
TEMPLATES_DIR="$SCRIPT_DIR/section_templates"

# shellcheck source=../lib/guard_cwd.sh
source "$REPO_ROOT/scripts/lib/guard_cwd.sh"
_guard_require_proposal_or_engine_root "$REPO_ROOT"

# ── Colours ───────────────────────────────────────────────────────────────────
BOLD=$(tput bold 2>/dev/null || echo "")
RESET=$(tput sgr0 2>/dev/null || echo "")
GREEN=$(tput setaf 2 2>/dev/null || echo "")
YELLOW=$(tput setaf 3 2>/dev/null || echo "")
CYAN=$(tput setaf 6 2>/dev/null || echo "")
RED=$(tput setaf 1 2>/dev/null || echo "")

info()    { echo -e "${CYAN}ℹ${RESET}  $*"; }
success() { echo -e "${GREEN}✔${RESET}  $*"; }
warn()    { echo -e "${YELLOW}⚠${RESET}  $*"; }
die()     { echo -e "${RED}✖${RESET}  $*" >&2; exit 1; }
header()  { echo ""; echo "${BOLD}${CYAN}$*${RESET}"; echo ""; }

# ── Prompt helpers (GAP-18) ───────────────────────────────────────────────────
# Each helper assigns the answer to the variable named in $2.
# When called with a third arg (current value), shows it as an editable default
# and accepts Enter to keep it — used by the summary edit loop.

_prompt_nonempty() {
  local prompt="$1" varname="$2" current="${3:-}" answer
  while true; do
    if [ -n "$current" ]; then
      read -rp "$prompt [$current]: " answer
      [ -z "$answer" ] && answer="$current"
    else
      read -rp "$prompt: " answer
    fi
    if [ -n "$answer" ]; then
      printf -v "$varname" "%s" "$answer"
      return 0
    fi
    warn "Cannot be empty — please enter a value."
  done
}

_prompt_date() {
  local prompt="$1" varname="$2" current="${3:-}" answer
  while true; do
    if [ -n "$current" ]; then
      read -rp "$prompt [$current]: " answer
      [ -z "$answer" ] && answer="$current"
    else
      read -rp "$prompt: " answer
    fi
    if [ -z "$answer" ]; then
      warn "Cannot be empty — please enter a date."
      continue
    fi
    if [[ ! "$answer" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
      warn "Not in YYYY-MM-DD format. Accepting anyway — fix in proposal_config.yml if needed."
    fi
    printf -v "$varname" "%s" "$answer"
    return 0
  done
}

_prompt_optional() {
  local prompt="$1" varname="$2" current="${3:-}" answer
  if [ -n "$current" ]; then
    read -rp "$prompt [$current]: " answer
    [ -z "$answer" ] && answer="$current"
  else
    read -rp "$prompt: " answer
  fi
  printf -v "$varname" "%s" "$answer"
}

# ── Section library ───────────────────────────────────────────────────────────
# Format: "id|display_name|folder_prefix|placeholder_file"
declare -a SECTION_LIBRARY=(
  "executive_summary|Executive Summary|executive_summary|executive_summary.md"
  "cover_letter|Cover Letter|cover_letter|cover_letter.md"
  "tab_technical_approach|Technical Approach Tab|tab_technical_approach|tab_technical_approach.md"
  "tab_firms_experience|Firms & Experience Tab|tab_firms_experience|tab_firms_experience.md"
  "tab_key_personnel|Key Personnel Tab|tab_key_personnel|tab_key_personnel.md"
  "technical_approach|Technical Approach|technical_approach|technical_approach.md"
  "management_plan|Management Plan|management_plan|management_plan.md"
  "qualifications|Qualifications / Firm Experience|qualifications|qualifications.md"
  "past_performance|Past Performance / References|past_performance|past_performance.md"
  "staffing_plan|Staffing Plan|staffing_plan|staffing_plan.md"
  "project_schedule|Project Schedule|project_schedule|project_schedule.md"
  "price_volume|Price / Fee Proposal|price_volume|pricing_narrative.md"
  "subconsultant|Subconsultant Information|subconsultant|subconsultant_info.md"
  "quality_control|Quality Control|quality_control|quality_control.md"
  "geographic|Geographic Location / Local Presence|geographic_location|geographic_location.md"
  "construction_services|Construction Period Services|construction_services|construction_services.md"
  "appendices|Appendices / Attachments|appendices|README.md"
)

# ── Args ──────────────────────────────────────────────────────────────────────
PRESET_TYPE=""
LIST_PRESETS=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --type)    PRESET_TYPE="$2"; shift 2 ;;
    --list)    LIST_PRESETS=true; shift ;;
    -h|--help)
      echo "Usage:"
      echo "  bash scripts/scaffold/new_proposal.sh              # interactive"
      echo "  bash scripts/scaffold/new_proposal.sh --type sled_full"
      echo "  bash scripts/scaffold/new_proposal.sh --list"
      exit 0 ;;
    *) die "Unknown argument: $1" ;;
  esac
done

# ── List presets ──────────────────────────────────────────────────────────────
if $LIST_PRESETS; then
  header "Available Proposal Type Presets"
  for f in "$TYPES_DIR"/*.yml; do
    name=$(basename "$f" .yml)
    desc=$(grep '^description:' "$f" 2>/dev/null | sed 's/description: *//' | tr -d '"' || echo "")
    printf "  %-30s %s\n" "${YELLOW}$name${RESET}" "$desc"
  done
  echo ""
  exit 0
fi

# ══════════════════════════════════════════════════════════════════════════════
# PHASE 1 — Proposal metadata
# ══════════════════════════════════════════════════════════════════════════════
header "Proposal Scaffolding Tool"
echo "This script will generate a new proposal folder with the sections you select."
echo ""

# If using a preset, load section IDs from it
PRESET_SECTIONS=()
PRESET_LABEL=""
if [ -n "$PRESET_TYPE" ]; then
  PRESET_FILE="$TYPES_DIR/${PRESET_TYPE}.yml"
  [ ! -f "$PRESET_FILE" ] && die "Preset not found: $PRESET_TYPE\nRun --list to see available presets."
  PRESET_LABEL=$(grep '^description:' "$PRESET_FILE" | sed 's/description: *//' | tr -d '"')
  info "Using preset: ${YELLOW}$PRESET_TYPE${RESET} — $PRESET_LABEL"
  while IFS= read -r line; do
    [[ "$line" =~ ^[[:space:]]*-[[:space:]](.+) ]] && PRESET_SECTIONS+=("${BASH_REMATCH[1]}")
  done < <(grep -A 100 '^sections:' "$PRESET_FILE")
fi

# Collect metadata
echo "${BOLD}Proposal Details${RESET}"
echo "────────────────"
_prompt_nonempty "RFP / Solicitation title"          RFP_TITLE
_prompt_nonempty "RFP number"                        RFP_NUMBER
_prompt_nonempty "Issuing agency / client"           CLIENT_NAME
_prompt_date     "Submission date (YYYY-MM-DD)"      SUBMISSION_DATE
_prompt_optional "Output folder location (default: current dir)" OUTPUT_BASE
OUTPUT_BASE="${OUTPUT_BASE:-.}"

# ── Review + edit loop (GAP-18) ───────────────────────────────────────────────
# Lets the user fix typos without Ctrl+C and starting over.
while true; do
  echo ""
  echo "${BOLD}Review:${RESET}"
  echo "  1. RFP title:           $RFP_TITLE"
  echo "  2. RFP number:          $RFP_NUMBER"
  echo "  3. Issuing agency:      $CLIENT_NAME"
  echo "  4. Submission date:     $SUBMISSION_DATE"
  echo "  5. Output folder base:  $OUTPUT_BASE"
  echo ""
  read -rp "Confirm? [Y]es / [E]dit N / [Q]uit: " ANSWER
  ANSWER_LC="${ANSWER,,}"
  case "$ANSWER_LC" in
    ""|y|yes) break ;;
    q|quit)   echo "Cancelled."; exit 0 ;;
    e|edit)
      warn "Specify which field: e.g. 'edit 2' or 'e 4'"
      ;;
    e*)
      # SC2221: e* already covers anything starting with 'e' (including 'edit*'),
      # so no need for the extra alternative.
      FIELD=$(echo "$ANSWER" | grep -oE '[0-9]+' | head -1)
      case "$FIELD" in
        1) _prompt_nonempty "RFP / Solicitation title"          RFP_TITLE       "$RFP_TITLE" ;;
        2) _prompt_nonempty "RFP number"                        RFP_NUMBER      "$RFP_NUMBER" ;;
        3) _prompt_nonempty "Issuing agency / client"           CLIENT_NAME     "$CLIENT_NAME" ;;
        4) _prompt_date     "Submission date (YYYY-MM-DD)"      SUBMISSION_DATE "$SUBMISSION_DATE" ;;
        5) _prompt_optional "Output folder location"            OUTPUT_BASE     "$OUTPUT_BASE"
           OUTPUT_BASE="${OUTPUT_BASE:-.}" ;;
        "") warn "No field number found in '$ANSWER'. Use e.g. 'edit 2'." ;;
        *)  warn "No field $FIELD. Valid range: 1-5." ;;
      esac
      ;;
    *) warn "Unrecognized: '$ANSWER'. Use Y, E <num>, or Q." ;;
  esac
done

# Generate folder name from RFP number + client slug
CLIENT_SLUG=$(echo "$CLIENT_NAME" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-//;s/-$//')
RFP_SLUG=$(echo "$RFP_NUMBER" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g')
PROPOSAL_FOLDER="${OUTPUT_BASE}/proposal-${RFP_SLUG}-${CLIENT_SLUG}"

echo ""
info "Proposal folder will be created at: ${YELLOW}$PROPOSAL_FOLDER${RESET}"
read -rp "Press Enter to continue or type a different path: " CUSTOM_PATH
[ -n "$CUSTOM_PATH" ] && PROPOSAL_FOLDER="$CUSTOM_PATH"
[ -d "$PROPOSAL_FOLDER" ] && die "Folder already exists: $PROPOSAL_FOLDER"

# Resolve PROPOSAL_FOLDER to an absolute path for self-nesting check.
# Parent must exist (we don't create arbitrary parent trees); folder itself
# is expected NOT to exist yet (checked above).
_parent_dir="$(dirname "$PROPOSAL_FOLDER")"
[ ! -d "$_parent_dir" ] && die "Parent directory does not exist: $_parent_dir"
PROPOSAL_FOLDER_ABS="$(cd "$_parent_dir" && pwd)/$(basename "$PROPOSAL_FOLDER")"

# Refuse to scaffold inside the engine repo itself — a proposal nested inside
# the engine would pollute the template and mix live pursuit data with engine
# source. ARCH-16: prevent wrong-folder scaffolding.
if _guard_path_inside "$PROPOSAL_FOLDER_ABS" "$REPO_ROOT"; then
  die "Refusing to scaffold a proposal inside the engine repo:
       $PROPOSAL_FOLDER_ABS
       is inside
       $REPO_ROOT

       Re-run from a directory outside the engine repo, or specify a path
       outside it when prompted. A proposal must be its own repo, not a
       subfolder of ae-proposal-engine."
fi

PROPOSAL_FOLDER="$PROPOSAL_FOLDER_ABS"
unset _parent_dir PROPOSAL_FOLDER_ABS

# ══════════════════════════════════════════════════════════════════════════════
# PHASE 2 — Section selection
# ══════════════════════════════════════════════════════════════════════════════
header "Section Selection"

declare -a SELECTED_IDS=()

if [ ${#PRESET_SECTIONS[@]} -gt 0 ]; then
  # Use preset sections
  info "Sections from preset (in order):"
  for id in "${PRESET_SECTIONS[@]}"; do
    echo "  + $id"
    SELECTED_IDS+=("$id")
  done
else
  # Interactive selection
  echo "Select sections for this proposal."
  echo "Enter the numbers of sections you want, separated by spaces."
  echo "Order matters — enter them in the order they should appear."
  echo ""

  # Print menu
  declare -a LIB_IDS=()
  declare -a LIB_NAMES=()
  i=1
  for entry in "${SECTION_LIBRARY[@]}"; do
    IFS='|' read -r id name folder file <<< "$entry"
    LIB_IDS+=("$id")
    LIB_NAMES+=("$name")
    printf "  ${YELLOW}%2d${RESET}. %s\n" "$i" "$name"
    i=$((i+1))
  done

  echo ""
  # GAP-18: accept comma- OR space-separated input. Validate each entry as a
  # positive integer before arithmetic — bash arithmetic on a non-numeric
  # token under `set -euo pipefail` crashes the whole script.
  read -rp "Enter section numbers in order (e.g. '1 4 2 5' or '1,4,2,5'): " SELECTION_RAW
  SELECTION_RAW="$(echo "$SELECTION_RAW" | tr ',' ' ' | tr -s ' ')"
  read -ra SELECTION_NUMS <<< "$SELECTION_RAW"

  for num in "${SELECTION_NUMS[@]}"; do
    if ! [[ "$num" =~ ^[0-9]+$ ]]; then
      warn "Skipped invalid entry: '$num' (not a positive integer)"
      continue
    fi
    idx=$((num-1))
    if [ "$idx" -ge 0 ] && [ "$idx" -lt "${#LIB_IDS[@]}" ]; then
      SELECTED_IDS+=("${LIB_IDS[$idx]}")
    else
      warn "Invalid selection: $num — out of range (1-${#LIB_IDS[@]})"
    fi
  done
fi

# ── Custom sections ───────────────────────────────────────────────────────────
echo ""
declare -a CUSTOM_SECTIONS=()
while true; do
  read -rp "Add a custom section? (y/n): " ADD_CUSTOM
  [[ "$ADD_CUSTOM" != "y" && "$ADD_CUSTOM" != "Y" ]] && break
  read -rp "  Section name: " CUSTOM_NAME
  [ -z "$CUSTOM_NAME" ] && continue
  CUSTOM_SLUG=$(echo "$CUSTOM_NAME" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-//;s/-$//')
  CUSTOM_SECTIONS+=("$CUSTOM_SLUG|$CUSTOM_NAME")
  success "  Added: $CUSTOM_NAME"
done

# ── Confirm selection ─────────────────────────────────────────────────────────
echo ""
header "Proposal Structure Preview"

SECTION_ORDER=0
declare -a FINAL_SECTIONS=()   # "order|id|label|folder|file"

# Admin is always 00
FINAL_SECTIONS+=("00|admin|Admin|00_admin|")

for id in "${SELECTED_IDS[@]}"; do
  SECTION_ORDER=$((SECTION_ORDER+1))
  PADDED=$(printf "%02d" $SECTION_ORDER)
  # Look up in library
  found=false
  for entry in "${SECTION_LIBRARY[@]}"; do
    IFS='|' read -r lid lname lfolder lfile <<< "$entry"
    if [ "$lid" = "$id" ]; then
      folder="${PADDED}_${lfolder}"
      FINAL_SECTIONS+=("$PADDED|$id|$lname|$folder|$lfile")
      echo "  ${CYAN}$PADDED${RESET}  $lname  ${YELLOW}→ $folder/${RESET}"
      found=true
      break
    fi
  done
  $found || warn "Section ID not found in library: $id"
done

# Custom sections
for custom in "${CUSTOM_SECTIONS[@]}"; do
  SECTION_ORDER=$((SECTION_ORDER+1))
  PADDED=$(printf "%02d" $SECTION_ORDER)
  IFS='|' read -r cslug cname <<< "$custom"
  folder="${PADDED}_${cslug}"
  FINAL_SECTIONS+=("$PADDED|custom_${cslug}|$cname|$folder|${cslug}.md")
  echo "  ${CYAN}$PADDED${RESET}  $cname  ${YELLOW}→ $folder/ ${GREEN}[custom]${RESET}"
done

# Always add attachments last if not already included
if ! echo "${SELECTED_IDS[*]}" | grep -q "appendices"; then
  SECTION_ORDER=$((SECTION_ORDER+1))
  PADDED=$(printf "%02d" $SECTION_ORDER)
  FINAL_SECTIONS+=("$PADDED|attachments|Attachments|${PADDED}_attachments|README.md")
  echo "  ${CYAN}$PADDED${RESET}  Attachments  ${YELLOW}→ ${PADDED}_attachments/ ${GREEN}[auto-added]${RESET}"
fi

echo ""
read -rp "Proceed with this structure? (y/n): " CONFIRM
[[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]] && { echo "Cancelled."; exit 0; }

# ══════════════════════════════════════════════════════════════════════════════
# PHASE 3 — Generate folder structure
# ══════════════════════════════════════════════════════════════════════════════
header "Generating Proposal Structure"

mkdir -p "$PROPOSAL_FOLDER"

# Copy static assets from template
# `retrospectives` carries the empty per-pursuit scaffold folder + README;
# children fill it with their own post-mortems. Engine-historical retros
# live in `docs/retrospectives/` and are NOT copied — `docs/` is intentionally
# excluded so children don't inherit engine dev process artifacts.
for dir in assets templates scripts .github retrospectives; do
  if [ -d "$REPO_ROOT/$dir" ]; then
    cp -r "$REPO_ROOT/$dir" "$PROPOSAL_FOLDER/"
  fi
done

# Copy project-shared Claude Code config — the cwd-guard hook is repo-relative
# (uses `git rev-parse --show-toplevel`), so it enforces against the
# scaffolded proposal's own boundary, not the engine's. settings.local.json
# is gitignored and should NOT be copied (per-user override).
if [ -f "$REPO_ROOT/.claude/settings.json" ]; then
  mkdir -p "$PROPOSAL_FOLDER/.claude"
  cp "$REPO_ROOT/.claude/settings.json" "$PROPOSAL_FOLDER/.claude/"
fi

# Copy static root files
# CLAUDE.md carries the agent guardrail (cwd discipline, internal-notes
# convention) into child repos so agent sessions there behave identically.
# LICENSE is intentionally NOT copied — that license is for the engine code,
# not for the proposal content authored in the child repo.
for f in README.md .gitignore .markdownlint.yml compliance_matrix.md CLAUDE.md; do
  [ -f "$REPO_ROOT/$f" ] && cp "$REPO_ROOT/$f" "$PROPOSAL_FOLDER/"
done

# Create compliance_matrix.md placeholder
success "Copied template assets"

# ── Generate each section folder + placeholder .md ────────────────────────────
for entry in "${FINAL_SECTIONS[@]}"; do
  IFS='|' read -r order id label folder file <<< "$entry"

  full_path="$PROPOSAL_FOLDER/$folder"
  mkdir -p "$full_path"

  # Admin folder — copy existing admin files
  if [ "$id" = "admin" ]; then
    cp -r "$REPO_ROOT/00_admin/." "$full_path/"
    success "  $folder/"
    continue
  fi

  # Attachments — create subdirs
  if [ "$id" = "attachments" ]; then
    mkdir -p "$full_path/figures" "$full_path/data" "$full_path/letters_of_support"
    echo "# Attachments" > "$full_path/README.md"
    success "  $folder/"
    continue
  fi

  # Check for a section template
  TMPL="$TEMPLATES_DIR/${id}.md"
  if [ -f "$TMPL" ]; then
    cp "$TMPL" "$full_path/$file"
  else
    # Generate generic placeholder
    cat > "$full_path/$file" << MDEOF
---
title: "$label"
volume: "$label"
order: $order
status: "PLACEHOLDER — Author: [Name]"
---

# $label

> **PLACEHOLDER:** Replace this section with proposal content.
> Delete this notice before submission.

## Overview

\`PLACEHOLDER: Introduce this section. State the client's need and your approach in 2–3 sentences.\`

## Approach

\`PLACEHOLDER: Describe your approach in detail.\`

## Relevant Experience

\`PLACEHOLDER: Reference past performance that supports this section.\`
MDEOF
  fi

  success "  $folder/$file"
done

# ══════════════════════════════════════════════════════════════════════════════
# PHASE 4 — Generate proposal_config.yml
# ══════════════════════════════════════════════════════════════════════════════
CONFIG_FILE="$PROPOSAL_FOLDER/00_admin/proposal_config.yml"

# ── Firm profile pre-fill (ARCH-11) ───────────────────────────────────────────
# Read ~/.bfa/firm_profile.yml (or $BFA_FIRM_PROFILE) and pre-fill the
# firm.* block so the user doesn't have to type firm metadata in two
# places. Graceful fallback when:
#   - firm_profile.yml is missing       → keep placeholder defaults
#   - yq is not installed               → keep placeholder defaults + warn
#   - a specific field is PLACEHOLDER   → keep placeholder for that field
# Per-field detection means a partially-filled firm_profile.yml still
# pulls in whatever IS filled.

FIRM_NAME="Your Firm Name, Inc."
FIRM_SHORT="YourFirm"
FIRM_ADDRESS="PLACEHOLDER: Street, City, State, ZIP"
FIRM_WEBSITE="https://example.com"

FIRM_PROFILE_PATH="${BFA_FIRM_PROFILE:-$HOME/.bfa/firm_profile.yml}"

# Returns 0 + prints value if filled and not PLACEHOLDER; returns 1 otherwise.
_firm_profile_field() {
  local path="$1" expr="$2" val
  val=$(yq e ".$expr // \"\"" "$path" 2>/dev/null) || return 1
  case "$val" in
    PLACEHOLDER*|"") return 1 ;;
    *) printf "%s" "$val"; return 0 ;;
  esac
}

if [ -f "$FIRM_PROFILE_PATH" ]; then
  if ! command -v yq >/dev/null 2>&1; then
    warn "yq not found — firm profile auto-fill skipped. Install yq or fill firm.* fields manually."
  else
    loaded_fields=()
    if val=$(_firm_profile_field "$FIRM_PROFILE_PATH" "firm.name"); then
      FIRM_NAME="$val"
      loaded_fields+=("name")
    fi
    if val=$(_firm_profile_field "$FIRM_PROFILE_PATH" "firm.short_name"); then
      FIRM_SHORT="$val"
      loaded_fields+=("short_name")
    fi
    # Combine addr1 + addr2 into the proposal_config single-string `address`
    # field. Both must be filled for the join; otherwise keep the placeholder.
    if addr1=$(_firm_profile_field "$FIRM_PROFILE_PATH" "firm.addr1") && \
       addr2=$(_firm_profile_field "$FIRM_PROFILE_PATH" "firm.addr2"); then
      FIRM_ADDRESS="$addr1, $addr2"
      loaded_fields+=("address")
    fi
    if val=$(_firm_profile_field "$FIRM_PROFILE_PATH" "firm.website"); then
      FIRM_WEBSITE="$val"
      loaded_fields+=("website")
    fi

    if [ ${#loaded_fields[@]} -gt 0 ]; then
      info "Pre-filled firm.* from $FIRM_PROFILE_PATH (${loaded_fields[*]})"
    fi
  fi
else
  info "No firm profile at $FIRM_PROFILE_PATH — using placeholders"
  info "  Set up ~/.bfa/firm_profile.yml (see 00_admin/firm_profile.yml.example) to auto-fill firm.* on next scaffold."
fi

cat > "$CONFIG_FILE" << YAMEOF
# ══════════════════════════════════════════════════════════════════════════════
# proposal_config.yml — generated by new_proposal.sh
# Generated: $(date '+%Y-%m-%d %H:%M')
# ══════════════════════════════════════════════════════════════════════════════

opportunity:
  rfp_title:        "$RFP_TITLE"
  rfp_number:       "$RFP_NUMBER"
  issuing_agency:   "$CLIENT_NAME"
  submission_date:  "$SUBMISSION_DATE"
  submission_time:  "PLACEHOLDER: HH:MM TZ"
  submission_method: "PLACEHOLDER: Email / Portal / Physical"
  contract_type:    "PLACEHOLDER: Fixed-Price / T&M / IDIQ"
  contract_value:   "PLACEHOLDER: \$X,XXX,XXX"
  period_of_performance: "PLACEHOLDER: X years"

# Firm-level metadata — denormalized copy of ~/.bfa/firm_profile.yml.
# Auto-pre-filled by new_proposal.sh when firm_profile.yml is present.
# To keep this in sync after a firm profile update, re-run the relevant
# fields manually OR re-scaffold. The publish pipeline reads firm.* from
# this file; the AE-form populators read firm-level data from
# ~/.bfa/firm_profile.yml directly.
firm:
  name:             "$FIRM_NAME"
  short_name:       "$FIRM_SHORT"
  address:          "$FIRM_ADDRESS"
  website:          "$FIRM_WEBSITE"

contacts:
  proposal_manager:
    name:           "PLACEHOLDER: Full Name"
    title:          "PLACEHOLDER: Title"
    email:          "PLACEHOLDER: email@example.com"
    phone:          "PLACEHOLDER: (XXX) XXX-XXXX"

volumes:
YAMEOF

# Write volumes block
for entry in "${FINAL_SECTIONS[@]}"; do
  IFS='|' read -r order id label folder file <<< "$entry"
  [ "$id" = "admin" ] && continue
  cat >> "$CONFIG_FILE" << YAMEOF
  - id:     "$id"
    label:  "$label"
    folder: "$folder"
    active: true
    order:  $order

YAMEOF
done

success "proposal_config.yml generated"

# ══════════════════════════════════════════════════════════════════════════════
# PHASE 5 — Git init
# ══════════════════════════════════════════════════════════════════════════════
cd "$PROPOSAL_FOLDER"
git init -q
git add -A
git commit -q -m "init: scaffold proposal — $RFP_NUMBER — $CLIENT_NAME"
git branch -M main

# ══════════════════════════════════════════════════════════════════════════════
# Done
# ══════════════════════════════════════════════════════════════════════════════
header "Proposal Scaffolded Successfully"
echo "  ${BOLD}Location:${RESET}  $PROPOSAL_FOLDER"
echo "  ${BOLD}Sections:${RESET}  $SECTION_ORDER volumes"
echo "  ${BOLD}Config:${RESET}    00_admin/proposal_config.yml"
echo ""
echo "${BOLD}Next steps:${RESET}"
echo "  1. cd \"$PROPOSAL_FOLDER\""
echo "  2. code .                                    # open in VS Code"
echo "  3. Edit 00_admin/proposal_config.yml         # fill remaining PLACEHOLDERs"
echo "  4. ${YELLOW}Fill in 00_admin/proposal_schedule.md TODAY${RESET} — dates go stale fast"
echo "  5. source scripts/git/proposal-aliases.sh"
echo "  6. Create GitHub repo and: git remote add origin <url> && git push -u origin main"
echo ""
