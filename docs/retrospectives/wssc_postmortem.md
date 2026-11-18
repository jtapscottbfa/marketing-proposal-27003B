# Post-Mortem: WSSC RFP 98586 — Small A&E Projects Term Contract

**Proposal Submitted:** 2026-03-31  
**Post-Mortem Date:** 2026-04-02  
**Author:** jtapscottbfa  
**Purpose:** Identify actionable improvements to the BFA proposal template — not to evaluate proposal quality.

---

> **Inputs used in this analysis:**
> - `z:\marketing-proposal-26015\retrospectives\brain_dump_wssc.md` — 6 practitioner observations
> - `z:\marketing-proposal-26015\00_admin\rfp_shred.md` — fully populated WSSC shred
> - `z:\marketing-proposal-26015\00_admin\template_optimization_notes.md` — 12 self-documented improvements
> - `z:\marketing-proposal-26015\00_admin\pre_submission_gaps.md` — submission-day risk tracker
> - `z:\marketing-proposal-26015\00_admin\proposal_schedule.md`, `compliance_matrix.md`, `bid_no_bid.md`, `win_themes.md` — all blank
> - `z:\marketing-proposal-26015\_output\BFA_98586_Technical_Proposal_20260331.pdf` — delivered 62-page document
> - Template baseline files in `z:\template-marketing-proposal-public\`

---

## Category 1 — Repeatable Template Gaps

Findings validated against the actual template files and delivered document. Each entry names the exact template file or folder that needs to change.

---

### GAP-01: No A&E Term Contract Preset YAML

**Evidence:** `scripts/scaffold/proposal_types/` contains `sled_full`, `sled_qualifications`, `hed_research`, and `design_build` presets. None maps to a tab-structured QBS/qualifications-based selection. The WSSC proposal required renaming all five Shipley-volume folders to RFP-tab-aligned names (`01_cover_letter/`, `02_tab1_technical_approach/`, etc.) — done manually under time pressure.

**Template action:** Add `ae_term_contract.yml` to `scripts/scaffold/proposal_types/` with section IDs `cover_letter`, `tab_technical_approach`, `tab_firms_experience`, `tab_key_personnel`, `price`. Register it in `new_proposal.sh`. This preset should be the default starting point for any SLED/HED A&E term contract pursuit.

---

### GAP-02: No Artifact Folder Scaffold (`06_attachments/`)

**Evidence:** The WSSC proposal developed a two-layer build: narrative `.md` files compiled via Pandoc, and external PDFs (project sheets, resumes, signed forms, COI, licenses) assembled separately. The template has no scaffold for this layer. The WSSC repo organic structure ended up as:

```text
06_attachments/
  project_sheets/
    _source_artifacts/      ← raw BOD/source docs per project, each with INTAKE.md
    ps_01_bfa_project.md    ← rendered 1-pager markdown files
  resumes/                  ← 15 individual per-person .md files
  forms_tab4/               ← 5 signed WSSC PDF forms
  forms_tab5/               ← 3 OSDI PDF forms
  coi/                      ← certificate of insurance
  licenses/                 ← firm license documentation
```

**Template action:** Add `06_attachments/` with these subfolders to the scaffold in `new_proposal.sh`. Include a `README.md` in each explaining the content type and noting that these folders are excluded from the Pandoc build. Promote the two-layer build approach (narrative + artifact assembly) in `readme.md`.

---

### GAP-03: No Subconsultant Intake Structure

**Evidence:** The WSSC team had 8 subconsultants. Their artifacts (firm bios, resumes, rate sheets, certifications, licenses — 30+ files) were loaded into `00_admin/subconsultant_intake/` ad hoc with no template guidance. Brain dump item 1 notes this directly: "I ended up just dumping all subconsultant artifacts...into 00_admin."

**Template action:** Add `00_admin/subconsultant_intake/` to the scaffold with a `subconsultant_digest.md` starter (columns: Firm, Role, POC, Key Staff, Certs, Files Received, Status). Add a `README.md` with intake instructions. Include the folder in `new_proposal.sh` for any preset that involves teaming.

---

### GAP-04: `rfp_shred.md` Missing Addendum Change Log Section

**Evidence:** The WSSC RFP went through at least 3 addenda. A material change between Addendum 1 and Addendum 3 moved team resumes outside the 75-page count, expanding the page budget. The WSSC shred captured this in a hand-added `## Addendum Change Log` table. The template `00_admin/rfp_shred.md` has no such section.

