# Post-Mortem — VT RFP #443882616
**Opportunity:** Term Contract for Professional M&E Engineering Services  
**Submitted:** 2026-04-23 | **Written:** 2026-04-23  
**Author:** J. Tapscott / Claude Code  
**Outcome:** Pending award decision  
**Template version at kickoff:** 2.0

---

## Summary

21-day pursuit from initial scaffold to submitted package. The system handled RFP intake structure,
compliance tracking scaffolding, and review gate document structure. Every other operational
capability — AE form population, package assembly, color team scripting, sanity checking, and
content library — was built from scratch inside the pursuit and run by Claude with no underlying
template code. This report is the source for v2.1 and v3.0 backlog items.

**Score at submission:** 86/86 sanity checks passing. No open H-priority findings. Win probability
estimated 45–55% — structural constraints remain (geographic disadvantage EVAL-003; no delivered
VT or JMU task orders) but no document-level scoring liabilities remain open.

---

## Timeline

| Date | Event |
|---|---|
| 2026-04-02 | RFP released |
| 2026-04-09 | Q&A period closed — BFA did not submit questions (started late) |
| 2026-04-14 | Bid/No-Bid → BID · Kickoff · RFP Shred complete · Compliance matrix draft |
| 2026-04-15 | Proposal outline built |
| 2026-04-16 | Pink Team (storyboard review) |
| 2026-04-20 | Pink Team revisions · Draft AE-6, AE-4, AE-5 · Red Team |
| 2026-04-21 | All RT findings resolved · AE-4 project columns populated · V-8 SWaM corrected |
| 2026-04-22 | Red Team 2 (compiled PDF) · Gold Team · Code fixes (RT2-01–09) · Package recompile |
| 2026-04-23 | Signatures · Final PDF · Sanity check (86/86) · Portal upload · Submitted 13:47 ET |

---

## What Was Built From Scratch During This Pursuit

The following scripts did not exist in the template and were written mid-pursuit:

| Script | Lines | Purpose |
|---|---|---|
| `populate_ae_forms.py` | 1,330 | DGS AE-1 through AE-6 form population |
| `color_team_review.sh` | 583 | Pink/Red/Gold team review orchestration |
| `review_triage.sh` | 418 | Finding remediation workflow |
| `assemble_package.py` | 313 | Submission package assembly |
| `sanity_check.py` | 311 | 86-point pre-submission check |
| `proposal_digest.sh` | 493 | Reference proposal digestion |
| `compile_package.py` | 142 | PDF compile and merge |

The ae1–ae6 directory structure, blank form templates, and all subconsultant intake organization
were also created from scratch. The content library, project selector, and reference proposal
digestion were entirely ad-hoc.

---

## Priority 1 — Quick Wins

Low-effort, self-contained fixes. Most are one-function or one-config changes.

