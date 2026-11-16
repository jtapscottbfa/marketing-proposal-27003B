# A/E Proposal Template

Public Sector Marketing Proposal System  
Framework: APMP Best Practices · Shipley Methodology  
Targets: State & Local Government · Higher Education / Research  
Output: `.docx` via Pandoc · Solo author · Git version control

**Template Version:** v0.0.1

---

## Table of Contents

- [Overview](#overview)
- [Dependencies](#dependencies)
- [Quick Start](#quick-start)
- [Folder Structure](#folder-structure)
- [Configuration](#configuration)
- [Proposal Workflow](#proposal-workflow)
- [Build Pipeline](#build-pipeline)
- [Git Aliases](#git-aliases)
- [Scaffolding](#scaffolding)
- [Compliance and Requirements Tracking](#compliance-and-requirements-tracking)
- [CI/CD Pipeline](#cicd-pipeline)
- [GitHub Template Setup](#github-template-setup)
- [Branching, Commits, and Versioning](#branching-commits-and-versioning)
- [Windows / Git Bash Notes](#windows--git-bash-notes)

---

## Overview

This repository is a reusable proposal generation system for public sector bids. It scaffolds a structured proposal project, provides APMP/Shipley-aligned authoring documents, and converts Markdown source files into a branded `.docx` submission package via Pandoc.

**What it does:**

- Generates a complete proposal folder in minutes via interactive or preset-based scaffolding
- Enforces compliance tracking from RFP shred through submission
- Converts Markdown volumes to professional `.docx` output with consistent branding, headers, and footers
- Integrates Git milestone tagging aligned with Shipley review gates (Pink/Red/Gold Team)
- Runs automated linting, placeholder audits, and build checks via GitHub Actions on every push

**Supported proposal types:**

- State/Local/Municipal (SLED) — full or qualifications-only
- Higher Education / Research
- Design-Build
- Architecture/Engineering Term Contracts

---

## Dependencies

All dependencies must be available in your Git Bash terminal.

### Required tools

| Tool | Version | Install |
|---|---|---|
| **Git** | Any recent | [git-scm.com/download/win](https://git-scm.com/download/win) — use "Git Bash" terminal |
| **Pandoc** | 2.x or 3.x | [pandoc.org/installing.html](https://pandoc.org/installing.html) |
| **Node.js** | 18 LTS or higher | [nodejs.org](https://nodejs.org) (download LTS) |
| **yq** | 4.x | Download `yq_windows_amd64.exe` → rename `yq.exe` → place in `C:\Program Files\Git\usr\bin\` from [github.com/mikefarah/yq/releases/latest](https://github.com/mikefarah/yq/releases/latest) |
| **envsubst** | Bundled with Git Bash | No install needed — comes with Git for Windows |

### Node.js packages (install once per clone)

Build dependencies are pinned in `package.json` / `package-lock.json`. After
cloning the engine or a scaffolded proposal repo, run once from the repo
root:

```bash
npm ci
```

`npm ci` reads the lockfile exactly — same versions every machine, every
time. Don't use `npm install` here; it can drift the lockfile.

### VS Code extensions (recommended)

| Extension ID | Purpose |
|---|---|
| `yzhang.markdown-all-in-one` | Markdown preview, shortcuts, TOC |
| `davidanson.vscode-markdownlint` | Lint Markdown as you type |
| `eamodio.gitlens` | Enhanced Git history and blame |
| `redhat.vscode-yaml` | YAML syntax for `proposal_config.yml` |

---

## Quick Start

### Option A: Interactive scaffolding (recommended)

```bash
# From the template repo root
bash scripts/scaffold/new_proposal.sh
```

Follow the prompts — enter RFP details, select sections, and optionally add custom sections. A fully structured proposal folder is generated and Git-initialized automatically.

### Option B: Preset-based scaffolding

```bash
# List available presets
bash scripts/scaffold/new_proposal.sh --list

# Scaffold from preset (still prompts for RFP metadata)
bash scripts/scaffold/new_proposal.sh --type sled_full
bash scripts/scaffold/new_proposal.sh --type sled_qualifications
bash scripts/scaffold/new_proposal.sh --type hed_research
bash scripts/scaffold/new_proposal.sh --type design_build
bash scripts/scaffold/new_proposal.sh --type ae_term_contract
```

### After scaffolding

```bash
cd proposal-rfp-XXXX-client-name

# Install Node packages
npm ci

# Install Git hooks
bash scripts/git/hooks/install_hooks.sh

# Load Git aliases (or add to ~/.bashrc for automatic loading)
source scripts/git/proposal-aliases.sh

# Fill in proposal metadata
code 00_admin/proposal_config.yml

# Push to GitHub
git remote add origin https://github.com/<your-github-username>/<repo-name>.git
git push -u origin main
```

---

## Folder Structure

```text
proposal-template/
│
├── 00_admin/                        # Internal — never submitted
│   ├── proposal_config.yml          # Single source of truth (gitignored)
│   ├── proposal_config.yml.example  # Copy → proposal_config.yml to start
│   ├── bid_no_bid.md                # Capture-phase decision record
│   ├── proposal_schedule.md         # Kickoff to submission timeline
│   ├── rfp_shred.md                 # RFP requirements decomposition
│   ├── win_themes.md                # Client hot buttons and discriminators
│   ├── color_team_reviews.md        # Pink/Red/Gold Team findings and resolutions
│   ├── pre_submission_gaps.md       # Final QC checklist before submission
│   ├── template_backlog.md          # Roadmap for future template improvements
│   ├── rfp_intake/                  # RFP parsing inputs (gitignored content)
│   │   ├── original_rfp/            # Primary RFP document(s) — shred input
│   │   ├── addendums/               # Addendums / revisions — shred input
│   │   └── attachments/             # Attachments, exhibits, spec refs — shred input
│   └── subconsultant_intake/        # Partner firm intake forms
│
├── 01_executive_summary/            # Proposal volumes (numbered by scaffold)
├── 02_technical_volume/
├── 03_management_volume/
├── 04_past_performance/
│   └── references/
├── 05_price_volume/
├── 06_attachments/
│   ├── figures/                     # PNG/SVG diagrams (tracked in Git)
│   ├── data/                        # Pricing spreadsheets (gitignored)
│   └── letters_of_support/          # Partner letters (gitignored)
│
├── scripts/
│   ├── git/
│   │   ├── proposal-aliases.sh      # Proposal Git shortcuts
│   │   └── hooks/
│   │       ├── pre-commit           # PLACEHOLDER audit + empty file check
│   │       └── install_hooks.sh     # Run once after clone
│   ├── publish/
│   │   ├── build_docx.sh            # Build all volumes → _output/
│   │   ├── build_single.sh          # Build one .md → .docx (rapid iteration)
│   │   ├── combine_volumes.sh       # Merge all volumes into submission file
│   │   ├── generate_reference_docx.js  # Generate firm-branded reference.docx
│   │   ├── post_process_tables.js   # Fix table column widths post-Pandoc
│   │   └── README.md                # Publish pipeline documentation
│   └── scaffold/
│       ├── new_proposal.sh          # Scaffold a new proposal interactively
│       ├── proposal_types/          # YAML presets (sled_full, hed_research, etc.)
│       ├── section_templates/       # Placeholder .md per section type
│       └── README.md                # Scaffolding documentation
│
├── templates/
│   ├── docx_reference/
│   │   └── reference.docx           # Firm-branded Pandoc reference (tracked in Git)
│   ├── docm_reference/              # Macro-enabled reference (experimental)
│   └── cover_page/
│       └── cover_page.md            # Cover page template (envsubst variables)
│
├── assets/
│   ├── logos/
│   │   └── YOUR_LOGO_PLACEHOLDER.png  # Firm logo (replace with actual logo)
│   └── brand/
│       └── brand_guidelines.md      # Colour, font, and margin reference
│
├── compliance_matrix.md             # RFP requirements → proposal section map
├── retrospectives/                  # Post-proposal lessons learned
├── .github/
│   ├── REPOSITORY_SETUP.md          # GitHub settings walkthrough
│   ├── ISSUE_TEMPLATE/              # Action item, review gate, RFP requirement
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── workflows/
│       └── proposal_ci.yml          # CI: lint + PLACEHOLDER audit + build check
├── .gitignore
├── .markdownlint.yml
├── package.json
└── README.md                        ← You are here
```

**Build output** (gitignored, overwritten on each build):

```text
_output/
├── vol_00_executive_summary.docx
├── vol_01_technical.docx
├── vol_02_management.docx
├── vol_03_past_performance.docx
├── vol_04_price.docx
└── FirmShortName_RFP-XXXX_Proposal_YYYYMMDD.docx   # Combined submission file
```

---

## Configuration

**File:** `00_admin/proposal_config.yml` (gitignored)

Copy the example file to get started:

```bash
cp 00_admin/proposal_config.yml.example 00_admin/proposal_config.yml
```

The config is the single source of truth for all proposal metadata. Every build script and the cover page template read from this file. Key sections:

| Section | Contents |
|---|---|
| `opportunity` | RFP title, number, client, due date, contract type and value |
| `firm` | Firm name, address, CAGE code, UEI |
| `contacts` | Proposal manager, principal investigator, capture manager |
| `strategy` | Win probability, discriminators, incumbent, competitors |
| `schedule` | Shipley gate dates (kickoff, shred, outline, pink/red/gold, production, submission) |

All values are exported as environment variables and substituted into the cover page and footer via `envsubst`. Re-run `generate_reference_docx.js` after changing the RFP number to update page footers:

```bash
node scripts/publish/generate_reference_docx.js --rfp "RFP-2025-001"
```

---

## Proposal Workflow

The workflow follows the Shipley methodology from capture through submission.

```text
Capture → Kickoff → Outline → Draft → Reviews → Production → Submit
```

### Phase 1: Capture

```bash
code 00_admin/bid_no_bid.md           # Evaluate strategic fit and win probability
```

### Phase 2: Kickoff

```bash
code 00_admin/rfp_shred.md            # Decompose RFP into discrete shall/must/should requirements
code 00_admin/win_themes.md           # Define client hot buttons and 3–4 win themes with proof points
code 00_admin/proposal_schedule.md    # Set gate dates (kickoff through submission)
code compliance_matrix.md             # Map each requirement → volume/section
prop-save "docs: RFP shred, win themes, schedule"
```

### Phase 3: Authoring

```bash
# Write content in each volume
code 01_executive_summary/executive_summary.md
code 02_technical_volume/technical_approach.md
# ... etc.

# Preview formatting during drafting
bash scripts/publish/build_single.sh 02_technical_volume/technical_approach.md --open

# Periodic commits
prop-checkpoint
prop-save "draft: technical approach - core solution"
```

Replace all `PLACEHOLDER` tokens as you write. The pre-commit hook will warn if any remain in narrative volumes (01–05).

### Phase 4: Reviews (Shipley Gates)

```bash
# Pink Team — storyboard/outline review
prop-tag v1.0-pink-team "Pink Team submission (YYYY-MM-DD)"
git push origin v1.0-pink-team
code 00_admin/color_team_reviews.md   # Log findings and resolutions

# Red Team — full draft review from evaluator perspective
prop-tag v2.0-red-team "Red Team package (YYYY-MM-DD)"

# Gold Team — final review and senior approval
prop-tag v3.0-gold-team "Gold Team approval (YYYY-MM-DD)"
```

### Phase 5: Production

```bash
# Build all volumes
bash scripts/publish/build_docx.sh --clean

# Verify no PLACEHOLDERs remain
grep -r "PLACEHOLDER" 0[1-5]_*/

# Final QC checklist
code 00_admin/pre_submission_gaps.md

# Combine into single submission file
bash scripts/publish/combine_volumes.sh

prop-save "prod: ready for submission"
```

### Phase 6: Submission

```bash
# Upload _output/FirmShortName_RFP-XXXX_Proposal_YYYYMMDD.docx to RFP portal

# Tag final submission
prop-tag v3.1-submitted "Submitted to [Client] (YYYY-MM-DD)"
git push origin v3.1-submitted
```

### Authoring workflow summary

| Phase | Activity | Key File |
|---|---|---|
| Capture | Bid/no-bid decision | `00_admin/bid_no_bid.md` |
| Kickoff | RFP shred, win themes | `00_admin/rfp_shred.md` · `win_themes.md` |
| Kickoff | Proposal schedule | `00_admin/proposal_schedule.md` |
| Outline | Compliance mapping | `compliance_matrix.md` |
| Draft | Author volumes | `01_*` through `05_*` |
| Pink Team | Storyboard review | `00_admin/color_team_reviews.md` |
| Red Team | Full draft review | `00_admin/color_team_reviews.md` |
| Gold Team | Final approval | `00_admin/color_team_reviews.md` |
| Production | Build and QC | `bash scripts/publish/build_docx.sh` |
| Production | Final gaps check | `00_admin/pre_submission_gaps.md` |
| Submission | Tag and archive | `prop-tag v3.1-submitted` |

---

## Build Pipeline

### Build commands

```bash
# Build all volumes → _output/
bash scripts/publish/build_docx.sh

# Options
bash scripts/publish/build_docx.sh --clean           # Clean _output/ before building
bash scripts/publish/build_docx.sh --volumes 1,2     # Build only specific volumes

# Build one file (fast iteration during drafting)
bash scripts/publish/build_single.sh 02_technical_volume/technical_approach.md
bash scripts/publish/build_single.sh 02_technical_volume/technical_approach.md --open

# Combine all volumes into one submission file
bash scripts/publish/combine_volumes.sh
bash scripts/publish/combine_volumes.sh --output "CustomName.docx"
```

### How the pipeline works

```text
.md source files
   ↓  envsubst → cover page variable substitution
   ↓  Pandoc (--reference-doc=templates/docx_reference/reference.docx)
       → applies firm styles, fonts, headers, footers, auto-TOC
raw .docx
   ↓  post_process_tables.js
       → locks all table column widths to 7.05" content area
final .docx → _output/
```

**Important:** Do not manually format the output `.docx` files — all styling must come from `reference.docx` or Markdown source. Manual formatting is overwritten on every rebuild.

### Output files

| File | Contents |
|---|---|
| `vol_00_executive_summary.docx` | 2–4 pages |
| `vol_01_technical.docx` | 10–25 pages |
| `vol_02_management.docx` | 8–15 pages |
| `vol_03_past_performance.docx` | 10–20 pages |
| `vol_04_price.docx` | 5–10 pages |
| `FirmShortName_RFP-XXXX_Proposal_YYYYMMDD.docx` | Combined submission |

The combined filename is auto-generated from `proposal_config.yml` values: `{firm.short_name}_{rfp_number}_{submission_date}.docx`.

---

## Git Aliases

Load once per session, or add to `~/.bashrc` for automatic loading:

```bash
source scripts/git/proposal-aliases.sh
```

### Workflow aliases

| Command | Description |
|---|---|
| `prop-save "message"` | Stage all and commit with message |
| `prop-checkpoint` | Auto-timestamped commit |
| `prop-tag v1.0-pink-team [msg]` | Tag a Shipley review gate milestone |
| `prop-tags` | List all milestone tags |
| `prop-undo` | Undo last commit, keep changes staged |
| `prop-discard` | Discard unstaged changes (prompts for confirmation) |

### Review and diff aliases

| Command | Description |
|---|---|
| `prop-diff [file]` | Word-level diff (readable for prose) |
| `prop-diff-tag <t1> <t2>` | Word diff between two milestone tags |
| `prop-log` | Clean commit history |
| `prop-log-files` | Commit log with file change stats |

### Status and analytics aliases

| Command | Description |
|---|---|
| `prop-status` | Repo status summary |
| `prop-wc` | Word count per volume |
| `prop-pages` | Estimated page count (≈250 words/page) |
| `prop-help` | Print full alias reference |

### Pre-commit hook

Install once per repo:

```bash
bash scripts/git/hooks/install_hooks.sh
```

The hook warns (non-blocking) before each commit if any of these are detected:

- `PLACEHOLDER` tokens remaining in narrative volumes (01–05)
- Empty section files (only YAML front matter, no body content)
- Unchecked compliance items in `compliance_matrix.md`
- Shell script syntax errors (if `shellcheck` is installed)

Use `git commit --no-verify` to bypass the hook when needed.

---

## Scaffolding

### Commands

```bash
# Interactive — prompts for all details
bash scripts/scaffold/new_proposal.sh

# From preset
bash scripts/scaffold/new_proposal.sh --type sled_full

# List available presets
bash scripts/scaffold/new_proposal.sh --list
```

### Available presets

| Preset ID | Use case |
|---|---|
| `sled_full` | State/Local/Municipal — comprehensive proposal |
| `sled_qualifications` | QBS (Qualifications-Based Selection) — no price volume |
| `hed_research` | Higher Education / Research institutions |
| `design_build` | Design-Build with construction period services |
| `ae_term_contract` | Architecture/Engineering term contracts |

### Available section types

| ID | Section Name |
|---|---|
| `executive_summary` | Executive Summary |
| `technical_approach` | Technical Approach |
| `management_plan` | Management Plan |
| `qualifications` | Qualifications / Firm Experience |
| `past_performance` | Past Performance / References |
| `staffing_plan` | Staffing Plan |
| `project_schedule` | Project Schedule |
| `price_volume` | Price / Fee Proposal |
| `subconsultant` | Subconsultant Information |
| `quality_control` | Quality Control |
| `geographic` | Geographic Location / Local Presence |
| `construction_services` | Construction Period Services |
| `appendices` | Appendices / Attachments |
| *(custom)* | Any name — prompted interactively, multiple allowed |

Each scaffolded section includes `PLACEHOLDER` tokens with APMP-aligned guidance comments indicating what content belongs in each area.

---

## Compliance and Requirements Tracking

### Documents

| Document | Purpose |
|---|---|
| `00_admin/rfp_shred.md` | Decompose RFP into discrete requirements (shall/must/should statements), key facts, pass/fail minimums, and evaluation criteria |
| `compliance_matrix.md` | Map each requirement → proposal volume/section → verification checkbox |
| `00_admin/bid_no_bid.md` | Capture-phase decision record (strategic fit, win probability, make/buy/team) |
| `00_admin/win_themes.md` | Client hot buttons + 3–4 win themes with proof points |
| `00_admin/proposal_schedule.md` | Kickoff → submission timeline with Shipley gate milestones |
| `00_admin/color_team_reviews.md` | Pink/Red/Gold Team findings, action items, and resolutions |
| `00_admin/pre_submission_gaps.md` | Final QC checklist — confirm all requirements addressed before submitting |

### Placeholder audit

Every scaffolded section contains `PLACEHOLDER` tokens marking content areas that require author input. Example:

```markdown
`PLACEHOLDER: Open with a crisp 2–3 sentence statement of the client's core challenge...`
```

**Audit locations:**

- **Pre-commit hook** — warns locally when staged files in narrative volumes still contain `PLACEHOLDER` tokens
- **CI/CD job** — counts and reports all remaining tokens on every push; outputs locations to the GitHub Actions job summary

### Compliance matrix

`compliance_matrix.md` links every RFP requirement to the proposal section that addresses it and includes a verification checkbox. The pre-commit hook warns if unchecked items remain at commit time.

---

## CI/CD Pipeline

**File:** `.github/workflows/proposal_ci.yml`

**Triggers:**

- Push to `main` (filtered to proposal file paths)
- Pull requests to `main`

**Path filter (push only):** `0[0-6]_**/*.md`, `compliance_matrix.md`, `scripts/publish/**`, `templates/**`

### Job 1: Markdown Lint

Runs `markdownlint-cli` against all `.md` files using `.markdownlint.yml`. Warns only — does not block build.

Notable rules disabled for proposal prose:

- `MD013` (line length)
- `MD033` (inline HTML — allows `<br>` in tables)
- `MD041` (first-line heading — allows YAML front matter)

### Job 2: PLACEHOLDER Audit

Counts unfilled `PLACEHOLDER` tokens in narrative volumes (01–05). Reports count and line-by-line locations in the GitHub Actions job summary. Warns only — does not block build.

### Job 3: Docx Build Check

Installs Pandoc and yq on the CI runner, creates a stub config (all `PLACEHOLDER` values replaced with `CI_STUB`), and runs the full `build_docx.sh` pipeline. **Fails if any build errors occur.** Uploads the output `.docx` files as artifacts (7-day retention) for inspection.

### Branch protection (optional)

After the first CI run, you can enforce passing checks before merge. See `.github/REPOSITORY_SETUP.md` for the full setup walkthrough.

---

## GitHub Template Setup

See [.github/REPOSITORY_SETUP.md](.github/REPOSITORY_SETUP.md) for the complete step-by-step guide including:

- Creating a new repo from this template
- Enabling the Template Repository setting
- Label setup
- Branch protection and required status checks
- Milestone tag conventions
- Issue template usage (action items, review gate findings, RFP requirement tracking)

---

## Branching, Commits, and Versioning

This project follows trunk-based development with Conventional Commits and Semantic Versioning.

### Branches

| Branch | Purpose |
|---|---|
| `main` | Trunk. Protected. All changes land via pull request. CI must pass before merge. |
| `feat/<slug>` | New feature or capability. |
| `fix/<slug>` | Bug fix. |
| `docs/<slug>` | Documentation-only changes. |
| `chore/<slug>` | Tooling, build, or housekeeping with no runtime effect. |
| `ci/<slug>` | CI/CD workflow changes. |
| `refactor/<slug>` | Code restructuring without behavior change. |

Keep branches short-lived. Rebase onto `main` before opening a PR to keep history linear. Delete the branch after merge.

### Commit messages ([Conventional Commits](https://www.conventionalcommits.org/))

```text
<type>(<optional scope>): <short imperative summary>

<optional body explaining the why>

<optional footer: BREAKING CHANGE, Refs #123, etc.>
```

Types: `feat`, `fix`, `docs`, `chore`, `ci`, `refactor`, `test`, `perf`, `build`.

Examples:

- `feat(scaffold): add design-build preset`
- `fix(publish): lock table column widths to 7.05in`
- `docs: document branch protection setup`
- `chore: initial commit — v0.0.1 kickoff`

Breaking changes append `!` to the type (`feat!: …`) and include a `BREAKING CHANGE:` footer.

### Versioning ([Semantic Versioning 2.0.0](https://semver.org/))

Version format: `MAJOR.MINOR.PATCH`.

| Bump | When |
|---|---|
| `MAJOR` | Incompatible changes to scaffold presets, config schema, or build output structure. |
| `MINOR` | New backwards-compatible capability (new preset, new script, new optional config field). |
| `PATCH` | Backwards-compatible fix (bug fix, typo, dependency patch). |

Pre-1.0 (`0.x.y`) signals the API is still in flux — minor bumps may introduce breaking changes. The `1.0.0` release will mark the first stable contract.

Every release:

1. Lands the change set on `main` via PR.
2. Updates `package.json` `version` field.
3. Moves the `## [Unreleased]` entries in `CHANGELOG.md` under a new `## [X.Y.Z] - YYYY-MM-DD` heading.
4. Is tagged as an annotated tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`.
5. Is pushed with the tag: `git push origin main && git push origin vX.Y.Z`.

Full step-by-step runbook (pre-flight checks, GitHub release creation, post-release verification): [docs/release-process.md](docs/release-process.md).

Shipley review gate tags (`v1.0-pink-team`, `v2.0-red-team`, `v3.0-gold-team`, `v3.1-submitted`) are per-proposal milestone tags created inside a scaffolded proposal repo — they are **not** releases of this template and do not follow SemVer.

### Pull requests

- One logical change per PR. If you can't describe it in one sentence, split it.
- Fill out the PR template. Link related issues with `Closes #N` or `Refs #N`.
- CI (lint, PLACEHOLDER audit, docx build) must be green.
- Squash-merge into `main` so trunk history stays one-commit-per-PR.

### Issues

Use the provided templates in `.github/ISSUE_TEMPLATE/`:

- **Action item** — general work tracking.
- **Review gate** — Pink/Red/Gold Team findings from a scaffolded proposal.
- **RFP requirement** — tracking a specific shall/must statement through to submission.

---

## Windows / Git Bash Notes

**HOME path** — if `~` resolves incorrectly in Git Bash, add to `~/.bashrc`:

```bash
export HOME=/c/Users/<your-username>
```

**Line endings** — suppress CRLF warnings:

```bash
git config core.autocrlf true
```

**Auto-load aliases on every terminal** — add to `~/.bashrc`:

```bash
source /c/Users/<your-username>/path/to/proposal-aliases.sh
```

**yq installation** — ensure the renamed `yq.exe` binary is in a directory on your `PATH` that Git Bash can access. `C:\Program Files\Git\usr\bin\` is the recommended location.