**Template action:** Add `## Addendum Change Log` as the final section of `00_admin/rfp_shred.md` with an empty table: `| Addendum # | Date | Section Affected | Change Summary | Impact on Proposal |`.

---

### GAP-05: `rfp_shred.md` Missing Source/Addendum Header Field

**Evidence:** The template `rfp_shred.md` header block has no field identifying which addendum the shred reflects. On a multi-addendum RFP, a stale shred (reflecting Addendum 1 when Addendum 3 is current) is a compliance risk.

**Template action:** Add `> **Source:** [Addendum # and revision — update this line every time the shred is refreshed]` to the header block in `00_admin/rfp_shred.md`.

---

### GAP-06: `rfp_shred.md` Missing Pass/Fail Minimum Qualifications Section

**Evidence:** The WSSC RFP had two pass/fail minimum qualifications (PM Maryland PE/AIA license + domicile, and MDE Stormwater/ESC permit experience). These are disqualifiers, not scored criteria. The template shred has Section L and Section M tables but no dedicated pass/fail section. The WSSC shred added a `## MINIMUM QUALIFICATIONS (Pass/Fail)` section between Key Facts and Section L — this is the correct location.

**Template action:** Add a `## Minimum Qualifications (Pass/Fail)` section to `00_admin/rfp_shred.md` between the Key Facts block and Section L. Include a table: `| Requirement | Source | Status |`. Instruct users to complete this before scoring the bid/no-bid.

---

### GAP-07: `rfp_shred.md` Missing "Key Facts at a Glance" Block

**Evidence:** The WSSC shred opened with a dense quick-reference block covering client, contract value, page limits, submission portal, due date, and evaluation structure at a glance. The template shred has no equivalent. This block proved useful during the proposal.

**Template action:** Add a `## Key Facts at a Glance` block to `00_admin/rfp_shred.md` immediately after the header. Fields: Client, Procurement Number, Contract Type, Contract Value, Due Date, Submission Portal/Method, Page Limit, Evaluation Structure, MBE/DBE/SBE Goal.

---

### GAP-08: No `pre_submission_gaps.md` Template

**Evidence:** `z:\marketing-proposal-26015\00_admin\pre_submission_gaps.md` was created organically during the final 48 hours of the WSSC proposal. It provides a tiered risk-tracking structure (Tier 1 Non-Responsive Risk → Tier 5 Remaining Narrative Placeholders) with a 10-step Submission Day Sequence. This document does not exist in the template repo. It was critical enough that its absence in earlier proposals likely represents untracked risk.

**Template action:** Add `00_admin/pre_submission_gaps.md` to the template with the tiered structure (Tier 1–5) and submission sequence checklist. Wire it into the Shipley gate schedule at the Gold Team / Final Review milestone.

---

### GAP-09: No `mbe_tracker.md` Template

**Evidence:** The WSSC 32% OSDI goal used tiered credit percentages (AA/WBE = 100%, Asian American = 18%, Hispanic = 7%, Native = 1%). Tracking this in a plain checklist is error-prone. No dedicated tracker exists in the template.

**Template action:** Add `00_admin/mbe_tracker.md` to the template with a table: `| Firm | Cert Type | Credit % | Scope | Est. $ | Est. % of Contract | Verified? |`. Include calculation instructions. Reference it from `compliance_matrix.md` for proposals with MBE/DBE/SBE goals.

---

### GAP-10: `highlight_placeholders.py` Missing from Template