| ID | Item | File/Area | Fix |
|---|---|---|---|
| QW-01 | Comma crashes guided prompts; no go-back option | `new_proposal.sh` | Comma-escape sanitizer on inputs; `[B]ack` branch at each prompt step |
| QW-02 | `bid_no_bid.md` ships blank | `new_proposal.sh` scaffold step | Pre-populate Section 1 from `proposal_config.yml` at scaffold time |
| QW-03 | `rfp_shred.sh` re-prompts for RFP title | `rfp_shred.sh` | Read `proposal_config.yml::rfp_title` at script top; remove interactive prompt |
| QW-04 | `proposal_schedule.md` dates are placeholders | `new_proposal.sh` | Calculate milestone dates from `deadline` in config; write at scaffold time |
| QW-05 | `compliance_matrix.md` not stubbed during shred | `rfp_shred.sh` | Auto-stub one row per extracted requirement post-shred |
| QW-06 | `color_team_reviews.md` not seeded during shred | `rfp_shred.sh` | Write gate headers and findings table skeleton post-shred |
| QW-07 | Em dashes saturate AI-generated narratives | `populate_ae_forms.py` | Add `text.replace('—', '-')` to strip pass; em dashes flag AI authorship |
| QW-08 | Markdown renders as literal syntax in AE-6 cells | `populate_ae_forms.py` | Promote `_strip_markdown()` from one-off fix to template default |
| QW-09 | AE-5 `gross_sf` appends "sf" to N/A entries | `populate_ae_forms.py` | Skip unit suffix when value starts with `N/A` |
| QW-10 | AE-5 `const_end` truncates in column | `populate_ae_forms.py` | Cap at 12 chars; normalize `In Progress` / `Ongoing` variants |
| QW-11 | Internal notes and `[VERIFY]` tags visible in compiled PDF | `populate_ae_forms.py` | Expand `_strip_internal_refs()` patterns: `[VERIFY]`, `[PLACEHOLDER]`, `*End of draft*` |
| QW-12 | Mock RFP and `media-*` temp folders in template | Template root | Delete artifacts; add `media-*/` and mock RFP patterns to `.gitignore` |
| QW-13 | Double numbering in kickoff meeting compilation | `kickoff_meeting.md` | Fix list counter reset; add section separator between agenda items |
| QW-14 | README has no RFP shred instructions | `scripts/scaffold/README.md` | Add "Running the RFP Shred" section with step-by-step and common errors |
| QW-15 | `new_proposal.sh` has no GitHub URL helper | `new_proposal.sh` | Print new repo URL and `git remote set-url` instructions at end of scaffold |
| QW-16 | No addendum check at color team review gates | `color_team_review.sh` | Pre-flight prompt: "Has an addendum been issued since last gate?"; halt if yes |

---

## Priority 2 — Show Stoppers

These are the gaps where the system had no code and Claude had to improvise everything in real
time. Each one added hours of unplanned work and introduced quality risk.

---

### SS-01 — AE Form Population Infrastructure Did Not Exist

The ae1–ae6 directories, blank form templates, and all population logic (`populate_ae_forms.py`,
1,330 lines) were built from scratch inside the pursuit. Population involved hallucination in roles
tables, cell dimension explosion on paste, markdown rendering as literal text in every cell, and a
multi-pass correction cycle that generated RT2 findings RT2-01 through RT2-09.

**Impact:** 2–3 days unplanned. Multiple submission-level defects from this gap.

**Fix:**
- Promote `populate_ae_forms.py` to `scripts/` in template
- Scaffold `ae1/`–`ae6/` with blank forms in `ae_term_contract.yml`
- Typed personnel/project data schema in `proposal_config.yml` so script has clean inputs from day one
- Role validation step catches unlicensed staff (Shur pattern) before population
- Field formatter library: unit suffix suppression, truncation, markdown strip, em dash replacement — one place

---

### SS-02 — Package Assembly Did Not Exist

`assemble_package.py` (313 lines) and `compile_package.py` (142 lines) were written during the
pursuit. No mechanism combined AE form tabs, appendix dividers, and supplementary docs into a
submission package. Bookmark and TOC structure were done by hand on submission day.

**Fix:**
- Promote both scripts to template
- Bookmark scaffolding auto-generated from `_toc.md`
- PDF TOC generation via Python PDF library
- Attachment ordering configurable in `proposal_config.yml`

---

### SS-03 — Color Team Scripting Did Not Exist

`color_team_review.sh` (583 lines) and `review_triage.sh` (418 lines) were built mid-pursuit. The
review process was interactive but lacked reconciliation discipline. When findings were remediated,
downstream reference docs (win_themes, compliance_matrix, project_selector) were not updated
atomically. This caused stale cross-references in RT2 — characterizations corrected in one doc but
not propagated to others.

**Fix:**
- Promote both scripts to template
- `reconcile_finding()` patches all reference docs atomically when a finding is marked resolved
- Add Blue Team (competitive intelligence) and Black Hat (adversarial) gate definitions
- `--dry-run` flag on all gates
- Token-budget mode: lighter model for raw digestion, full evaluator simulation for final gates only

