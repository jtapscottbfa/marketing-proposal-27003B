#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════
# scripts/review/color_team_review.sh
#
# Runs a color team review (Pink / Red / Gold) using Claude and writes findings
# directly into 00_admin/color_team_reviews.md as YAML-frontmatter records per
# 00_admin/color_team_reviews.SCHEMA.md.
#
# USAGE:
#   bash scripts/review/color_team_review.sh --pink            # storyboard review
#   bash scripts/review/color_team_review.sh --red             # full draft review
#   bash scripts/review/color_team_review.sh --gold            # final approval
#   bash scripts/review/color_team_review.sh --pink --dry-run  # preview only
#   bash scripts/review/color_team_review.sh --red --force     # bypass gate guard
#
# REQUIRES:
#   - claude CLI (npm install -g @anthropic-ai/claude-code)
#   - yq         (https://github.com/mikefarah/yq)
#
# INPUTS (auto-discovered):
#   00_admin/proposal_config.yml         — volumes list (drives section enum)
#   00_admin/win_themes.md
#   00_admin/rfp_shred_*.md or rfp_shred.md   (latest by mtime)
#   00_admin/project_selector.md          (optional)
#   compliance_matrix.md
#   00_admin/rfp_intake/addendums/*       (addendum pre-flight)
#   <volume_folder>/*.md                  (per active volume in config)
#
# OUTPUT:
#   00_admin/color_team_reviews.md  (gate section replaced in-place)
#
# AC coverage (issue #7): #1 (script promotion), #2 (config-driven volume
# enumeration), #3 (YAML findings), #4 (Pink→Red gate), #7 (loud status),
# #8 (addendum pre-flight). Closure lock (#5) and Blue/Black Hat (#6) land in
# follow-up PRs.
# ══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

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

info()    { echo "${CYAN}ℹ${RESET}  $*"; }
success() { echo "${GREEN}✔${RESET}  $*"; }
warn()    { echo "${YELLOW}⚠${RESET}  $*"; }
die()     { echo "${RED}✖${RESET}  $*" >&2; exit 1; }
header()  { echo ""; echo "${BOLD}${CYAN}$*${RESET}"; echo ""; }

# ── Paths ─────────────────────────────────────────────────────────────────────
ADMIN_DIR="$REPO_ROOT/00_admin"
REVIEWS_FILE="$ADMIN_DIR/color_team_reviews.md"
CONFIG_FILE="$ADMIN_DIR/proposal_config.yml"
WIN_THEMES_FILE="$ADMIN_DIR/win_themes.md"
SELECTOR_FILE="$ADMIN_DIR/project_selector.md"
COMPLIANCE_FILE="$REPO_ROOT/compliance_matrix.md"
ADDENDA_DIR="$ADMIN_DIR/rfp_intake/addendums"
TODAY="$(date '+%Y-%m-%d')"

# ── Args ──────────────────────────────────────────────────────────────────────
MODE=""
DRY_RUN=false
FORCE=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --pink)    MODE="pink";    shift ;;
    --red)     MODE="red";     shift ;;
    --gold)    MODE="gold";    shift ;;
    --dry-run) DRY_RUN=true;   shift ;;
    --force)   FORCE=true;     shift ;;
    -h|--help)
      cat <<'USAGE'
Usage:
  bash scripts/review/color_team_review.sh --pink              # Pink Team
  bash scripts/review/color_team_review.sh --red               # Red Team
  bash scripts/review/color_team_review.sh --gold              # Gold Team
  bash scripts/review/color_team_review.sh --pink --dry-run    # preview only
  bash scripts/review/color_team_review.sh --red --force       # bypass gate guard

The script reads `00_admin/proposal_config.yml` to enumerate active volumes
(see the `volumes:` block) and includes their `.md` content as input to the
Claude review. Findings are written to `00_admin/color_team_reviews.md` as
YAML-frontmatter records per `00_admin/color_team_reviews.SCHEMA.md`.

Gate ordering (configurable via --force):
  pink → red → gold

Pre-flight checks per gate:
  1. Addendum freshness — RFP shred newer than every addendum file (GAP-33).
  2. Prior gate H findings — must be resolved or accepted (GAP-38, GAP-49).
