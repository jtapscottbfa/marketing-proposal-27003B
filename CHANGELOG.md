# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.0.2] - 2026-04-30

### Added

#### `populate_ae_forms.py` — DGS-30-004 AE-form population (closes #8)

Promotes the VT pursuit's 1,330-line script into a content-library-driven
engine module. Eight PRs split framework first, then one populator per PR
for reviewability:

- **#79** — framework: `scripts/lib/ae_form_helpers.py` (openpyxl wrappers — `write_cell`, `fit_merged_rows`, `fill_dgs_header`, `load_template`, `save_workbook`), `scripts/lib/firm_profile.py` (loader for `~/.bfa/firm_profile.yml` per ARCH-11), CLI dispatcher with `--list`/`--only`, pre-flight gates that refuse to run on `[VERIFY]` content_library rows or `PLACEHOLDER` firm_profile fields.
- **#80** — AE-1 (Firm Data): firm-identity, ownership, principals, personnel-by-discipline (14 rows × 4 columns).
- **#81** — AE-1A (Firm Data continued): insurance narrative, SWaM percentage + narrative, Virginia state agency contracts (≤20), representative-project summary table (5 rows). Adds `proposal_config.representative_projects` (drives both AE-1A and AE-5).
- **#82** — AE-3 (Project Staffing Organization): **closes DISC-09**. Key-personnel slot resolver pins the org-chart table to typed inputs (`personnel_id` lookup or explicit inline) — no AI-fill, no plausible-but-wrong values. Adds `firm_profile.narratives` (staff availability, project methodology, QA/QC) and `proposal_config.key_personnel`.
- **#83** — AE-4 (Personnel Qualifications): per-personnel cardinality. New `content_library/personnel_projects.csv` table linking people × projects with role text. Derives AE-4 registration line from `license_*` fields when no override is set; supports per-pursuit `duty`/`assignment`/`pct` overrides on `key_personnel` slots.
- **#84** — AE-5 (Representative Project Data): per-project cardinality. 16 new optional columns on `projects.csv` (construction data, codes, SWaM); two new tables — `project_contacts.csv` (admin POC + construction prime/supt) and `project_designers.csv` (design team by discipline).
- **#85** — AE-6 (Supplemental Information): multi-tab narrative populator. Reads a per-pursuit markdown draft, splits on `## Section N` headings, strips markdown decorations + internal proposal-shred refs (EVAL-NNN/TECH-NNN/REQ-NNN), paginates long sections across continuation tabs.
- **#86** — AE-2 (Consultant Data): per-firm, mirrors AE-1 cell layout for sub firms. Adds `proposal_config.proposed_subconsultants` and 3 optional `firms.csv` columns (`fax`, `other_names`, `legal_form`).

SF330 Part 2 stubbed to a separate proposal type (ARCH-12).

311 tests across the issue, all passing. Issue #8 met all 8 acceptance criteria.

#### `scripts/lib/csv_renderer.py` — content_library reader

Schema-driven reader for `content_library/*.csv` (projects, personnel,
firms, past_performance, plus three new tables for AE-form population:
personnel_projects, project_contacts, project_designers). Type coercion,
semicolon-list splitting, enum validation, and `[VERIFY]` enforcement on
required columns. Includes `render_project_one_liner` (compact AE-5 cell
labels) and `render_personnel_role_block` (multi-line AE-4
employment-history boxes). Initial version landed in #74; extended
through #79, #83, and #84 to support the AE-form populator dispatcher.

#### `scripts/publish/sanity_check.py` — pre-submission verification (ARCH-05)