---

### SS-04 — Sanity Check Did Not Exist

`sanity_check.py` (311 lines, 86 checks) was written during the pursuit. Nothing in the scaffold
verified submission readiness.

**Fix:**
- Promote to template with configurable check registry driven by `proposal_config.yml`
- Checks adapt to submission method, file size limit, required forms, required signatures
- Add as CI step in `.github/workflows/proposal_ci.yml`

---

### SS-05 — RFP Shred Misses Attachments; Temp File Breaks Silently

`rfp_shred.sh` processed only the primary RFP text file. Attachments in
`rfp_intake/original_rfp/attachments/` were skipped entirely — including Appendix G (Hokie Stone
Masonry Guide Spec) which was directly relevant to win theme WT-8. The script creates a temp
extraction file then requests permission to copy it, failing silently in some environments.

**Impact:** Win theme WT-8 developed without reading the actual spec. Subconsultant disciplines
missed in initial digest. Shred re-run with manual file copying.

**Fix:**
- Loop over all files in `rfp_intake/original_rfp/` and `rfp_intake/original_rfp/attachments/`
- File-type dispatcher: `.pdf` → Claude file API, `.doc/.docx` → pandoc, `.txt` → direct read
- Flag when a file cannot be read (binary, oversized, corrupt) — do not skip silently
- All extracted text written directly to `rfp_intake/rfp_text.txt` — no intermediate temp file

---

### SS-06 — Subconsultant Intake Not Scaffolded by Discipline

Discipline-specific intake folders had to be created manually. The initial `subconsultant_digest.md`
missed several disciplines. Intake was high-touch and required multiple re-work cycles. Structr's
DSBSD cert and V-8 SWaM corrections were found at Red Team, not at shred.

**Fix:**
- `rfp_shred.sh` identifies probable disciplines and auto-creates `subconsultant_intake/<discipline>/`
  with an intake form template
- Subconsultant intake validation before color team: named contact + DSBSD cert + one project
- `subconsultant_digest.md` pre-populated with discipline rows from shred

---

### SS-07 — Content Library and Project Selector Not Scaffolded

`project_selector.md` and all reference proposal digestion were built from scratch. Project
selection was wrong on first pass. Wrong characterizations (V-8 SWaM, WJCC role, U-7 BFA role)
required mid-pursuit corrections that rippled across win_themes, compliance_matrix, and AE-6 in
parallel. Every narrative was generated from Claude context with no reusable project data.

**Fix:**
- `content_library/projects.csv` (project ID, client, year, fee, SWaM%, key scopes, verified flags)
- `content_library/personnel.csv`, `content_library/firms.csv`
- `project_selector.md` auto-generated from CSV at scaffold filtered to likely eval criteria
- CPARS/PPQ ingest step
- Seed the library from VT pursuit verified data immediately

---

### SS-08 — Proposal Outline Not Built After Shred

No automatic outline generation after shred. Outline was manually assembled. Generic 01–17 section
folders did not match the DGS AE form structure and had to be deleted and replaced entirely.

**Fix:**
- `rfp_shred.sh` final step generates `proposal_outline.md` mapped to the proposal type's section
  structure from `ae_term_contract.yml`
- AE term contract type scaffolds `ae1/`–`ae6/` + `price_volume/` + `appendices/`, not 01–17 folders

---

### SS-09 — Org Chart Generation Has No Tooling

No tooling for org chart generation. Manual Visio dependency. AE-2 was excluded by Addendum 1 in
VT but will be required in other pursuits.

**Fix:**
- Script generates org chart as SVG/PNG from `proposal_config.yml` team roster
- Graphviz or Mermaid (zero install dependency)
- Output importable to AE-2 or package PDF directly

---

### SS-10 — Go/No-Go Module Does Not Exist