USAGE
      exit 0 ;;
    -*) die "Unknown option: $1" ;;
    *)  die "Unexpected argument: $1" ;;
  esac
done

[ -z "$MODE" ] && die "Specify a review mode: --pink, --red, or --gold (--help for usage)"
command -v claude &>/dev/null || die "'claude' CLI not found. Install: npm install -g @anthropic-ai/claude-code"
command -v yq     &>/dev/null || die "'yq' not found. Install: https://github.com/mikefarah/yq"
[ -f "$REVIEWS_FILE" ] || die "color_team_reviews.md not found: $REVIEWS_FILE"
[ -f "$CONFIG_FILE" ]  || die "proposal_config.yml not found: $CONFIG_FILE  (copy from .example and fill in)"

# ══════════════════════════════════════════════════════════════════════════════
# Helpers — input discovery
# ══════════════════════════════════════════════════════════════════════════════

# Echo "folder|label|id" for each active volume, sorted by `order`.
# AC #2 — config-driven volume enumeration.
load_active_volumes() {
  yq e '
    .volumes // []
    | map(select(.active == true or .active == null))
    | sort_by(.order // 9999)
    | .[]
    | (.folder + "|" + .label + "|" + .id)
  ' "$CONFIG_FILE"
}

# Echo every .md file (one per line) inside the given volume folder, max-depth 2.
# Skips compiled output and assembly artifacts.
discover_volume_files() {
  local folder="$1"
  local abs="$REPO_ROOT/$folder"
  [ -d "$abs" ] || return 0
  find "$abs" -maxdepth 2 -name "*.md" -type f \
    ! -name "_compiled.md" ! -name "README.md" 2>/dev/null | sort
}

# Latest RFP shred file (rfp_shred.md or rfp_shred_YYYYMMDD.md). Returns empty
# if none exist.
find_latest_shred() {
  # Use mtime (the addendum-freshness check below relies on it). If multiple
  # dated shreds exist, the newest mtime wins.
  local f
  f="$(find "$ADMIN_DIR" -maxdepth 1 -type f \
    \( -name "rfp_shred.md" -o -name "rfp_shred_*.md" \) \
    -not -name "*.template" 2>/dev/null \
    | while read -r p; do printf '%s\t%s\n' "$(stat -c '%Y' "$p" 2>/dev/null || stat -f '%m' "$p")" "$p"; done \
    | sort -rn | head -1 | cut -f2-)"
  echo "$f"
}

# Newest addendum file mtime as epoch seconds (or empty if no addenda).
latest_addendum_mtime() {
  [ -d "$ADDENDA_DIR" ] || return 0
  find "$ADDENDA_DIR" -type f \
    \( -name "*.pdf" -o -name "*.md" -o -name "*.docx" \) 2>/dev/null \
    | while read -r p; do stat -c '%Y' "$p" 2>/dev/null || stat -f '%m' "$p"; done \
    | sort -rn | head -1
}

# ══════════════════════════════════════════════════════════════════════════════
# Helpers — pre-flight checks (loud failures, AC #7)
# ══════════════════════════════════════════════════════════════════════════════

# Print a loud red banner. Used by gate-blocked failures so they cannot be
# missed in a long script log (closes GAP-38).
loud_block() {
  local title="$1"; shift
  echo ""
  echo "${BOLD}${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
  echo "${BOLD}${RED}  ${title}${RESET}"
  echo "${BOLD}${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
  echo ""
  for line in "$@"; do echo "  $line"; done
  echo ""
}

# AC #8 — addendum pre-flight. Block if any addendum file is newer than the
# latest RFP shred. The shred is what reviewers cite as "what the RFP says";
# letting it fall behind a new addendum is the GAP-33 failure mode.
check_addendum_freshness() {
  local shred shred_mtime addendum_mtime
  shred="$(find_latest_shred)"
  addendum_mtime="$(latest_addendum_mtime)"

  # No addenda — nothing to check.
  [ -z "$addendum_mtime" ] && return 0

  if [ -z "$shred" ]; then
    loud_block "ADDENDUM PRE-FLIGHT FAILED" \
      "Found addendum file(s) in 00_admin/rfp_intake/addendums/ but no RFP shred." \
      "Run: bash scripts/rfp_shred.sh" \
      "Then re-run this gate."
    $FORCE || die "Addendum pre-flight failed. Pass --force to override."
    warn "--force given; proceeding despite missing shred."
    return 0
  fi

  shred_mtime="$(stat -c '%Y' "$shred" 2>/dev/null || stat -f '%m' "$shred")"

  if [ "$addendum_mtime" -gt "$shred_mtime" ]; then
    loud_block "ADDENDUM PRE-FLIGHT FAILED (closes GAP-33)" \
      "RFP shred is older than the latest addendum:" \
      "  Shred: $(realpath --relative-to="$REPO_ROOT" "$shred" 2>/dev/null || echo "$shred")" \
      "  Addendum mtime: newer than shred" \
      "" \
      "Re-run: bash scripts/rfp_shred.sh" \
      "Or pass --force to override (the review will not reflect addendum changes)."
    $FORCE || die "Addendum pre-flight failed. Pass --force to override."
    warn "--force given; proceeding with stale shred."
  else
    info "Addendum pre-flight OK (shred newer than latest addendum)."
  fi
}

# AC #4 + #7 — gate ordering with loud status. Parses YAML frontmatter records
# in REVIEWS_FILE; if any record has the given prefix, status=open, priority=H,
# block the gate (unless --force).
check_prior_gate() {
  local prefix="$1" gate_name="$2"
  local open_high
  open_high="$(extract_open_high_findings "$prefix")"

  if [ -n "$open_high" ]; then
    local count
    count="$(echo "$open_high" | wc -l | tr -d ' ')"
    loud_block "GATE BLOCKED: ${gate_name} HAS ${count} UNRESOLVED H FINDING(S)" \
      "Open H-priority finding(s):" \
      "$(echo "$open_high" | sed 's/^/  - /')" \
      "" \
      "Resolve or risk-accept each before advancing:" \
      "  bash scripts/review/review_triage.sh --remediate <ID>" \
      "  bash scripts/review/review_triage.sh --accept    <ID> \"reason\"" \
      "" \
      "Or bypass:  --force  (logged in the audit trail)"
    $FORCE || die "Prior gate must close. Pass --force to override."
    warn "--force given; proceeding with ${count} open ${gate_name} H finding(s)."
  else
    info "${gate_name} clear (no open H-priority findings)."
  fi
}

# Emit the IDs of YAML records in REVIEWS_FILE matching:
#   id starts with $1, status == "open", priority == "H".
#
# REVIEWS_FILE is markdown with embedded YAML frontmatter blocks. We extract
# blocks via awk into a multi-doc YAML stream, then yq filters per-doc.
extract_open_high_findings() {
  local prefix="$1"
  awk '
    /^---[[:space:]]*$/ {
      if (in_block) {
        # End of a block: emit a doc separator so yq sees the next block as
        # a new YAML document.
        printf "---\n"
        in_block = 0
      } else {
        in_block = 1
      }
      next
    }
    in_block { print }
  ' "$REVIEWS_FILE" \
  | yq e 'select(
      .id != null
      and (.id | test("^'"$prefix"'-"))
      and .status == "open"
      and .priority == "H"
    ) | .id' - 2>/dev/null \
  | grep -Ev '^(null|)$' || true
}

# ══════════════════════════════════════════════════════════════════════════════
# Helpers — section injection
# ══════════════════════════════════════════════════════════════════════════════

# Replace the named gate section in REVIEWS_FILE with content from a file.
# Section markers match the template in 00_admin/color_team_reviews.md.
inject_section() {
  local section="$1" content_file="$2"
  local start_marker end_marker

  case "$section" in
    pink) start_marker="## Pink Team";  end_marker="## Red Team"   ;;
    red)  start_marker="## Red Team";   end_marker="## Blue Hat"   ;;
    gold) start_marker="## Gold Team";  end_marker=""              ;;
    *)    die "inject_section: unknown section '$section'" ;;
  esac

  local start_line
  start_line="$(grep -n "^${start_marker}" "$REVIEWS_FILE" | head -1 | cut -d: -f1)"
  [ -z "$start_line" ] && die "Start marker '${start_marker}' not found in $(basename "$REVIEWS_FILE")"

  local tmp
  tmp="$(mktemp)"

  if [ -n "$end_marker" ]; then
    local end_line
    end_line="$(grep -n "^${end_marker}" "$REVIEWS_FILE" | head -1 | cut -d: -f1)"
    [ -z "$end_line" ] && die "End marker '${end_marker}' not found in $(basename "$REVIEWS_FILE")"
    {
      head -n "$((start_line - 1))" "$REVIEWS_FILE"
      cat "$content_file"
      printf '\n---\n\n'
      tail -n "+${end_line}" "$REVIEWS_FILE"
    } > "$tmp"
  else
    {
      head -n "$((start_line - 1))" "$REVIEWS_FILE"
      cat "$content_file"
      printf '\n'
    } > "$tmp"
  fi

  mv "$tmp" "$REVIEWS_FILE"
  info "Injected [${section}] section into $(basename "$REVIEWS_FILE")"
}