Generalized check registry replacing VT's 311-line, 86-hardcoded-check
script. Pre-flight residue checks (`[VERIFY]`, `PLACEHOLDER`, `[FIXME]`,
markdown-as-text), prohibited-content patterns, proof-points, addendum
acknowledgement, and personnel/firm form-coverage matching the
content_library. CLI exit codes for safe-to-submit gating; Python API
for embedding in other scripts. (#76)

#### `scripts/proposal_digest.sh` — proposal-PDF ingestion (ARCH-15)

Reads prior proposal PDFs, extracts every project / past-performance
entry as a structured record with YAML frontmatter, and produces a
ranked Project Selector keyed to the active pursuit's win themes. Emits
a DISC-19 client-attestation list documenting which clients each prior
proposal claimed. (#71)

#### Color-team review (issue #7 — partial)

Finding-schema YAML + volumes-config wiring for Pink/Red/Gold gate
output (#77), plus the gate-running script
`scripts/review/color_team_review.sh` (#78). The script reads
`00_admin/proposal_config.yml::volumes` to enumerate active volume
content, runs the configured gate (Pink → Red → Gold), and writes
findings to `00_admin/color_team_reviews.md` per
`00_admin/color_team_reviews.SCHEMA.md`. Pre-flight checks: addendum
freshness vs. last RFP shred (GAP-33), and prior-gate H findings must
be resolved or accepted (GAP-38, GAP-49).

Issue #7 stays open after v0.0.2 — `review_triage.sh` and Blue/Black
Hat gate scripting are out of scope for this release.

#### Claude Code cwd guardrail (ARCH-16)

Prevents the agent from writing outside the active repo root after a
prior session wrote files to the user's Desktop. Two phases:

- **Phase 1** (#66) — Python `scripts/lib/guard_cwd.py` helper with tests; matches the bash `guard_cwd.sh` contract.
- **Phase 2** (#69) — Claude Code `PreToolUse` hook in `.claude/settings.json` runs `python scripts/hooks/cwd_guard_hook.py` before every `Write`/`Edit`/`NotebookEdit` tool call. Repo-relative — works the same way in the engine repo and any scaffolded proposal repo. Allowlists `~/.claude/projects/` for auto-memory storage.

#### `new_proposal.sh` reads firm_profile.yml at scaffold (ARCH-11)

The new pursuit's `proposal_config.yml` `firm:` block (`name`,
`short_name`, `address`, `website`) is pre-filled from
`~/.bfa/firm_profile.yml` (override path via `$BFA_FIRM_PROFILE`)
when the firm profile is present. Per-field PLACEHOLDER-skip: fields
still bearing the `PLACEHOLDER:` marker in the firm profile fall back
to the scaffold defaults rather than propagating the template marker.
Headers in `firm_profile.yml.example` and `proposal_config.yml.example`
updated to describe the wiring. (#88)

#### `content_library/` framework (ARCH-08)

Initial scaffold (#70) with header-only CSVs for `projects.csv`,
`personnel.csv`, `firms.csv`, `past_performance.csv` plus a `narratives/`
directory. Schemas documented in `content_library/README.md`. Extended
through the issue #8 PRs with `personnel_projects.csv` (#83),
`project_contacts.csv` + `project_designers.csv` (#84), and 16 new
optional columns on `projects.csv` (#84).

#### CI shellcheck job

`.github/workflows/proposal_ci.yml` adds a shellcheck job that lints
every tracked `.sh` file under `scripts/`. Uses `-x --severity=warning
--source-path=SCRIPTDIR --source-path=scripts/lib` so cross-script
`source` resolution works without false-positive SC1091 noise. (#68)

#### Engine-repo label sync

`scripts/github/labels.yml` + `sync_labels.sh` — canonical engine-repo
issue label set, idempotent sync via `gh label create --force` with
optional `--prune`. (#1)

#### Customer-zip packaging — `scripts/ship/`

`scripts/ship/package_zip.sh` builds a clean customer-specific zip
from HEAD. Substitutes licensee name + effective date into the
customer LICENSE template (`scripts/ship/LICENSE.customer.template`).
Rewrites GitHub-URL references in the staged export to a
`<your-org>/ae-proposal-engine` placeholder across
`.md`/`.yml`/`.sh`/`.py`/`.json` files so the receiving customer can
drop in their own. Excludes `scripts/ship/` itself from the export —
customers are licensed to use the engine, not redistribute it, so
the packaging tooling has no business in their copy. Strips `.git/`
and dev artifacts via `git archive`. Output defaults to `_ship/`
(gitignored). Driven by the BFA delivery model. (#92)

### Changed

- **`LICENSE` — proprietary, all rights reserved.** Replaces MIT.
  The engine is now Jonathan Tapscott's proprietary IP; possession of
  a copy does not grant any license by default. Customer-specific
  limited-use licenses are issued per delivery via the
  `scripts/ship/` pipeline — see
  `scripts/ship/LICENSE.customer.template` for the per-licensee
  grant template. (#92)
- **Backlog migrated to GitHub Issues.** 54 active backlog rows from `00_admin/template_backlog.md` opened as engine-repo issues; 15 rows marked covered by v0.0.1 ship; v0.0.2 ship gate teed up. Backlog markdown file kept as historical record.
- **`00_admin/firm_profile.yml.example`** extended with optional sections used by AE-form populators: `insurance` (#81), `swam` (#81), `agency_contracts` (#81), `narratives` (#82). Plus 3 optional AE-1 fields: `years_under_current_name`, `parent_phone`, `parent_fax` (#80).
- **`00_admin/proposal_config.yml.example`** extended with optional per-pursuit sections: `key_personnel` (#82), `representative_projects` (#81), `proposed_subconsultants` (#86), `ae6_narrative_path` (#85).
- **`scripts/scaffold/proposal_types/ae_term_contract.yml`** adds `ae_forms:` data-driven tab list (7 form codes with `cardinality` and `enabled` flags) — the dispatcher reads this rather than hardcoding the form set.
- **`requirements.txt`** adds `openpyxl>=3.1` for `.xlsx` population.
- **`.gitattributes`** enforces LF line endings on code files (`*.py`, `*.sh`, `*.yml`, `*.md`, etc.) to keep diffs clean across Windows + Linux contributors. (#67)
- **README install instructions** use `npm ci` (reads lockfile exactly) instead of the stale `npm install adm-zip @xmldom/xmldom` + `npm install -g docx` pair. Build deps are already pinned in `package.json`. (#3)
- **`populate_ae_forms.py` framework-phase residue retired.** Module/test docstrings rewritten now that all six populators ship; dead `NotImplementedError` dispatcher arm removed; `firm_profile.py` schema reference filled in for the three optional AE-1 fields shipped in #80. Doc-only plus one-line refactor; no behavior change. (#89)

### Fixed

- CI `build-check` job now installs Node dependencies (`actions/setup-node@v4` + `npm ci`) before invoking `build_docx.sh`. Previously failed with `Cannot find module 'adm-zip'` because the workflow had no Node setup step. (#2)

### Security

- Bumped `@xmldom/xmldom` 0.9.9 → 0.9.10 — patches GHSA-2v35-w6hq-6mfw (DoS via uncontrolled recursion in XML serialization) and three related XML injection advisories (GHSA-f6ww-3ggp-fr8h, GHSA-x6wf-f3px-wcqx, GHSA-j759-j44w-7fr8). Real-world exposure low (we serialize pandoc's own output, not adversarial input), but no reason to ship known CVEs. Also syncs `package-lock.json` "version" field (was stale `1.0.0`, now matches `package.json`'s `0.0.1`). (#4)

## [0.0.1] - 2026-04-27

Initial release. Production engine for concurrent A/E proposal pursuits, with the eight pre-release fatal-flaw items from the VT pursuit retrospective resolved before first push.

### Added

#### Foundations

- Initial project kickoff as a formal GitHub project under MIT license.
- Proposal scaffolding system (`scripts/scaffold/new_proposal.sh`) with five presets: `sled_full`, `sled_qualifications`, `hed_research`, `design_build`, `ae_term_contract`.
- Pandoc-based build pipeline (`scripts/publish/`) producing branded `.docx` volumes and a combined submission file.
- APMP/Shipley-aligned admin templates in `00_admin/` (bid/no-bid, RFP shred, win themes, schedule, color team reviews, pre-submission gaps).
- Compliance matrix (`compliance_matrix.md`) linking RFP requirements to proposal sections.
- Git automation: proposal aliases (`scripts/git/proposal-aliases.sh`) and pre-commit hook for PLACEHOLDER and empty-file audits.
- GitHub Actions CI workflow (`.github/workflows/proposal_ci.yml`): markdown lint, PLACEHOLDER audit, docx build check.
- Issue templates (action item, review gate, RFP requirement) and pull request template.
- Branching, commit, and versioning conventions codified in `README.md` (trunk-based, Conventional Commits, SemVer with squash-merge).

#### Engine dev process separation

- `docs/` folder for engine-internal documentation (engine-historical retrospectives moved here from root); `retrospectives/` at root reserved as a per-pursuit scaffold folder. (GAP-36)
- `CLAUDE.md` codifies agent operating instructions: cwd discipline, internal-notes convention, repository context, and workflow conventions.
- `new_proposal.sh` propagates `retrospectives/` and `CLAUDE.md` into scaffolded child proposal repos; `docs/` and `LICENSE` are intentionally excluded (engine-only).

#### Working-directory and intake guardrails (ARCH-16)

- New `scripts/lib/guard_cwd.sh` — sourced by every script; refuses to run when the resolved repo root is neither the engine repo nor a scaffolded proposal repo.
- `new_proposal.sh` rejects any output path that resolves inside the engine repo itself, preventing self-nested proposals.

#### Repo hygiene (GAP-29)

- Removed mock RFP (`test_rfp.txt`) and reset `subconsultant_digest.md` to a clean default while preserving the seven A/E discipline rows.
- `.gitignore` extended to cover `rfp_intake/{original_rfp,addendums,attachments}/` content (with `.gitkeep` exceptions), `media-*/`, `media/`, `_scratch/`, `_tmp/`.

#### RFP shred — multi-folder collection (GAP-35)

- New `00_admin/rfp_intake/attachments/` folder for exhibits, reference specs, drawings, and standard contracts.
- `rfp_shred.sh` now collects content from all three intake subfolders (primary RFP, addendums, attachments) into a single bundle with section markers, instead of processing only the primary file.
- File-type dispatcher supporting `.pdf` (via `pdftotext`), `.txt`, `.md`, and `.docx` (via `pandoc`); unsupported types are flagged loudly at end of run.

#### RFP shred — silent-failure paths closed (GAP-34)

- Per-file size-delta validation: extraction tools that exit 0 with empty output are now caught and flagged, not silently passed through.
- Pre-flight tool check warns and prompts before running when extraction tools are missing for file types present in the intake.
- Claude output validation: empty or structurally-invalid responses abort the run with both the bundle and raw-output paths preserved for inspection (`KEEP_TEMPS` flag short-circuits the cleanup trap).
- `sed` backfill verification: each `proposal_config.yml` substitution is grepped for confirmation; silent no-ops are surfaced.

#### Publish lint gate (GAP-45, GAP-28)

- `check_output_pdf.sh` patterns expanded to include `[VERIFY]`, `[NEEDS_VERIFICATION]`, `[FIXME]`, `[TODO]`, `[XX]`, `[XXX]`, `[INTERNAL]`, `[DRAFT]`, and `*End of draft*` markers.
- `combine_volumes.sh` runs the lint gate automatically on the combined output and **blocks submission** on any hit; emergency `--no-lint` override available with prominent warning.
- `build_docx.sh` runs the lint gate after per-volume builds; warn-only by default to support authoring iteration, with `--strict` to block (CI / Gold Team) and `--no-lint` to skip.
- HTML-comment convention (`<!-- INTERNAL: … -->`) documented as the way to write invisible internal notes; verified that Pandoc strips them from `.docx` output.

#### Scaffold robustness (GAP-18)

- Section selection accepts comma- or space-separated input; non-numeric and out-of-range entries are skipped with warnings instead of crashing the script.
- Phase 1 metadata collection has a review/edit/quit loop — fields can be re-entered without restarting the script.
- Empty values rejected for required fields (RFP title, number, agency); date format mismatch warns but accepts.

[Unreleased]: https://github.com/<your-org>/ae-proposal-engine/compare/v0.0.2...HEAD
[0.0.2]: https://github.com/<your-org>/ae-proposal-engine/releases/tag/v0.0.2
[0.0.1]: https://github.com/<your-org>/ae-proposal-engine/releases/tag/v0.0.1