`bid_no_bid.md` is reactive — it captures a decision after someone already decided to look at the
RFP. No firm-level pipeline screen filters opportunities before pursuit resources are allocated. No
institutional scoring history to compare across pursuits.

**Fix:**
- Go/No-Go module in `new_proposal.sh` runs before scaffolding
- Weighted score against firm profile criteria stored in `~/.bfa/firm_profile.yml`
- Recommend Bid / Conditional / Pass
- Log each decision to a pursuit history file for trend analysis

---

## Priority 3 — Process and Quality Issues

| ID | Item | Note |
|---|---|---|
| P3-01 | win_themes / compliance_matrix / project_selector drift during revisions | Reconciliation function or single source of truth propagated to all derived docs |
| P3-02 | Color team reviews are high-token | --fast mode with lighter model for digestion; full simulation for final gates only |
| P3-03 | DGS workbook roles table has hallucination risk | Roles driven from typed data in proposal_config.yml only; no inference |
| P3-04 | Reference proposal digestion is high-touch | Structured project_digest.md with explicit [VERIFY] flags; not narrative summaries |
| P3-05 | Addendum tracking not wired to compliance matrix | Addendum watcher flags affected matrix rows; pre-flight check at each gate |
| P3-06 | 00_admin is disorganized | Canonical paths in proposal_config.yml; scripts reference config paths not hardcoded |
| P3-07 | SF330 scaffolding missing entirely | sf330.yml proposal type; SF330 Part 1 A-F and Part 2 form population scripted |
| P3-08 | CPARS/PPQ not ingested | Ingest script reads CPARS reports; writes to content_library/past_performance.csv |
| P3-09 | Second-pass color team reconciliation fragile | review_triage.sh tracks which reference docs each finding touches; second-pass pre-flight confirms none stale |
| P3-10 | Internal reference cleanup before publish not systematic | _strip_internal_refs() applied to all output documents before compile, not just AE-6 |

---

## Key Decisions Made During Pursuit

| Decision | Rationale | Outcome |
|---|---|---|
| No sub AE-4 forms submitted | Addendum 1 RFI #5 confirmed VT prefers project-by-project team selection | Correct; removed compliance risk |
| TCI replaced by BFA in-house (2026-04-22) | TCI withdrew; OSP/ISP/telecom/security handled by BFA | Clean removal; no scoring impact |
| WJCC removed entirely | Confirmed BFA is not a client; all WJCC references removed | Eliminated false credential risk |
| V-8 SWaM corrected (SDVOSB → Virginia DSBSD) | McPherson/HEA/GER all confirmed DSBSD-certified | Prevented evaluator credibility discount |
| Shur PE situation disclosed | 63-year Soviet-trained engineer; Williams holds stamp | Framed as strength; transparent |
| AARB gap acknowledged directly | BFA has no AARB project history; honest step-by-step workflow substituted | Evaluator trust over overreach |
| JMU relocated from EVAL-008 to EVAL-004 | Zero task orders issued; credential-only argument weaker in technical section | Reduced evaluator skepticism |

---

## Content Library Seed Data (VT Pursuit — Verified)

The following project data was verified during this pursuit and should be seeded into the content
library immediately. All [VERIFY] flags resolved as of 2026-04-22.

| Project ID | Client | Scope | Fee Range | SWaM% | CPARS | Notes |
|---|---|---|---|---|---|---|
| S-1 | CPS / Rena B. Wright | HVAC replacement, occupied K-12 | — | 98% confirmed | — | SOO authored by BFA; billing records confirm SWaM |
| S-2 | West Point Readiness Center | LCC MEP, CPSM App I applied | — | — | — | SOO authored; DCSM-class compliance |
| N-1 | NH-95 Substations A–L | Electrical infrastructure, $35.7M | — | 99% | Very Good | 12 substations, 30–40 yr infrastructure |
| N-8 | NMCP Replace Boiler 108 | Mechanical replacement, occupied hospital | — | 100% (BFA self-perform) | Exceptional | Ref: William Shirk (757) 395-8258 |
| V-8 | McGuire VAMC Generator | Campus-wide generator capacity | — | 100% | — | 32% under program budget; McPherson/HEA/GER |
| V-12 | Perry Point VAMC 364A RRTP | RRTP renovation, VA TIL LCCA deliverable | $2.65M est / $2.3M bid | — | — | LCCA confirmed formal deliverable |
| V-88 | NSA Norfolk Bldg V-88 | MEP renovation, 1917 historic building, SHPO review | — | — | — | SHPO workflow analog for AARB |