**Evidence:** `scripts/publish/highlight_placeholders.py` exists in the WSSC proposal repo but not in the template. Brain dump item 2 notes placeholder highlighting was "very helpful." The pre-commit hook catches PLACEHOLDERs in source `.md` files, but the highlight script targets rendered documents (`.docx`) — a different point in the pipeline and a different audience (reviewers, not committers).

**Template action:** Copy `highlight_placeholders.py` from the WSSC proposal repo into `scripts/publish/` in the master template. Document its use in `readme.md` and reference it from the Gold Team review step in `proposal_schedule.md`.

---

### GAP-11: `proposal_intake.sh` Missing from Template

**Evidence:** `scripts/scaffold/proposal_intake.sh` was created during the WSSC proposal to run a guided offline questionnaire (evaluation factors, win themes, team gaps, MBE/SLBE, red flags) when Claude is not available. It does not exist in the template repo.

**Template action:** Add `proposal_intake.sh` to `scripts/scaffold/` in the master template. Consider wiring it into `new_proposal.sh` as an optional Phase 5 (post-scaffold intake). Document in `readme.md`.

---

### GAP-12: `compliance_matrix.md` Uses Hardcoded Volume Labels

**Evidence:** The template `compliance_matrix.md` uses "Vol I / Vol II / Vol III" labels throughout. For tab-structured RFPs, these labels are incorrect and require manual find-and-replace. On the WSSC proposal, the compliance matrix was never updated (see Category 3 below), in part because the mismatch added friction.

**Template action:** Update `compliance_matrix.md` to use a configurable `[TAB/VOLUME]` label pattern, or add a prominent header note: "Update volume/tab labels to match RFP structure before populating." Consider adding a `location_label` field to `proposal_config.yml.example` that drives this label.

---

### GAP-13: Pandoc `--number-sections` Causes Double-Numbering

**Evidence:** `build_docx.sh` includes `--number-sections`. When the `reference.docx` styles also include heading numbering, the output produces headings like "1. 1.0 Technical Approach." This was discovered and removed during the WSSC build.

**Template action:** Remove `--number-sections` from the master `build_docx.sh`. Add a comment: "Do not add --number-sections — heading numbering is controlled by reference.docx styles only."

---

### GAP-14: Section Starters Hardcode Heading Numbers

**Evidence:** Section template starters (e.g., `pricing_narrative.md`) contain `## 1.0 Introduction`, `### 2.1 Approach` style prefixes. These conflict with reference.docx auto-numbering styles and were stripped during the WSSC build.

**Template action:** Audit all section starter `.md` files in the template and remove `X.X` numeric prefixes from headings. Add a note to volume `README.md` files: "Do not number headings manually — use plain heading text and let reference.docx styles handle numbering."

---

### GAP-15: CI Pipeline Missing `npm ci` Before Build Step

**Evidence:** `post_process_tables.js` depends on `adm-zip` and `@xmldom/xmldom`. Without `npm ci` in the CI job, these packages are absent in the runner and the table post-processing step fails silently. This was added to the WSSC `proposal_ci.yml` but not back-ported to the template.

**Template action:** Add `npm ci` step before `bash scripts/publish/build_docx.sh` in the Docx Build Check job in the master `proposal_ci.yml`. Add an inline comment explaining the dependency.

---

### GAP-16: CI PLACEHOLDER Audit Uses Hardcoded Folder Names

**Evidence:** The PLACEHOLDER audit in `proposal_ci.yml` explicitly lists folder paths (`01_cover_letter/`, `02_tab1_technical_approach/`, etc.). When folder names change to match RFP tab labels, this list goes stale silently. This was discovered during the WSSC build.

**Template action:** Replace the hardcoded folder list in the PLACEHOLDER audit `grep` command with the glob `0[1-5]_*/`. This makes the audit folder-name-agnostic and compatible with any preset.

---

### GAP-17: PDF Bookmarking Not Addressed in Build Documentation

**Evidence:** WSSC REQ-007 required a bookmarked PDF for submission. No mention of PDF bookmarking exists in `readme.md` or any build script. This was handled outside the template pipeline.