# ══════════════════════════════════════════════════════════════════════════════
# Helpers — proposal context (lead, etc.)
# ══════════════════════════════════════════════════════════════════════════════

review_lead_name() {
  local n
  n="$(yq e '.contacts.proposal_manager.name // "TBD"' "$CONFIG_FILE" 2>/dev/null)"
  [ -z "$n" ] || [ "$n" = "null" ] && n="TBD"
  echo "$n"
}

# Emit the review-input file list as Claude-readable bullets:
#   "- {label} (volume {id}): {abs_path}"
build_volume_input_list() {
  local out=""
  while IFS='|' read -r folder label vid; do
    [ -z "$folder" ] && continue
    while read -r mdfile; do
      [ -z "$mdfile" ] && continue
      out="${out}- ${label} [${vid}]: ${mdfile}"$'\n'
    done < <(discover_volume_files "$folder")
  done < <(load_active_volumes)
  printf '%s' "$out"
}

# ══════════════════════════════════════════════════════════════════════════════
# Shared prompt fragments
# ══════════════════════════════════════════════════════════════════════════════

yaml_record_format_block() {
  local prefix="$1" gate="$2"
  cat <<YAML_FMT
Each finding MUST be emitted in this exact format — a YAML frontmatter block
followed by a markdown body, separated by blank lines. Records are themselves
separated by blank lines. The script downstream parses these YAML blocks; any
deviation will break gate-ordering enforcement.

---
id: "${prefix}-NN"
gate: "${gate}"
priority: "H"              # H (will cost evaluation points) | M | L
status: "open"
owner: "Proposal Manager"  # or Tech Lead | PM Lead | Pricing Lead
target_docs:
  - "<repo-relative path to the doc(s) the finding implicates>"
dependencies: []
created: "${TODAY}"
locked_at: null
---

**Finding:** [one direct sentence — what is missing, weak, or misaligned. Be specific. No softening.]

**Notes:** [empty at creation time; the proposal manager fills this with verified facts before --remediate]

YAML_FMT
}