**Personnel verified:**
- Richard H. Williams Jr., PE #402048025 (Virginia) — Principal-in-Charge / Electrical EOR
- Kevin O'Grady, PE, CEM — Senior Mechanical EOR; 40-yr NAVFAC career; SOO author
- Boris Shur — Senior Electrical Engineer (63 yrs); works under Williams PE of record
- Mario Peralta — VT Project Manager designation
- Erika Osbourne — Backup PM; NAVFAC/VA IDIQ task order PM experience
- Nolan Huber — Mechanical Engineer
- Keith O'Berry — Plumbing Designer

**References confirmed:**
- William Shirk, NAVFAC Mid-Atlantic: (757) 395-8258, william.h.shirk3.civ@us.navy.mil — N-8 Exceptional CPARS
- James Chadwell, NAVFAC Mid-Atlantic: james.e.chadwell.civ@us.navy.mil — N-1 / Building 1816
- Donald "Bubba" Lewis, CPS: (757) 406-1373, donald.lewis@cpschools.com — S-1 98% SWaM

---

## Subconsultant Data Verified

| Firm | Role | DSBSD Cert | Key Contact | Lead Project |
|---|---|---|---|---|
| McPherson Design Group | Structural | SWaM Small | — | V-8 (confirmed) |
| Hoggard-Eure Associates (HEA) | Civil/Site | SWaM Small | — | V-8 (confirmed) |
| GeoEnvironmental Resources (GER) | Geotechnical | SWaM Micro #9548 | — | V-8 (confirmed) |
| BSG | Independent CxA | — | — | ODU NHS (CxA only; BFA is not MEP prime on U-7) |
| Structr Advisors | Energy/Sustainability | DSBSD #S6740791 | Kelly DeVito, kelly.devito@structradvisors.com | VCU STEM Facility (LEED Gold) |
| Jensen Hughes | Fire Protection | Large business (not DSBSD) | — | — |
| Andre + Marquez Architects | Architecture | — | — | — |

---

## Lessons Learned Summary

1. **Start the Q&A period.** Missing the Q&A window cost influence over addendum content.
2. **Reference proposal intake needs a schema.** Narrative digestion produces wrong project characterizations; typed fields with explicit [VERIFY] flags catch errors earlier.
3. **First shred must process all attachments.** Win themes built on incomplete RFP data require expensive corrections later.
4. **Color team reconciliation must be atomic.** Partial updates to cross-referenced docs propagate errors through subsequent review passes.
5. **Geographic disadvantage is a real scoring cap.** At 323 miles / 4h54m, EVAL-003 will limit competitive position on any Virginia institution west of Richmond without a western Virginia satellite presence or affiliated firm.
6. **SWaM verification must happen at shred, not at Red Team.** V-8 SDVOSB→DSBSD correction at RT2 rippled across six documents.
7. **Honest disclosure outperforms overreach.** AARB gap, JMU zero task orders, Shur PE situation — direct acknowledgment with framing performed better than avoidance.

---

## Appendix A — Findings From Session-Transcript Mining

The 58 Claude Code sessions that ran the pursuit (≈125MB of JSONL) were mined 2026-04-24 for
friction points that didn't surface in `retrospective_notes.md` or the QW/SS/P3 lists above.
These items are registered in the backlog at IDs **GAP-38 … GAP-54, DISC-17 … DISC-20, ARCH-16**.