**Template action:** Add a note in `readme.md` under the build pipeline section: "For submissions requiring bookmarked PDFs, add `--pdf-engine-opt=--outline` to the Pandoc flags, or post-process the PDF with a tool that adds bookmarks from heading structure. Verify the submission portal accepts the output before deadline."

---

## Category 2 — WSSC-Specific One-Offs

Findings specific to this pursuit that do not warrant template changes. Documented here for the project record.

---

### ONE-OFF-01: Maryland SDAT Non-Maryland Corporation Qualification

BFA was required to register as a foreign corporation authorized to do business in Maryland. SDAT filing was completed 2026-03-20. This is a Maryland-specific legal/compliance requirement triggered by the client's state, not a proposal process gap.

---

### ONE-OFF-02: OpenGov Portal Vendor Questionnaire

WSSC used OpenGov for submission. The portal required completion of a vendor questionnaire (Q1–Q8, Q12.1–12.4) separate from the document upload. This is WSSC-portal-specific and not generalizable to the template.

---

### ONE-OFF-03: WSSC OSDI Weighted Credit Tiers

The 32% OSDI goal used WSSC-specific credit percentages: AA/WBE = 100%, Asian American = 18%, Hispanic = 7%, Native American = 1%. These weights are unique to WSSC's OSDI program and should not be hardcoded into the template `mbe_tracker.md`. The tracker should be structured to accept any credit percentage per firm (see GAP-09).

---

### ONE-OFF-04: Tab 4 WSSC Affidavit Package

Tab 4 required 5 WSSC-specific signed forms (Affidavit of Non-Collusion, MBE/DBE forms, etc.). The form set is unique to WSSC and not generalizable. The `06_attachments/forms_tab4/` folder structure (see GAP-02) is the generalizable lesson.

---

### ONE-OFF-05: Tab 5 OSDI Forms and Dual-Signature Requirement

Tab 5 OSDI documentation required 3 WSSC-specific forms with a 2-signature requirement (principal and OSDI firm). This is WSSC-program-specific. Folder structure is the generalizable lesson.

---

### ONE-OFF-06: PM Maryland PE/AIA License + Domicile Pass/Fail

The RFP required the designated PM to hold a Maryland PE or AIA license and maintain a Maryland-domicile office. This was a pass/fail disqualifier tied to Maryland's A&E licensure laws — not a template-level concern, though it reinforces GAP-06 (minimum qualifications section in shred).

---

### ONE-OFF-07: MDE Stormwater/ESC Permit Experience Pass/Fail

The RFP required documented experience preparing MDE-compliant stormwater management and erosion/sediment control permits. This is a WSSC environmental compliance requirement, not a generalizable template element.

---

### ONE-OFF-08: Security Clearance for Plan Receipt (REQ-002)

The RFP required team members receiving sensitive plans to hold or be eligible for security clearance. This is a WSSC security program requirement. No template action warranted.

---

## Category 3 — Process Discipline Gaps

Findings where the template provided the right tool but the team did not use it. These are habit and process failures, not template gaps — though some template changes could reduce friction and improve adoption.

---

### DISC-01: `proposal_schedule.md` Never Filled In

**Evidence:** `z:\marketing-proposal-26015\00_admin\proposal_schedule.md` is entirely blank — all 19 milestones remain PLACEHOLDER with unchecked boxes. Brain dump item 6 acknowledges this: "I didn't fully execute the checklists and schedules that were generated at the onset of the project."

**Root cause:** Time crunch combined with no forcing function at the start of the project.

**Recommendation:** Wire `proposal_schedule.md` population into the Phase 1 kickoff checklist in `new_proposal.sh` output. Consider adding a CI check: if `proposal_schedule.md` contains more than N PLACEHOLDERs after day 2, emit a warning. The schedule should be dated on the same day the scaffold is created, while RFP dates are fresh.

---

### DISC-02: `compliance_matrix.md` Never Populated

