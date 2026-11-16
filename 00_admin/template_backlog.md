# Proposal Template Backlog

**Last updated:** 2026-04-27
**Active Version:** v0.0.1 (shipped 2026-04-27); v0.0.2 in planning

> **NOTE (2026-04-27):** Active backlog has **migrated to GitHub Issues** at
> https://github.com/<your-org>/ae-proposal-engine/issues. See milestones for
> v0.0.2 / v0.0.3 / v0.1.0 / v0.2.0. Closed and Migrated rows below are the
> historical record. The Cross-References section at the bottom preserves
> retrospective ↔ backlog-ID mappings.


> **v0.0.1 ship gate (closed 2026-04-27):** Of the original 8 fatal-flaw
> items (ARCH-16, GAP-18, GAP-28, GAP-29, GAP-34, GAP-35, GAP-36, GAP-45),
> 7 closed and ARCH-16 is In Progress — shell coverage shipped (guard_cwd.sh
> sourced by 7 scripts; new_proposal.sh refuses self-nested scaffolding).
> Python coverage + Claude Code agent hook carry to v0.0.2.
>
> **v0.0.2 ship gate (next):** Four VT-pursuit show-stoppers must land
> before the next concurrent pursuits begin — ARCH-04 (color_team_review.sh
> + review_triage.sh), ARCH-02 (populate_ae_forms.py + ae1–ae6 scaffold),
> ARCH-15 / DISC-10 (proposal_digest.sh), ARCH-05 (sanity_check.py). Each
> was built ad-hoc inside the VT pursuit; without them in the engine, the
> next pursuit will repeat the same scratch-build cost.
>
> All other items are deferred to post-v0.0.2 triage. Legacy `2.0` / `2.1` /
> `3.0` version labels predate the v0.0.x reset and will be re-mapped to
> real `v0.x.y` milestones before bulk migration to GitHub Issues.
**Sources:**