### A.1 Color-team review tooling gaps

- `color_team_review.sh --red` exits silently when pink findings are still open — no status output
  or gate error; the script simply returns with no action (**GAP-38**).
- No enforced prerequisite that pink must close before red can run. The user asked "So pink needs
  to clear before red runs?" and the tooling never answered — process knowledge, not code
  (**DISC-18**).
- Pink team re-review re-opened items that had been closed (struck AREC, flipped SOO authorship).
  Decisions in `color_team_reviews.md` drifted from the actual closure state (**DISC-17**).
- RT/PT findings (RT-05 O'Grady, RT-13 CO-3a appendix, RT-15 TCI scope) re-opened across passes —
  the tracker lacks a closure lock and dependency map (**GAP-49**).

### A.2 AE workbook and form gaps

- AE-1A header structure differs from AE-1..AE-6; cross-sheet formulas broke during population
  (**GAP-41**).
- AE-6 narrative overflow required manual page carry-over — no auto-paginate/overflow handler
  (**GAP-42**).
- AE-6 scaffold ships as a single tab; VT needed a multi-tab breakout by evaluation factor — the
  user had to ask for it explicitly (**GAP-43**).
- Scaffold generated per-sub AE packets that had to be torn down after Addendum 1 clarified no
  sub-AE forms were required (**GAP-54**).

### A.3 Intake, scaffold, and content-library gaps

- PC-number handling assumed DGS convention; VT-managed RFPs have no PC number and the templated
  headers broke (**GAP-46**).
- No staff utilization / % workweek model template for management volume — built from scratch
  (**GAP-47**).
- Recurring pattern: explaining an unlicensed senior engineer under PE responsible charge
  (Shur/Williams). Belongs as a reusable narrative asset in the content library (**GAP-48**).
- Subconsultant SWaM / cert-number registry missing — Dills #10615, Broyles #665787, GER #9548
  were entered ad-hoc (**GAP-44**).
- CO-3a insurance appendix artifacts surfaced at PT-03, not in the scaffold appendix list
  (**GAP-52**).
- The unreadable-attachment log lived inside `win_themes.md` rather than as a first-class intake
  artifact (**GAP-53**).

### A.4 Publish pipeline and quality gates

- Publish pipeline does not block on `PLACEHOLDER` / `[VERIFY]` tokens. Placeholder triple-blocks
  shipped in `price_volume/pricing_narrative.md` at one point and survived into a compile. A lint
  gate is needed (**GAP-45**).
- Workbook → PDF round-trip is manual between Red Team passes — the user had to generate and
  re-feed the PDF. Needs to be one publish step (**GAP-50**).
- Internal EVAL-00x IDs appeared in AE-6 narrative text; reviewers have no crosswalk from these
  codes to the RFP's actual grading criterion names (**GAP-39**).
- Gold team + schedule update + next-day plan were consistently requested as one action. A
  `finalize-day` script would consolidate (**GAP-51**).

### A.5 Process and workflow discipline

- Addendum delta propagation across AE-2/AE-6/compliance_matrix was manual — no script applies
  addendum changes as a batch (**GAP-40**).
- Reference list included projects (West Point Readiness Center) that had not been verified with
  the client. Needs a reference-verification pass before the draft moves to Pink (**DISC-19**).
- VT prior-client verification (U-1) relied on manual lookup; no automated attestation mechanism
  (**DISC-20**).

### A.6 Operational / runtime

- Files were written to the user's Desktop instead of the project folder during at least one
  session ("Why were you creating files on my desktop?"). Agent / script cwd needs to be pinned
  to the proposal root (**ARCH-16**).

### A.7 Template hygiene

- The WSSC retrospective remained in the template's retrospectives folder after v2.0 closed
  (**GAP-36**).
- Final manual review still required hand resizing/formatting work that was never scripted
  (**GAP-37**).