**Evidence:** `z:\marketing-proposal-26015\compliance_matrix.md` is entirely blank — all rows remain PLACEHOLDER. The rfp_shred.md was used as the de-facto compliance tracker instead.

**Root cause:** The shred and compliance matrix serve overlapping purposes. The shred captures requirements; the matrix tracks where they are addressed in the proposal. When the shred is rich and the matrix is blank, compliance tracking is implicit rather than explicit.

**Recommendation:** Either (a) consolidate: add a `Location in Proposal` and `Compliant?` column to the rfp_shred.md Section L table so the shred doubles as the compliance matrix, or (b) enforce separation: update `compliance_matrix.md` instructions to direct the user to copy REQ IDs directly from rfp_shred.md rather than re-deriving them. Option (a) reduces document count and friction; option (b) preserves Shipley separation of concerns. Choose one and document the decision in `readme.md`.

---

### DISC-03: `bid_no_bid.md` Never Filled In

**Evidence:** `z:\marketing-proposal-26015\00_admin\bid_no_bid.md` is entirely blank. A bid decision was made, but it was not formally documented.

**Root cause:** The decision was obvious (pursue), so the form felt like overhead.

**Recommendation:** Reduce the bid/no-bid form to the minimum viable prompt for non-obvious decisions, and gate the scaffold: `new_proposal.sh` should prompt for a brief bid rationale string and pre-populate `bid_no_bid.md` with it before any other files are created. A one-line rationale is better than a blank form.

---

### DISC-04: `win_themes.md` Never Populated — Themes Scattered into `rfp_shred.md`

**Evidence:** `z:\marketing-proposal-26015\00_admin\win_themes.md` is entirely blank. Win themes were captured in a table within `rfp_shred.md` instead.

**Root cause:** The rfp_shred.md workflow naturally surfaces win themes during requirement analysis. Copying them to a separate file felt redundant under time pressure.

**Recommendation:** Move the win themes table from `win_themes.md` into `rfp_shred.md` as `## Win Themes` section, positioned after the evaluation factors. Remove `win_themes.md` as a standalone file. Consolidating adjacent content reduces the number of documents to maintain and mirrors how the WSSC work actually happened.

---

### DISC-05: Two Unresolved PLACEHOLDERs in Final Delivered PDF

**Evidence:** The submitted `BFA_98586_Technical_Proposal_20260331.pdf` contains two unresolved blocks:

1. **Section 2.6, p. 20:** `[PLACEHOLDER — confirm MBE/DBE/SBE/SDVOB certification status and certificate numbers for BFA, ECS, BW, Mead Hunt, Exton, MHM, Rummel]`
2. **Section 3.4.5, p. 37:** `[NUMBER] active assignments` — unfilled capacity letter placeholder

The pre-commit hook was designed to catch PLACEHOLDERs before commit. Either the final submission was assembled from the output folder without a clean commit, or the hook was bypassed. The `pre_submission_gaps.md` file flagged both items in Tier 5, but they were not resolved before submission.

**Root cause:** The pre-commit PLACEHOLDER hook guards against committing placeholder text to the repo but does not audit the rendered PDF. Once the document exits the Pandoc pipeline to the output folder, it is outside the hook's scope. There was also no independent final-PDF QC step.

**Recommendation:** Add a mandatory final-PDF audit step to `pre_submission_gaps.md` (Tier 1) and `proposal_schedule.md`: "Before upload, run `pdfgrep -n 'PLACEHOLDER\|\[NUMBER\]\|\[TBD\]' _output/*.pdf` and confirm zero results." Consider adding a `check_output_pdf.sh` script to `scripts/publish/` that wraps this command. This step must be human-executed (not CI) since it runs against the final assembled PDF.

---

### DISC-06: Reference Proposal Digestion Imports Stale/Irrelevant Content

**Evidence:** Brain dump item 4: "When analyzing the previous proposal example documents to assist with narrative development, there was information pulled that was not relevant to this proposal, i.e., former staff members, etc. I would like to flag this early during the digestion process."

