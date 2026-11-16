#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════
# scripts/proposal_digest.sh
#
# Reads one or more prior proposal PDFs, extracts every project / past-
# performance entry as a structured record, then scores the full project pool
# against the active pursuit's win themes and evaluation criteria — producing
# a ranked Project Selector you can use to pick and tailor narratives.
#
# USAGE:
#   bash scripts/proposal_digest.sh                        # digest all + score
#   bash scripts/proposal_digest.sh --digest-only          # extract projects only
#   bash scripts/proposal_digest.sh --score-only           # re-score existing digests
#   bash scripts/proposal_digest.sh --file path/to/X.pdf   # digest one file only
#
# REQUIRES:
#   - claude CLI  (npm install -g @anthropic-ai/claude-code)
#   - pdftotext   (optional; brew install poppler / choco install poppler)
#
# INPUT (drop files here before running):
#   00_admin/reference_proposals/   prior proposal PDFs (or .txt)
#
# OUTPUT:
#   00_admin/reference_proposals/{slug}/project_digest.md   per-source project DB
#   00_admin/reference_proposals/_claimed_clients.md        attestation list (DISC-19)
#   00_admin/project_selector.md                            ranked alignment matrix
#
# Each project record in project_digest.md uses a YAML frontmatter block for
# typed fields followed by a markdown body for narrative — see the schema in
# 00_admin/reference_proposals/README.md.
#
# Uncertain field values are marked [VERIFY]. The publish lint gate refuses
# to ship a docx containing [VERIFY] (per GAP-45 / ARCH-05).
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
ADMIN_DIR="$REPO_ROOT/00_admin"
REF_DIR="$ADMIN_DIR/reference_proposals"
SELECTOR_FILE="$ADMIN_DIR/project_selector.md"
CLAIMED_CLIENTS_FILE="$REF_DIR/_claimed_clients.md"
CONFIG_FILE="$ADMIN_DIR/proposal_config.yml"
WIN_THEMES_FILE="$ADMIN_DIR/win_themes.md"
TODAY="$(date '+%Y-%m-%d')"

# ── Args ──────────────────────────────────────────────────────────────────────
MODE="all"          # all | digest-only | score-only
SINGLE_FILE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --digest-only)  MODE="digest-only"; shift ;;
    --score-only)   MODE="score-only";  shift ;;
    --file|-f)      SINGLE_FILE="$2"; MODE="digest-only"; shift 2 ;;
    -h|--help)
      echo "Usage:"
      echo "  bash scripts/proposal_digest.sh                    # digest all + score"
      echo "  bash scripts/proposal_digest.sh --digest-only      # extract only"
      echo "  bash scripts/proposal_digest.sh --score-only       # re-score existing digests"
      echo "  bash scripts/proposal_digest.sh --file path/to/X.pdf"
      echo ""
      echo "Drop prior proposal PDFs into 00_admin/reference_proposals/ and run."
      exit 0 ;;
    -*) die "Unknown option: $1" ;;
    *)  die "Unexpected argument: $1 — use --file to specify a path" ;;
  esac
done

command -v claude &>/dev/null || die "'claude' CLI not found.\n  Install: npm install -g @anthropic-ai/claude-code"

mkdir -p "$REF_DIR"

# ══════════════════════════════════════════════════════════════════════════════
# PHASE 1 — Locate proposal files
# ══════════════════════════════════════════════════════════════════════════════

declare -a PROPOSAL_FILES=()

if [ -n "$SINGLE_FILE" ]; then
  [ ! -f "$SINGLE_FILE" ] && die "File not found: $SINGLE_FILE"
  PROPOSAL_FILES=("$SINGLE_FILE")
