# GitHub Repository Setup Guide

This document covers the one-time GitHub settings you should configure
when creating a new proposal repository from this template.

---

## 1. Create Repository from Template

```bash
# Option A: GitHub CLI (recommended)
gh repo create my-proposal-rfp-2025-001 \
  --template your-org/proposal-template \
  --private \
  --description "Proposal: [RFP Title] — [Agency] — Due [Date]"

# Option B: GitHub web UI
# → Use this repository as a template → Create new repository
# Set visibility to PRIVATE (proposals contain sensitive commercial data)
```

### After cloning the new repo — remove engine-internal content

The template carries a `docs/` folder containing engine development history
(retrospectives, roadmap, architecture notes). This is not part of your
pursuit and should be removed from the child repo:

```bash
git clone git@github.com:your-org/my-proposal-rfp-2025-001.git
cd my-proposal-rfp-2025-001
rm -rf docs/
git add -A && git commit -m "chore: remove engine-internal docs/"
```

If you scaffold via `scripts/scaffold/new_proposal.sh` instead of GitHub's
template flow, `docs/` is not copied and this step is unnecessary.

---

## 2. Repository Settings (GitHub Web UI)

Navigate to **Settings** for your new repository and configure:

### General

| Setting | Recommended Value | Reason |
|---|---|---|
| Visibility | **Private** | Proposals are confidential commercial documents |
| Default branch | `main` | Industry standard |
| Wikis | Disable | Not needed; all docs are in the repo |
| Issues | **Enable** | Used for RFP shred tasks and action items |
| Projects | **Enable** | Optional: use for proposal schedule Kanban |
| Discussions | Disable | Not needed for solo author |
| Allow merge commits | Enable | Preferred for proposal history |
| Allow squash merging | Disable | Preserve full commit history for audit trail |
| Allow rebase merging | Disable | Keep history linear and readable |
| Automatically delete head branches | Enable | Keeps repo clean |

### Branch Protection — `main`

Navigate to **Settings → Branches → Add branch ruleset** for `main`:

| Rule | Setting |
|---|---|
| Require pull request before merging | Optional for solo author; enable if adding reviewers |
| Require status checks to pass | Enable after first CI run: add `markdown-lint`, `placeholder-audit`, `build-check` |
| Do not allow bypassing the above settings | Disable (solo author needs direct push) |
| Lock branch | Disable during authoring; **enable after Gold Team** |

### Secrets & Variables

Navigate to **Settings → Secrets and variables → Actions**:

No secrets are required by default. If you add external integrations (e.g., notifications), add them here rather than hardcoding in workflow files.

---

## 3. GitHub Projects (Optional — Proposal Schedule Board)

If you want a visual Kanban for the proposal schedule:

1. Go to **Projects → New project → Board**
2. Name it: `[RFP Short Name] Proposal Schedule`
3. Create columns:
   - `Backlog`
   - `In Progress`
   - `In Review`
   - `Done`
4. Create Issues from `00_admin/proposal_schedule.md` milestones and add them to the board

---

## 4. Labels Setup

Create these labels in **Settings → Labels** (delete defaults you don't need):

| Label | Colour | Description |
|---|---|---|
| `rfp-requirement` | `#0075ca` | Tracks individual RFP requirements |
| `action-item` | `#e4e669` | Proposal action items |
| `review-gate` | `#d93f0b` | Pink / Red / Gold Team gates |
| `needs-author` | `#cfd3d7` | Awaiting content author |
| `in-review` | `#0075ca` | Under reviewer evaluation |
| `resolved` | `#0e8a16` | Finding addressed and verified |
| `blocked` | `#b60205` | Blocked — needs decision |
| `volume-i` | `#bfd4f2` | Technical Volume |
| `volume-ii` | `#bfd4f2` | Management Volume |
| `volume-iii` | `#bfd4f2` | Past Performance Volume |
| `volume-iv` | `#bfd4f2` | Price Volume |

---

## 5. Install Git Hooks Locally

After cloning:

```bash
bash scripts/git/hooks/install_hooks.sh
source scripts/git/proposal-aliases.sh
```

---

## 6. Milestone Tags Convention

Use annotated tags for review gate snapshots:

```bash
prop-tag v0.1-outline      "Annotated outline complete"
prop-tag v0.2-pink-team    "Pink Team package — YYYY-MM-DD"
prop-tag v1.0-red-team     "Red Team package — YYYY-MM-DD"
prop-tag v2.0-gold-team    "Gold Team package — YYYY-MM-DD"
prop-tag v3.0-submission   "Final submission — YYYY-MM-DD HH:MM TZ"
```

Push tags to GitHub:
```bash
git push origin --tags
```

---

## 7. Enable as a GitHub Template Repository

Since you want to spin up new proposals from this template with one click:

1. Go to **Settings → General**
2. Under **Template repository**, check ✅ **"Template repository"**
3. Save

From now on, anyone in your org can go to the template repo and click **"Use this template" → "Create a new repository"** to spin up a new branded proposal repo in seconds — with all scripts, folder structure, and your firm styles pre-wired.

### New Proposal Quickstart (after template is enabled)

```bash
# 1. On GitHub: click "Use this template" → name it e.g. "proposal-rfp-2025-cityofva"
# 2. Clone it
git clone git@github.com:your-org/proposal-rfp-2025-cityofva.git
cd proposal-rfp-2025-cityofva

# 3. Load aliases and install hooks
source scripts/git/proposal-aliases.sh
bash scripts/git/hooks/install_hooks.sh

# 4. Configure the opportunity
cp 00_admin/proposal_config.yml.example 00_admin/proposal_config.yml
# Edit proposal_config.yml with RFP details

# 5. Generate reference.docx with this proposal's RFP number in the footer
node scripts/publish/generate_reference_docx.js --rfp "RFP-2025-001"

# 6. Begin authoring
prop-save "init: configured proposal_config.yml for RFP-2025-001"
prop-tag v0.0-kickoff "Proposal repo initialised"
```

### What carries over from the template

Every new repo created from this template inherits:
- ✅ Full folder structure and all placeholder `.md` files
- ✅ Firm-branded `scripts/` (aliases, hooks, publish pipeline)
- ✅ GitHub Issue templates and PR template
- ✅ GitHub Actions CI workflow
- ✅ `.gitignore` and `.markdownlint.yml`
- ✅ `assets/logos/firm_logo.png`

What is **NOT** carried over (correct behaviour):
- ❌ `00_admin/proposal_config.yml` (gitignored — you fill it in fresh per proposal)
- ❌ `templates/docx_reference/reference.docx` (regenerated per proposal with correct RFP number via `generate_reference_docx.js`)
- ❌ `_output/` (gitignored build output)

---

## 8. Repository Description & Topics

In the repository **About** section (top right of repo home):

- **Description:** `Proposal: [RFP Title] | [Agency] | Due [YYYY-MM-DD]`
- **Topics:** `proposal`, `rfp`, `[state-abbreviation]`, `[agency-type]`, `[year]`
- **Website:** Leave blank (or link to the agency's procurement portal)