- docs/retrospectives/wssc_postmortem.md (v2.0 items)
- docs/retrospectives/vt_443882616_postmortem.md (v2.1 / 3.0 items — VT RFP #443882616, submitted 2026-04-23)
- docs/retrospectives/retrospective_notes.md (VT field notes)

## Status Lifecycles
- **Scripts** Not Started → In Progress → Tested → Committed → Closed
- **Content** Not Started → In Progress → Reviewed → Committed → Closed

## ID Glossary
- **GAP:** Proposal Template Gap
- **DISC:** Process/Discipline Gap
- **ARCH:** Architectural Change


| ID | Description | File/Folder | Assignee | Priority | Version | Status |
| ---- | ------------------------ | ---------------- | -------- | -------- | ---- | -------- |
| GAP-01 | No A&E Term Contract Preset YAML | scripts/scaffold/proposal_types/ | jtapscott | High | 2.0 | Closed |
| GAP-02 | No Artifact Folder Scaffold | 06_attachments/ | jtapscott | High | 2.0 | Closed |
| GAP-03 | No Subconsultant Intake Structure | 00_admin/ | jtapscott | High | 2.0 | Closed |
| GAP-04 | rfp_shred.md Missing Addendum Change Log Section | 00_admin/ | jtapscott | High | 2.0 | Closed |
| GAP-06 | rfp_shred.md Missing Pass/Fail Minimum Qualifications Section | 00_admin/ | jtapscott | High | 2.0 | Closed |
| GAP-08 | No 'pre_submission_gaps.md | 00_admin/ | jtapscott | High | 2.0 | Closed |
| GAP-13 | Pandoc --number-sections Causes Double-Numbering | scripts/publish/ | jtapscott | High | 2.0 | Closed |
| GAP-15 | CI Pipeline Missing 'npm ci' Before Build Step | scripts/publish/build_docx.sh | jtapscott | High | 2.0 | Closed |
| DISC-01 | proposal_schedule.md Never Filled In | 00_admin/ | jtapscott | High | 2.0 | Closed |
| DISC-02 | compliance_matrix.md Never Populated | 00_admin/ | jtapscott | High | 2.0 | Closed |
| DISC-05 | Two Unresolved PLACEHOLDERs in Final Delivered PDF | - | jtapscott | Critical | 2.0 | Closed |
| GAP-05 | rfp_shred.md Missing Source/Addendum Header Field | 00_admin/ | jtapscott | High | 2.0 | Closed |
| GAP-07 | rfp_shred.md Missing "Key Facts at a Glance" Block | 00_admin/ | jtapscott | High | 2.0 | Closed |
| GAP-09 | No mbe_tracker.md Template | 00_admin/ | jtapscott | Low | 2.1 | Migrated -> #34 |
| GAP-10 | highlight_placeholders.py Missing from Template | scripts/publish/ | jtapscott | High | 2.1 | Migrated -> #35 |
| GAP-11 | proposal_intake.sh Missing From Template | scripts/scaffold/ | jtapscott | High | 2.1 | Migrated -> #36 |
| GAP-12 | compliance_matrix.md Uses Hardcoded Volume Labels | / | jtapscott | High | 2.1 | Migrated -> #45 |
| GAP-14 | Section Starters Hardcode Heading Numbers | - | jtapscott | Medium | 2.1 | Migrated -> #50 |
| GAP-16 | CI PLACEHOLDER Audit Uses Hardcoded Folder Names | github/workflows/ | jtapscott | Medium | 2.1 | Migrated -> #51 |
| GAP-17 | PDF Bookmarking Not Addressed in Build Documentation | / | jtapscott | Low | 2.1 | Migrated -> #37 |
| DISC-03 | bid_no_bid.md Never Filled In | 00_admin/ | jtapscott | Low | 2.1 | Migrated -> #60 |
| DISC-04 | win_themes.md Never Populated - Themes Scattered into rfp_shred.md | 00_admin/ | jtapscott | Medium | 2.1 | Migrated -> #61 |
| DISC-06 | Reference Proposal Digestion Imports Stale/Irrelevant Content | 00_admin/reference_proposals/ | jtapscott | Medium | 2.1 | Migrated -> #62 |
| ARCH-01 | Resequence workflow: shred before scaffold | new_proposal.sh | jtapscott | High | 3.0 | Migrated -> #15 |
| GAP-18 | Section selection accepts commas + space; non-numeric entries skip with warning instead of crashing; metadata phase has summary+edit+quit loop; empty values rejected; bad date format warns | scripts/scaffold/new_proposal.sh | jtapscott | High | 0.0.1 | Closed |
| GAP-19 | bid_no_bid.md ships blank — not pre-populated from proposal_config.yml at scaffold | 00_admin/ | jtapscott | High | 2.1 | Migrated -> #16 |
| GAP-20 | rfp_shred.sh re-prompts for RFP title instead of reading proposal_config.yml | scripts/shred/rfp_shred.sh | jtapscott | High | 2.1 | Migrated -> #46 |
| GAP-21 | proposal_schedule.md milestone dates remain placeholders — not calculated from deadline | 00_admin/ | jtapscott | High | 2.1 | Migrated -> #17 |
| GAP-22 | compliance_matrix.md not auto-stubbed with one row per extracted requirement post-shred | 00_admin/ | jtapscott | High | 2.1 | Migrated -> #18 |
| GAP-23 | color_team_reviews.md not seeded with gate headers and findings table post-shred | 00_admin/ | jtapscott | High | 2.1 | Migrated -> #19 |
| GAP-24 | Em dashes saturate AI-generated narratives (AI smell) — no strip pass | scripts/publish/ | jtapscott | Medium | 2.1 | Migrated -> #47 |
| GAP-25 | Markdown renders as literal syntax in AE-6 / Excel cells — no md→bullet conversion | scripts/populate_ae_forms.py | jtapscott | High | 2.1 | Migrated -> #40 |
| GAP-26 | AE-5 gross_sf appends "sf" to N/A entries | scripts/populate_ae_forms.py | jtapscott | Medium | 2.1 | Migrated -> #41 |
| GAP-27 | AE-5 const_end column truncates; In Progress / Ongoing variants not normalized | scripts/populate_ae_forms.py | jtapscott | Medium | 2.1 | Migrated -> #42 |
| GAP-28 | [INTERNAL] / [DRAFT] / *End of draft* added to lint gate (extends GAP-45); HTML-comment convention for invisible internal notes documented in CLAUDE.md | scripts/publish/, CLAUDE.md | jtapscott | Critical | 0.0.1 | Closed |
| GAP-29 | Mock RFP and media-* temp folders left in template repo; no .gitignore entries | / | jtapscott | High | 0.0.1 | Closed |
| GAP-30 | Kickoff meeting compilation emits double numbering | 00_admin/kickoff_meeting.md | jtapscott | Medium | 2.1 | Migrated -> #52 |
| GAP-31 | README lacks "Running the RFP Shred" section and common-errors guide | scripts/scaffold/README.md | jtapscott | Medium | 2.1 | Migrated -> #20 |
| GAP-32 | new_proposal.sh does not print new GitHub repo URL / git remote set-url at end — partial: prints command in next-steps; auto-creation via gh repo create pending | scripts/scaffold/new_proposal.sh | jtapscott | Low | 2.1 | Migrated -> #21 |
| GAP-33 | No addendum pre-flight check at color team review gates | scripts/color_team_review.sh | jtapscott | High | 2.1 | Covered -> #7 |
| GAP-34 | Shred silent-failure paths closed: extraction-tool empty output, Claude empty/malformed output, missing tool pre-flight, sed backfill verification | scripts/rfp_shred.sh | jtapscott | Critical | 0.0.1 | Closed |
| GAP-35 | Shred now collects from original_rfp/ + addendums/ + attachments/; unreadable files flagged loudly | scripts/rfp_shred.sh | jtapscott | Critical | 0.0.1 | Closed |
| GAP-36 | Engine-historical retrospectives leaked into per-pursuit scaffold folder — moved to docs/retrospectives/ | docs/retrospectives/ | jtapscott | High | 0.0.1 | Closed |
| GAP-37 | Final manual review requires hand resizing/formatting work — not scripted | scripts/publish/ | jtapscott | Low | 3.0 | Migrated -> #38 |
| DISC-07 | win_themes / compliance_matrix / project_selector drift during revisions — no atomic reconciliation | 00_admin/ | jtapscott | High | 2.1 | Migrated -> #63 |
| DISC-08 | Color team reviews are high-token — no --fast mode with lighter digestion model | scripts/color_team_review.sh | jtapscott | Medium | 2.1 | Migrated -> #12 |
| DISC-09 | DGS workbook roles table has hallucination risk — roles not pinned to typed config | scripts/populate_ae_forms.py | jtapscott | High | 2.1 | Covered -> #8 |
| DISC-10 | Reference proposal digestion narrative-based; needs structured project_digest.md with [VERIFY] | scripts/proposal_digest.sh | jtapscott | Medium | 2.1 | Covered -> #6 |
| DISC-11 | Addendum tracking not wired to compliance_matrix rows | 00_admin/ | jtapscott | High | 2.1 | Migrated -> #22 |
| DISC-12 | 00_admin disorganized — scripts use hardcoded paths, not proposal_config.yml | 00_admin/ | jtapscott | Medium | 2.1 | Migrated -> #23 |
| DISC-13 | Second-pass color team reconciliation fragile — no tracking of docs each finding touches | scripts/review_triage.sh | jtapscott | High | 2.1 | Migrated -> #13 |
| DISC-14 | Internal reference cleanup before publish not systematic — only applied to AE-6 | scripts/publish/ | jtapscott | Medium | 2.1 | Migrated -> #64 |
| DISC-15 | SWaM / certification verification happens at Red Team rather than at shred | scripts/shred/rfp_shred.sh | jtapscott | High | 2.1 | Migrated -> #24 |
| DISC-16 | Q&A period window not flagged in proposal_schedule — BFA missed VT Q&A deadline | 00_admin/ | jtapscott | High | 2.1 | Migrated -> #25 |
| ARCH-02 | AE form population infrastructure does not exist in template (ae1–ae6 dirs, blanks, populate_ae_forms.py) | scripts/, 06_attachments/ | jtapscott | Critical | 3.0 | Covered -> #8 |
| ARCH-03 | Package assembly + PDF compile not in template (assemble_package.py, compile_package.py, bookmarks, TOC) | scripts/publish/ | jtapscott | Critical | 3.0 | Migrated -> #14 |
| ARCH-04 | Color team scripting not in template (color_team_review.sh, review_triage.sh, Blue/Black Hat gates) | scripts/ | jtapscott | Critical | 3.0 | Covered -> #7 |
| ARCH-05 | Sanity check script not in template — no pre-submission readiness verification | scripts/sanity_check.py | jtapscott | Critical | 3.0 | Covered -> #9 |
| ARCH-06 | Shred must loop all rfp_intake files with file-type dispatcher (pdf/docx/txt) and unreadable-file flag — duplicate of GAP-35; closed by same work | scripts/rfp_shred.sh | jtapscott | Critical | 0.0.1 | Closed |
| ARCH-07 | Subconsultant intake not scaffolded by discipline at scaffold-time (rfp_shred.sh creates per-discipline folders post-shred); no pre-color-team validation | 00_admin/subconsultant_intake/ | jtapscott | High | 3.0 | Migrated -> #26 |
| ARCH-08 | Content library + project_selector not in template (projects.csv, personnel.csv, firms.csv, past_performance.csv) | content_library/ | jtapscott | Critical | 3.0 | Covered -> #5 |
| ARCH-09 | Proposal outline not generated after shred; generic 01–17 folders don't match AE structure | scripts/shred/, scripts/scaffold/ | jtapscott | High | 3.0 | Migrated -> #27 |
| ARCH-10 | No org chart generation tooling — manual Visio dependency (Graphviz/Mermaid from config) | scripts/publish/ | jtapscott | Medium | 3.0 | Migrated -> #28 |
| ARCH-11 | Go/No-Go module does not exist at firm-profile level — bid_no_bid.md is reactive only | scripts/scaffold/, ~/.bfa/firm_profile.yml | jtapscott | High | 3.0 | Migrated -> #29 |
| ARCH-12 | SF330 proposal type not scaffolded (Part 1 A–F + Part 2 form population) | scripts/scaffold/proposal_types/sf330.yml | jtapscott | High | 3.0 | Migrated -> #30 |
| ARCH-13 | VA DGS AE term contract proposal type: promote ae1–ae6 scaffold from VT pursuit — preset shell exists; ae1–ae6 form scaffold + tab structure pending | scripts/scaffold/proposal_types/ae_term_contract.yml | jtapscott | High | 3.0 | Migrated -> #31 |
| ARCH-14 | CPARS/PPQ ingest not in template — past performance not in content library | scripts/, content_library/past_performance.csv | jtapscott | High | 3.0 | Migrated -> #32 |
| ARCH-15 | Reference proposal digestion needs typed schema — current narrative produces wrong characterizations | scripts/proposal_digest.sh | jtapscott | High | 3.0 | Covered -> #6 |

| GAP-38 | color_team_review.sh exits silently when prerequisite gate incomplete — no status/error output | scripts/color_team_review.sh | jtapscott | High | 2.1 | Covered -> #7 |
| GAP-39 | EVAL-00x internal IDs used in AE-6 narrative; no crosswalk to RFP grading criterion names for reviewer | scripts/publish/ | jtapscott | Medium | 2.1 | Migrated -> #53 |
| GAP-40 | Addendum delta propagation not automated — manual sweep across AE-2/AE-6/compliance_matrix | scripts/ | jtapscott | High | 2.1 | Migrated -> #54 |
| GAP-41 | AE-1A header structure differs from AE-1..AE-6 and breaks cross-sheet formulas in workbook | scripts/populate_ae_forms.py | jtapscott | High | 2.1 | Migrated -> #43 |
| GAP-42 | AE-6 narrative overflow required manual page carry-over — no auto-paginate/overflow handler | scripts/populate_ae_forms.py | jtapscott | High | 2.1 | Migrated -> #11 |
| GAP-43 | AE-6 ships single-tab scaffold; VT needed multi-tab breakout by evaluation factor | scripts/scaffold/proposal_types/ae_term_contract.yml | jtapscott | High | 2.1 | Migrated -> #33 |
| GAP-44 | Subconsultant SWaM / cert-number registry missing from content library | content_library/firms.csv | jtapscott | High | 3.0 | Covered -> #5 |
| GAP-45 | Publish lint gate added: combine_volumes blocks on PLACEHOLDER/[VERIFY]/[FIXME]/[TODO]/[XX] hits; build_docx warns by default, blocks with --strict; emergency override via --no-lint | scripts/publish/ | jtapscott | Critical | 0.0.1 | Closed |
| GAP-46 | PC-number handling assumes DGS — VT-managed RFPs have none; breaks templated headers | scripts/scaffold/, 00_admin/proposal_config.yml | jtapscott | High | 2.1 | Migrated -> #48 |
| GAP-47 | No staff utilization / % workweek model template for management volume | 03_management_volume/ | jtapscott | Medium | 2.1 | Migrated -> #55 |
| GAP-48 | Responsible-charge / unlicensed-senior-PE narrative pattern needed as library asset (Shur/Williams) | content_library/narratives/ | jtapscott | Medium | 3.0 | Covered -> #5 |
| GAP-49 | Findings tracker (RT/PT) lacks closure lock and dependency tracking — items re-open (RT-05, RT-13, RT-15) | scripts/review_triage.sh | jtapscott | High | 2.1 | Covered -> #7 |
| GAP-50 | Workbook → PDF round-trip is manual between RT passes — no automated publish step | scripts/publish/ | jtapscott | Medium | 2.1 | Migrated -> #56 |
| GAP-51 | No finalize-day script combining gold team + schedule update + next-day plan | scripts/ | jtapscott | Low | 3.0 | Migrated -> #57 |
| GAP-52 | CO-3a insurance / appendix artifacts surfaced late (PT-03); not in scaffold appendix list | 06_attachments/, scripts/scaffold/ | jtapscott | Medium | 2.1 | Migrated -> #58 |
| GAP-53 | Unreadable-attachment log lives inside win_themes.md — should be first-class intake artifact | 00_admin/rfp_intake/ | jtapscott | Medium | 2.1 | Migrated -> #59 |
| GAP-54 | Scaffold generates per-sub AE packets that had to be torn down after Addendum 1 clarification | scripts/scaffold/proposal_types/ae_term_contract.yml | jtapscott | Medium | 2.1 | Migrated -> #49 |
| DISC-17 | Pink team re-review re-opened closed items (AREC, SOO authorship) — decisions drifted from color_team_reviews.md | scripts/color_team_review.sh | jtapscott | High | 2.1 | Migrated -> #44 |
| DISC-18 | No enforced pink→red gating — "does pink need to clear before red runs?" unanswered by tooling | scripts/color_team_review.sh | jtapscott | High | 2.1 | Covered -> #7 |
| DISC-19 | Reference list included unverified clients (West Point) — no reference-verification pass before draft | scripts/proposal_digest.sh | jtapscott | High | 2.1 | Covered -> #6 |
| DISC-20 | VT prior-client verification (U-1) done manually — no automated lookup / attestation mechanism | scripts/ | jtapscott | Medium | 3.0 | Migrated -> #65 |
| ARCH-16 | Agent / script cwd guardrail — files were written to user Desktop instead of project folder. Shell coverage shipped (guard_cwd.sh; new_proposal.sh refuses self-nested scaffolding). Python coverage + Claude Code agent hook pending. | scripts/, agent config | jtapscott | Critical | 0.0.1 | Covered -> #10 |

## Cross-References

- Full VT pursuit post-mortem: [docs/retrospectives/vt_443882616_postmortem.md](../docs/retrospectives/vt_443882616_postmortem.md)
  - QW-01 through QW-16 → GAP-18 through GAP-33 (+ GAP-34, GAP-35 from SS-05 shred details)
  - SS-01 through SS-10 → ARCH-02 through ARCH-11
  - P3-01 through P3-10 → DISC-07 through DISC-14 + ARCH-12 / ARCH-14
- VT field notes: [docs/retrospectives/retrospective_notes.md](../docs/retrospectives/retrospective_notes.md)
- Remediation logs (PT-01 through PT-11): [docs/retrospectives/](../docs/retrospectives/)
- GAP-38 through GAP-54, DISC-17 through DISC-20, ARCH-16 sourced from mining the 58 VT-pursuit session transcripts (see post-mortem Appendix A)