# ══════════════════════════════════════════════════════════════════════════════
# PINK TEAM
# ══════════════════════════════════════════════════════════════════════════════

run_pink_team() {
  header "Pink Team — Storyboard / Outline Review"
  $DRY_RUN || check_addendum_freshness

  local shred_file
  shred_file="$(find_latest_shred)"

  [ -f "$WIN_THEMES_FILE" ] || die "Required input missing: $(basename "$WIN_THEMES_FILE")"
  [ -n "$shred_file" ]      || die "Required input missing: 00_admin/rfp_shred*.md"
  [ -f "$COMPLIANCE_FILE" ] || die "Required input missing: compliance_matrix.md"

  local volume_inputs
  volume_inputs="$(build_volume_input_list)"
  if [ -z "$volume_inputs" ]; then
    warn "No active volume .md files discovered. Pink Team will run with admin inputs only."
  fi

  local lead; lead="$(review_lead_name)"
  local PROMPT
  PROMPT=$(cat <<ENDPROMPT
You are performing a Pink Team (Storyboard / Outline Review) of an A/E proposal.

Pink Team scope: evaluate STRATEGY and STRUCTURE — not prose quality. Focus on
win theme visibility, compliance coverage, section structure, proof point
availability, and narrative direction. Do NOT rewrite prose.

---

## Inputs

Read each file in full before reviewing:

- Win Themes & Hot Buttons: ${WIN_THEMES_FILE}
- RFP Shred (Evaluation Criteria): ${shred_file}
- Compliance Matrix: ${COMPLIANCE_FILE}
$([ -f "$SELECTOR_FILE" ] && echo "- Project Selector: ${SELECTOR_FILE}")

Active proposal volumes (each .md is a section the review covers):
${volume_inputs}

---

## Review Instructions

For each finding:
- Sequential ID: PT-01, PT-02, ...
- Determine the target_docs path from the volumes list above (use repo-
  relative paths starting with the volume folder name).
- Priority: H = will cost evaluation points if not fixed before Red Team;
            M = should fix before Red Team; L = improve if time allows.
- Owner: Proposal Manager | Tech Lead | PM Lead | Pricing Lead.

Cover all of these review dimensions:

1. Win theme ghosting — for every win theme in win_themes.md, identify the
   specific section where it should appear. Unassigned themes are H findings.
2. Feature → Benefit → Proof structure — flag every discriminator that stops
   at Feature without translating to a client Benefit, or lacks a named proof.
3. Proof point gaps — win themes missing concrete examples or data.
4. Evaluation criterion coverage — does the draft touch every evaluation
   criterion in the shred?
5. Section structure — any volume undersized, missing, or out of place?
6. Discriminator strength — are differentiators surfaced with customer
   benefit framing, not just stated as facts?
7. Known data gaps — flag every unresolved [VERIFY] item.
8. Compliance matrix — unchecked requirements without an assigned section.

Aim for 8–15 findings. Do not pad; do not soften.

---

## Output Format

$(yaml_record_format_block "PT" "pink")

After the last finding record, output exactly one line:

**Overall Assessment:** [Pass | Conditional Pass | Fail] — [one sentence]

Output ONLY the section header below, the metadata, the \`### Findings\`
heading, the YAML records, then the Overall Assessment. Nothing else, no
preamble or trailing commentary.

## Pink Team — Storyboard / Outline Review

**Date:** ${TODAY}
**Review Lead:** ${lead}
**Reviewers:** Claude Code (AI-assisted internal review)
**Focus:** Are win themes visible? Is the compliance matrix addressed? Are sections structured correctly?

### Findings

[YAML frontmatter records here, one per finding, blank line between records]

**Overall Assessment:** [verdict + one sentence]
ENDPROMPT
)

  local TMP_OUT
  TMP_OUT="$(mktemp)"
  trap 'rm -f "$TMP_OUT"' EXIT

  info "Calling Claude for Pink Team review (30–60 seconds)..."
  claude --print -p "$PROMPT" > "$TMP_OUT"
  success "Claude response received ($(wc -l < "$TMP_OUT") lines)"

  if $DRY_RUN; then
    header "Dry Run — Pink Team output (not written)"
    cat "$TMP_OUT"
  else
    inject_section "pink" "$TMP_OUT"
    success "color_team_reviews.md updated — Pink Team section"
    echo ""
    echo "${BOLD}Next steps:${RESET}"
    echo "  1. Review findings in $(realpath --relative-to="$REPO_ROOT" "$REVIEWS_FILE")"
    echo "  2. Resolve all H-priority findings before Red Team"
    echo "  3. Triage with: bash scripts/review/review_triage.sh --list"
  fi
}

# ══════════════════════════════════════════════════════════════════════════════
# RED TEAM
# ══════════════════════════════════════════════════════════════════════════════

run_red_team() {
  header "Red Team — Full Draft Review"
  $DRY_RUN || check_addendum_freshness
  $DRY_RUN || check_prior_gate "PT" "Pink Team"

  local shred_file
  shred_file="$(find_latest_shred)"

  [ -f "$WIN_THEMES_FILE" ] || die "Required input missing: $(basename "$WIN_THEMES_FILE")"
  [ -n "$shred_file" ]      || die "Required input missing: 00_admin/rfp_shred*.md"
  [ -f "$COMPLIANCE_FILE" ] || die "Required input missing: compliance_matrix.md"

  local volume_inputs
  volume_inputs="$(build_volume_input_list)"

  local lead; lead="$(review_lead_name)"
  local PROMPT
  PROMPT=$(cat <<ENDPROMPT
You are performing a Red Team (Full Draft Review) of an A/E proposal. Role-
play as an evaluator scoring this proposal against the published criteria,
as if you have never met the offeror and are evaluating 10 submissions in
a single day.

---

## Inputs

Read each file in full before reviewing:

- Win Themes & Hot Buttons: ${WIN_THEMES_FILE}
- RFP Shred (full evaluation criteria): ${shred_file}
- Compliance Matrix: ${COMPLIANCE_FILE}
$([ -f "$SELECTOR_FILE" ] && echo "- Project Selector: ${SELECTOR_FILE}")

Active proposal volumes (the prose under evaluation):
${volume_inputs}

---

## Review Instructions

**Part 1 — Three Evaluator Questions (Shipley)**
1. Can they do the work? (Technical capability — demonstrated, not just claimed?)
2. Will they do what they say? (Past performance and management credibility?)
3. Is it worth the price? (Value proposition vs. competitors?)
Answer each with one sentence + confidence (High / Medium / Low).

**Part 2 — Evaluator Scoring**
Score each evaluation factor adversarially. Evaluators look for reasons to
score DOWN. Use the rubric: Outstanding / Good / Acceptable / Marginal /
Unacceptable. Note the gap between current score and Outstanding for each.

**Part 3 — Findings (the structured records below)**
Cover:
a) FBI structure violations — claims that are Feature without Benefit or Proof.
b) Me-too statements — sentences a competitor could copy verbatim.
c) Proof point gaps — claims without named projects, data, or credentials.
d) Open [VERIFY] items.
e) Unanswered evaluator questions.

Aim for 10–20 findings. Be specific about location (volume + section + sentence).

**Part 4 — Overall Assessment**
Pass / Conditional Pass / Fail with a one-paragraph explanation including
win-probability estimate, biggest single gap, and one action that would most
improve the score.

---

## Output Format

Output exactly the structure below. Nothing before or after.

## Red Team — Full Draft Review

**Date:** ${TODAY}
**Review Lead:** ${lead}
**Reviewers:** Claude Code (AI-assisted evaluator simulation)
**Focus:** Evaluator-perspective scoring. Does every evaluation criterion have a compelling response?

### Three Evaluator Questions

| Question | Answer | Confidence |
|---|---|---|
| Can they do the work? | [one sentence] | High / Medium / Low |
| Will they do what they say? | [one sentence] | High / Medium / Low |
| Is it worth the price? | [one sentence] | High / Medium / Low |

### Scoring (mirror the published evaluation criteria)

| Evaluation Factor | Evaluator Score | Our Target | Gap |
|---|---|---|---|
[one row per evaluation criterion in the shred — keep target as Outstanding]

### Findings

$(yaml_record_format_block "RT" "red")

**Overall Assessment:** [Pass | Conditional Pass | Fail] — [one paragraph]
ENDPROMPT
)

  local TMP_OUT
  TMP_OUT="$(mktemp)"
  trap 'rm -f "$TMP_OUT"' EXIT

  info "Calling Claude for Red Team review (60–120 seconds)..."
  claude --print -p "$PROMPT" > "$TMP_OUT"
  success "Claude response received ($(wc -l < "$TMP_OUT") lines)"

  if $DRY_RUN; then
    header "Dry Run — Red Team output (not written)"
    cat "$TMP_OUT"
  else
    inject_section "red" "$TMP_OUT"
    success "color_team_reviews.md updated — Red Team section"
    echo ""
    echo "${BOLD}Next steps:${RESET}"
    echo "  1. Review scoring table; address every criterion below Outstanding"
    echo "  2. Resolve all H-priority RT findings before Gold Team"
    echo "  3. Triage with: bash scripts/review/review_triage.sh --list --priority H"
  fi
}

# ══════════════════════════════════════════════════════════════════════════════
# GOLD TEAM
# ══════════════════════════════════════════════════════════════════════════════

run_gold_team() {
  header "Gold Team — Final Approval"
  $DRY_RUN || check_addendum_freshness
  $DRY_RUN || check_prior_gate "PT" "Pink Team"
  $DRY_RUN || check_prior_gate "RT" "Red Team"

  local shred_file
  shred_file="$(find_latest_shred)"

  [ -f "$COMPLIANCE_FILE" ] || die "Required input missing: compliance_matrix.md"
  [ -n "$shred_file" ]      || die "Required input missing: 00_admin/rfp_shred*.md"

  local lead; lead="$(review_lead_name)"
  local PROMPT
  PROMPT=$(cat <<ENDPROMPT
You are performing a Gold Team (Final Approval) review of an A/E proposal
prior to submission. This is the last gate. Verify production readiness,
compliance completeness, and submission logistics. Be brief and decisive.

---

## Inputs

- Compliance Matrix: ${COMPLIANCE_FILE}
- RFP Format Requirements (shred): ${shred_file}
- Prior Color Team Findings: ${REVIEWS_FILE}

---

## Review Instructions

**Part 1 — Final Executive Questions**
1. Is the submission fully compliant?
2. Is our pricing competitive?
3. Will we win? (final P(win) estimate — honest, not optimistic)

**Part 2 — Final Checklist**
Evaluate each item: ✅ confirmed / ⚠ needs verification / ❌ not complete.
Add items missing from the list based on RFP requirements.

**Part 3 — Findings (blockers only)**
Generate findings only for non-compliance risks, submission logistics gaps,
or pricing/positioning problems that could cost the award. Do not generate
findings for items that can wait until after submission.

---

## Output Format

Output exactly the structure below. Nothing before or after.

## Gold Team — Final Approval

**Date:** ${TODAY}
**Approver:** ${lead}
**Reviewers:** Claude Code (AI-assisted compliance check)
**Focus:** Price competitiveness, risk, final messaging, compliance with all format requirements.

### Executive Questions

| Question | Answer | Status |
|---|---|---|
| Is the submission fully compliant? | [one sentence] | ✅ / ⚠ / ❌ |
| Is our pricing competitive? | [one sentence] | ✅ / ⚠ / ❌ |
| Will we win? (P(win) estimate) | [one sentence] | ✅ / ⚠ / ❌ |

### Final Checklist

- [ ] All Pink Team findings resolved or risk-accepted
- [ ] All Red Team findings resolved or risk-accepted
- [ ] Blue Hat / Black Hat findings reviewed
- [ ] Compliance matrix 100% addressed
- [ ] Page limits verified for all volumes
- [ ] File naming / submission format confirmed
- [ ] Executive Sponsor sign-off obtained
- [ ] Submission logistics confirmed
- [ ] Addendum pre-flight clean (latest addendum reflected in rfp_shred)
[add additional checklist items derived from the RFP]

### Findings

$(yaml_record_format_block "GT" "gold")

**Decision:** ☐ APPROVED TO SUBMIT &nbsp;&nbsp; ☐ CONDITIONAL (see below)

**Conditions:** [list any conditions, or "None" if clean]
ENDPROMPT
)

  local TMP_OUT
  TMP_OUT="$(mktemp)"
  trap 'rm -f "$TMP_OUT"' EXIT

  info "Calling Claude for Gold Team review (30–60 seconds)..."
  claude --print -p "$PROMPT" > "$TMP_OUT"
  success "Claude response received ($(wc -l < "$TMP_OUT") lines)"

  if $DRY_RUN; then
    header "Dry Run — Gold Team output (not written)"
    cat "$TMP_OUT"
  else
    inject_section "gold" "$TMP_OUT"
    success "color_team_reviews.md updated — Gold Team section"
    echo ""
    echo "${BOLD}Next steps:${RESET}"
    echo "  1. Resolve every H-priority finding before production"
    echo "  2. Get Executive Sponsor sign-off"
    echo "  3. Run scripts/publish/sanity_check.py before final submission"
  fi
}

# ══════════════════════════════════════════════════════════════════════════════
# Dispatch
# ══════════════════════════════════════════════════════════════════════════════

case "$MODE" in
  pink) run_pink_team ;;
  red)  run_red_team  ;;
  gold) run_gold_team ;;
esac