**Validation status:** Unvalidatable from the delivered PDF (stale content was filtered before final submission). However, the `00_admin/reference_proposals/` folder contained 4 prior proposals and the structure included no guidance on how to use them.

**Recommendation:** Add a `reference_proposals/README.md` to the template scaffold with a "Relevance Filter Checklist" for use when feeding reference proposals into Claude context. Checklist items: (1) confirm staff named are still active at the firm; (2) confirm projects cited are still within the lookback window; (3) confirm fee ranges reflect current market; (4) confirm certification holders are current and still on team; (5) confirm subconsultant relationships are still active. Surface this checklist early — ideally as a Phase 2 step in the proposal schedule.

---

## Summary Action Table

| ID | Category | Template File / Folder | Priority |
| --- | --- | --- | --- |
| GAP-01 | Template Gap | `scripts/scaffold/proposal_types/ae_term_contract.yml` | High |
| GAP-02 | Template Gap | `06_attachments/` scaffold + subfolders | High |
| GAP-03 | Template Gap | `00_admin/subconsultant_intake/` scaffold | High |
| GAP-04 | Template Gap | `00_admin/rfp_shred.md` — Addendum Change Log section | High |
| GAP-05 | Template Gap | `00_admin/rfp_shred.md` — Source/addendum header field | Medium |
| GAP-06 | Template Gap | `00_admin/rfp_shred.md` — Pass/Fail Minimum Qualifications section | High |
| GAP-07 | Template Gap | `00_admin/rfp_shred.md` — Key Facts at a Glance block | Medium |
| GAP-08 | Template Gap | `00_admin/pre_submission_gaps.md` — new template file | High |
| GAP-09 | Template Gap | `00_admin/mbe_tracker.md` — new template file | Medium |
| GAP-10 | Template Gap | `scripts/publish/highlight_placeholders.py` — add to template | Medium |
| GAP-11 | Template Gap | `scripts/scaffold/proposal_intake.sh` — add to template | Medium |
| GAP-12 | Template Gap | `compliance_matrix.md` — configurable volume/tab labels | Medium |
| GAP-13 | Template Gap | `scripts/publish/build_docx.sh` — remove `--number-sections` | High |
| GAP-14 | Template Gap | All section starter `.md` files — strip X.X heading prefixes | Medium |
| GAP-15 | Template Gap | `proposal_ci.yml` — add `npm ci` before build step | High |
| GAP-16 | Template Gap | `proposal_ci.yml` — replace hardcoded folder list with glob | Medium |
| GAP-17 | Template Gap | `readme.md` — add PDF bookmarking guidance | Low |
| ONE-OFF-01 | One-Off | Maryland SDAT foreign corp registration | — |
| ONE-OFF-02 | One-Off | OpenGov portal vendor questionnaire | — |
| ONE-OFF-03 | One-Off | WSSC OSDI weighted credit tiers | — |
| ONE-OFF-04 | One-Off | Tab 4 WSSC affidavit package | — |
| ONE-OFF-05 | One-Off | Tab 5 OSDI forms + dual-signature requirement | — |
| ONE-OFF-06 | One-Off | PM Maryland PE/AIA license + domicile pass/fail | — |
| ONE-OFF-07 | One-Off | MDE Stormwater/ESC permit experience pass/fail | — |
| ONE-OFF-08 | One-Off | Security clearance for plan receipt | — |
| DISC-01 | Process | Populate `proposal_schedule.md` at scaffold creation | High |
| DISC-02 | Process | Consolidate compliance tracking (shred vs. matrix) | High |
| DISC-03 | Process | Reduce `bid_no_bid.md` to minimum viable prompt | Medium |
| DISC-04 | Process | Merge win themes into `rfp_shred.md`, retire `win_themes.md` | Medium |
| DISC-05 | Process | Final-PDF PLACEHOLDER audit before upload | Critical |
| DISC-06 | Process | Reference proposal relevance filter checklist | Medium |