elif [ "$MODE" != "score-only" ]; then
  # Auto-detect PDFs / txt directly in reference_proposals/ (not in subfolders)
  mapfile -t PROPOSAL_FILES < <(find "$REF_DIR" -maxdepth 1 -type f \
    \( -iname "*.pdf" -o -iname "*.txt" \) | sort)

  if [ ${#PROPOSAL_FILES[@]} -eq 0 ]; then
    if [ "$MODE" = "digest-only" ]; then
      die "No proposal files found in $REF_DIR\n  Drop PDFs there and re-run."
    else
      info "No new proposals to digest in $REF_DIR — checking for existing digests to score..."
    fi
  else
    info "Found ${#PROPOSAL_FILES[@]} proposal file(s) to digest:"
    for f in "${PROPOSAL_FILES[@]}"; do
      echo "    ${YELLOW}·${RESET} $(basename "$f")"
    done
  fi
fi

# ══════════════════════════════════════════════════════════════════════════════
# PHASE 2 — Helpers
# ══════════════════════════════════════════════════════════════════════════════

slugify() {
  echo "$1" | tr '[:upper:]' '[:lower:]' \
    | sed 's/\.[^.]*$//' \
    | sed 's/[^a-z0-9]/-/g' \
    | sed 's/--*/-/g' \
    | sed 's/^-//;s/-$//'
}

pdf_to_text() {
  local src="$1" dest="$2"
  if command -v pdftotext &>/dev/null; then
    pdftotext -layout "$src" "$dest" 2>/dev/null && return 0
  fi
  return 1
}

# ── Typed schema digest prompt ───────────────────────────────────────────────
# Each project becomes a YAML frontmatter block (typed fields) followed by a
# markdown body (Scope / Notable / Excerpt). [VERIFY] is the canonical
# uncertainty marker.
digest_prompt() {
  local read_instruction="$1"
  local proposal_filename="$2"

  cat <<ENDPROMPT
You are a proposal analyst extracting past-performance and project data from a prior A/E proposal.

${read_instruction}

Your job: identify every distinct project, past-performance entry, or project callout in the document — whether in a formal past performance section, a project sheet, a qualifications narrative, or embedded within technical text.

For each project, output ONE record using the exact format below. Records are separated by a blank line. Use sequential IDs starting at PROJ-001.

## Schema rules

- Every record begins with a YAML frontmatter block (\`---\` ... \`---\`) followed by a markdown narrative body.
- For ANY field where the document does not state a value clearly enough to be quoted in a delivered proposal, write the literal string \`[VERIFY]\` (with the brackets). Do NOT write \"not stated\", \"unknown\", \"n/a\", or guess. \`[VERIFY]\` is a hard signal that downstream tooling will block on.
- Use double quotes around all string values in YAML to avoid quoting edge cases (apostrophes, colons, dashes, etc.).
- Tag enums (case-sensitive):
  - \`client_type\`: higher_ed | state_local | federal | private | healthcare | k12 | military
  - \`delivery\`: design-bid-build | design-build | CM-at-risk | term-contract | indefinite-delivery | other
  - \`contract_size\`: small | medium | large | unknown
- For \`discipline_tags\` and \`building_type_tags\`, use any from the lists below (and add others if genuinely needed):
  - disciplines: mechanical, electrical, plumbing, BAS, commissioning, fire-protection, civil, structural, lighting, telecom, security, AV, laboratory, energy-modeling, LCC-analysis, LEED
  - building types: higher-ed, k12, healthcare, laboratory, office, residential, athletic, historic, mixed-use, transit, industrial, government, library, performing-arts, data-center, parking, retail
- \`scope_summary\`: 2–3 sentences, present tense, factual. What systems were designed and why.
- \`notable_aspects\`: bullet list of discriminating details — certifications, special standards met, awards, specific technical approaches, measurable outcomes (budget, schedule, energy savings). Empty list if nothing notable is stated.
- \`raw_excerpt\`: copy ONE paragraph of original narrative prose verbatim. Choose the paragraph that best describes the project scope. This is source material for tailoring new narrative.

Output ONLY the project records — no preamble, no summary, no explanation. Use this exact format for every project:

---
id: "PROJ-001"
name: "[Project Name]"
client: "[Client / Owner]"
client_type: "[enum]"
year_completed: "[YYYY or [VERIFY]]"
contract_value: "[USD or [VERIFY]]"
contract_size: "[enum]"
delivery: "[enum]"
discipline_tags: ["[tag1]", "[tag2]"]
building_type_tags: ["[tag1]"]
source_proposal: "${proposal_filename}"
---

**Scope Summary**

[2–3 sentences]

**Notable Aspects**

- [bullet]
- [bullet]

**Raw Excerpt**

> [verbatim paragraph from source document]

ENDPROMPT
}

DIGESTED_FILES=()  # track all digest files produced or already existing

# ══════════════════════════════════════════════════════════════════════════════
# PHASE 3 — Digest each proposal
# ══════════════════════════════════════════════════════════════════════════════

if [ ${#PROPOSAL_FILES[@]} -gt 0 ] && [ "$MODE" != "score-only" ]; then
  header "Phase 1 — Digest Proposals"

  for PROP_FILE in "${PROPOSAL_FILES[@]}"; do
    BASENAME="$(basename "$PROP_FILE")"
    SLUG="$(slugify "$BASENAME")"
    SLUG_DIR="$REF_DIR/$SLUG"
    DIGEST_OUT="$SLUG_DIR/project_digest.md"

    mkdir -p "$SLUG_DIR"

    # Skip if digest already exists
    if [ -f "$DIGEST_OUT" ]; then
      warn "Digest already exists: $SLUG/project_digest.md — skipping (delete to re-digest)"
      DIGESTED_FILES+=("$DIGEST_OUT")
      continue
    fi

    info "Digesting: $BASENAME → reference_proposals/$SLUG/"

    PROP_ABS="$(cd "$(dirname "$PROP_FILE")" && pwd)/$(basename "$PROP_FILE")"
    EXT="${PROP_FILE##*.}"
    CONTENT_FILE=""

    if [[ "${EXT,,}" == "pdf" ]]; then
      TEMP_TXT="$SLUG_DIR/extracted_text_$$.txt"
      if pdf_to_text "$PROP_ABS" "$TEMP_TXT"; then
        CONTENT_FILE="$TEMP_TXT"
        READ_INSTRUCTION="The proposal has been extracted from PDF to plain text. Read the file at: $CONTENT_FILE"
        success "  PDF extracted to text"
      else
        warn "  pdftotext not available — passing PDF directly to Claude"
        warn "  For best results: brew install poppler / choco install poppler"
        READ_INSTRUCTION="Read the proposal PDF file at: $PROP_ABS"
      fi
    else
      CONTENT_FILE="$PROP_ABS"
      READ_INSTRUCTION="Read the proposal file at: $PROP_ABS"
    fi

    PROMPT="$(digest_prompt "$READ_INSTRUCTION" "$BASENAME")"

    RAW_OUT="$SLUG_DIR/raw_digest_$$.md"

    {
      echo "# Project Digest — $BASENAME"
      echo ""
      echo "> **Source Proposal:** $BASENAME"
      echo "> **Digested:** $TODAY"
      echo "> **Schema:** YAML frontmatter + markdown body per project"
      echo "> **Status:** AI-extracted — \`[VERIFY]\` markers indicate fields needing human review before use"
      echo ""
    } > "$DIGEST_OUT"

    claude --print -p "$PROMPT" >> "$RAW_OUT"

    # Validate Claude actually emitted at least one frontmatter block
    if ! grep -q "^id: \"PROJ-" "$RAW_OUT"; then
      warn "  Claude output is missing the YAML frontmatter shape — preserving raw output for inspection"
      warn "  Inspect: $RAW_OUT"
      cat "$RAW_OUT" >> "$DIGEST_OUT"
      die "Aborted — re-run after reviewing raw output."
    fi

    cat "$RAW_OUT" >> "$DIGEST_OUT"
    rm -f "$RAW_OUT"

    # Clean up temp text file
    [ -n "$CONTENT_FILE" ] && [ -f "$CONTENT_FILE" ] && \
      [[ "$CONTENT_FILE" == *"extracted_text_"* ]] && rm -f "$CONTENT_FILE"

    success "  Digest written: reference_proposals/$SLUG/project_digest.md"
    DIGESTED_FILES+=("$DIGEST_OUT")

    # Move the source PDF into the slug folder (keeps reference_proposals/ root clean)
    mv "$PROP_FILE" "$SLUG_DIR/"
    success "  Moved source to: reference_proposals/$SLUG/$BASENAME"
  done
fi

# Also collect any existing digests not just generated
if [ "$MODE" = "score-only" ] || [ "$MODE" = "all" ]; then
  while IFS= read -r digest_file; do
    already=false
    for existing in "${DIGESTED_FILES[@]:-}"; do
      [ "$existing" = "$digest_file" ] && already=true && break
    done
    $already || DIGESTED_FILES+=("$digest_file")
  done < <(find "$REF_DIR" -name "project_digest.md" | sort)
fi

# ══════════════════════════════════════════════════════════════════════════════
# PHASE 4 — Emit claimed-clients attestation list (DISC-19)
# ══════════════════════════════════════════════════════════════════════════════
# Every unique client name extracted across digests goes in here for human
# attestation. Pursuit narrative cannot reference a client until its checkbox
# is ticked. Closes DISC-19 (VT first draft listed unverified clients).

if [ ${#DIGESTED_FILES[@]} -gt 0 ]; then
  header "Phase 2 — Claimed Clients Attestation"

  CLIENTS_TMP="$(mktemp)"
  for digest in "${DIGESTED_FILES[@]}"; do
    # Pull `client: "..."` lines from frontmatter blocks
    grep -h '^client: ' "$digest" 2>/dev/null \
      | sed 's/^client: *"\(.*\)"$/\1/' \
      | sed 's/^client: *//' \
      | grep -v '^\[VERIFY\]$' \
      | sed "s|$| (from $(basename "$(dirname "$digest")"))|"
  done | sort -u > "$CLIENTS_TMP"

  CLIENT_COUNT=$(wc -l < "$CLIENTS_TMP" | tr -d ' ')

  {
    echo "# Claimed Clients — Verification Required"
    echo ""
    echo "> **Generated:** $TODAY"
    echo "> **Total:** $CLIENT_COUNT unique clients across ${#DIGESTED_FILES[@]} digest(s)"
    echo ">"
    echo "> Confirm each is a real prior client of this firm with a verifiable"
    echo "> reference. **Unchecked entries cannot be referenced in the active"
    echo "> pursuit narrative until verified.** Closes DISC-19."
    echo ""
    while IFS= read -r line; do
      echo "- [ ] $line"
    done < "$CLIENTS_TMP"
  } > "$CLAIMED_CLIENTS_FILE"

  rm -f "$CLIENTS_TMP"
  success "Claimed-clients list: reference_proposals/_claimed_clients.md (${CLIENT_COUNT} clients)"
fi

# ══════════════════════════════════════════════════════════════════════════════
# PHASE 5 — Score projects against active RFP
# ══════════════════════════════════════════════════════════════════════════════

if [ "$MODE" = "digest-only" ]; then
  header "Digest Complete"
  echo "  ${BOLD}Output:${RESET}  00_admin/reference_proposals/"
  echo ""
  echo "${BOLD}Next steps:${RESET}"
  echo "  Review each project_digest.md — verify [VERIFY]-marked fields."
  echo "  Tick the checkboxes in _claimed_clients.md for verified clients."
  echo "  Run without --digest-only to score projects against the active RFP."
  echo ""
  exit 0
fi

if [ ${#DIGESTED_FILES[@]} -eq 0 ]; then
  warn "No project digests found — nothing to score."
  warn "Run: bash scripts/proposal_digest.sh  (drop proposals in 00_admin/reference_proposals/ first)"
  exit 0
fi

header "Phase 3 — Score Projects Against Active RFP"

# ── Win themes — prefer proposal_config.yml, fall back to win_themes.md ──────
WIN_THEMES_CONTENT=""
if [ -f "$CONFIG_FILE" ] && command -v yq &>/dev/null; then
  CFG_THEMES="$(yq '.win_themes // ""' "$CONFIG_FILE" 2>/dev/null || true)"
  if [ -n "$CFG_THEMES" ] && [ "$CFG_THEMES" != "null" ] && [ "$CFG_THEMES" != '""' ]; then
    WIN_THEMES_CONTENT="$CFG_THEMES"
    info "Loaded win themes from proposal_config.yml"
  fi
fi
if [ -z "$WIN_THEMES_CONTENT" ] && [ -f "$WIN_THEMES_FILE" ]; then
  WIN_THEMES_CONTENT="$(cat "$WIN_THEMES_FILE")"
  info "Loaded: 00_admin/win_themes.md"
fi
[ -z "$WIN_THEMES_CONTENT" ] && warn "No win themes found — scoring will use evaluation criteria only"

# ── Find latest rfp_shred ─────────────────────────────────────────────────────
SHRED_FILE=""
mapfile -t SHRED_FILES < <(find "$ADMIN_DIR" -maxdepth 1 -name "rfp_shred_*.md" | sort -r)
if [ ${#SHRED_FILES[@]} -gt 0 ]; then
  SHRED_FILE="${SHRED_FILES[0]}"
  info "Loaded: $(basename "$SHRED_FILE")"
  SHRED_CONTENT="$(awk '/^## Section M — Evaluation Criteria/,/^---/' "$SHRED_FILE" | head -80)"
else
  warn "No rfp_shred_*.md found — scoring will use win themes only"
  SHRED_CONTENT=""
fi

# ── Assemble combined project pool ───────────────────────────────────────────
info "Assembling project pool from ${#DIGESTED_FILES[@]} digest(s)..."

POOL_FILE="$ADMIN_DIR/project_pool_$$.md"
{
  for digest in "${DIGESTED_FILES[@]}"; do
    # Skip the document header (lines before first `id: "PROJ-`); take the rest
    awk '/^id: "PROJ-/{found=1} found{print}' "$digest"
    echo ""
  done
} > "$POOL_FILE"

PROJECT_COUNT=$(grep -c '^id: "PROJ-' "$POOL_FILE" 2>/dev/null || echo "0")
info "Total projects in pool: $PROJECT_COUNT"

# ── Build scoring prompt ──────────────────────────────────────────────────────
SCORING_PROMPT=$(cat <<ENDPROMPT
You are a proposal strategist helping select and position past performance for a competitive A/E proposal.

## Active RFP Context

### Win Themes and Hot Buttons
$([ -n "$WIN_THEMES_CONTENT" ] && echo "$WIN_THEMES_CONTENT" | head -120 || echo "Not available.")

### Evaluation Criteria (Section M)
$([ -n "$SHRED_CONTENT" ] && echo "$SHRED_CONTENT" || echo "Not available.")

---

## Project Pool

Read the complete project pool from the file at: $POOL_FILE

Each project starts with a YAML frontmatter block (\`---\` ... \`---\`) containing typed fields, followed by a markdown body with Scope Summary, Notable Aspects, and Raw Excerpt sections. Fields containing \`[VERIFY]\` indicate uncertain values from the source proposal — flag these in the Verify? column of the output.

---

## Your Task

Score every project in the pool against this RFP. Produce the Project Selector document below — complete, no truncation.

Rules:
- Tier 1 (Lead Projects): directly match the client type, scope, and two or more win themes. Use as primary past performance references.
- Tier 2 (Supporting): match at least one win theme or have a directly relevant technical discriminator. Use as secondary references or callout boxes.
- Tier 3 (Weak Fit / Skip): minimal relevance. Do not include in this proposal unless the pool is thin.
- For each project: list which win themes it supports and why in one sentence.
- Flag any project where key data (value, year, client name) is \`[VERIFY]\` — set Verify? to ⚠ in those rows.
- In the Narrative Tailoring Notes column: write one sentence describing how to lead the project write-up for this specific RFP (which win theme to open with, what discriminator to emphasize).

Output ONLY the markdown document below, fully populated. No preamble.

---

# Project Selector
> **Pursuit:** [extract RFP title from context above]
> **Generated:** $TODAY
> **Projects Scored:** $PROJECT_COUNT
> **Source Digests:** ${#DIGESTED_FILES[@]} proposal(s)
>
> _AI-generated — verify project data before committing to proposal. Resolve all \`[VERIFY]\` markers and tick \`_claimed_clients.md\` checkboxes before authoring. Delete Tier 3 rows before writing._

---

## Tier 1 — Lead Projects

> _Primary past performance references. Use in the Past Performance volume and Technical Approach callout boxes._

| ID | Project Name | Client | Year | Value | Win Themes Supported | Narrative Tailoring Notes | Verify? |
|---|---|---|---|---|---|---|---|

---

## Tier 2 — Supporting Projects

> _Secondary references. Use as additional examples, sidebar callouts, or to reinforce specific win themes._

| ID | Project Name | Client | Year | Value | Win Themes Supported | Narrative Tailoring Notes | Verify? |
|---|---|---|---|---|---|---|---|

---

## Tier 3 — Weak Fit / Skip

> _Low relevance to this RFP. Do not include unless Tier 1 and Tier 2 are thin._

| ID | Project Name | Reason for Low Fit |
|---|---|---|

---

## Win Theme Coverage Map

> _Confirm every evaluated win theme has at least one Tier 1 or Tier 2 project supporting it._

| Win Theme | Tier 1 Projects | Tier 2 Projects | Gap? |
|---|---|---|---|

---

## Authoring Queue

> _Prioritized list of projects to write up first. Copy project IDs here as you start each write-up._

| Priority | Project ID | Project Name | Target Volume / Section | Status |
|---|---|---|---|---|
| 1 | | | | Not Started |
| 2 | | | | Not Started |
| 3 | | | | Not Started |
| 4 | | | | Not Started |
| 5 | | | | Not Started |

ENDPROMPT
)

info "Calling Claude to score $PROJECT_COUNT projects... (this may take 60–120 seconds)"

claude --print -p "$SCORING_PROMPT" > "$SELECTOR_FILE"

rm -f "$POOL_FILE"

success "Project Selector written: 00_admin/project_selector.md"

# ══════════════════════════════════════════════════════════════════════════════
# Done
# ══════════════════════════════════════════════════════════════════════════════
header "Proposal Digest Complete"
echo "  ${BOLD}Digests:${RESET}   00_admin/reference_proposals/"
for d in "${DIGESTED_FILES[@]}"; do
  slug_name="$(basename "$(dirname "$d")")"
  COUNT=$(grep -c '^id: "PROJ-' "$d" 2>/dev/null || echo "?")
  echo "             · $slug_name/project_digest.md  (${COUNT} projects)"
done
echo "  ${BOLD}Clients:${RESET}   00_admin/reference_proposals/_claimed_clients.md"
echo "  ${BOLD}Selector:${RESET}  00_admin/project_selector.md"
echo ""
echo "${BOLD}Next steps:${RESET}"
echo "  1. Review project_selector.md — verify Tier 1 picks and win-theme coverage"
echo "  2. Open _claimed_clients.md — tick checkboxes only for verified clients"
echo "  3. Open each project_digest.md — resolve [VERIFY] markers"
echo "  4. Fill in the Authoring Queue with chosen projects in priority order"
echo "  5. Re-run with --score-only after adding more proposals to update the selector"
echo ""
