# Proposal Scaffolding Tool

Generates a new proposal folder structure from scratch based on the sections you select.

---

## Usage

### Interactive (quick new proposal)
```bash
bash scripts/scaffold/new_proposal.sh
```
The script will prompt you for:
1. RFP title, number, client, due date, output location
2. Which sections to include (numbered checklist)
3. Section order
4. Any custom sections (named on the fly, multiple allowed)

### From a preset (repeatable proposal type)
```bash
bash scripts/scaffold/new_proposal.sh --type sled_full
bash scripts/scaffold/new_proposal.sh --type sled_qualifications
bash scripts/scaffold/new_proposal.sh --type hed_research
bash scripts/scaffold/new_proposal.sh --type design_build
```

### List available presets
```bash
bash scripts/scaffold/new_proposal.sh --list
```

---

## Available Sections

| ID | Name |
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
| *(custom)* | Any name — prompted interactively |

---

## Presets

Presets live in `scripts/scaffold/proposal_types/`. Each is a simple YAML file:

```yaml
description: "My proposal type description"
sections:
  - executive_summary
  - technical_approach
  - qualifications
  - past_performance
  - price_volume
```

To create a new preset — copy any existing `.yml` file, rename it, adjust the sections list.

---

## What Gets Generated

For a proposal named `proposal-rfp-2025-001-city-of-norfolk/`:

```
proposal-rfp-2025-001-city-of-norfolk/
├── 00_admin/
│   └── proposal_config.yml     ← pre-filled with your inputs
├── 01_executive_summary/
│   └── executive_summary.md    ← branded placeholder
├── 02_technical_approach/
│   └── technical_approach.md
├── 03_qualifications/          ← only if selected
│   └── qualifications.md
├── ...
├── XX_attachments/
│   ├── figures/
│   ├── data/
│   └── letters_of_support/
├── scripts/                    ← full proposal pipeline
├── templates/                  ← reference.docx
├── assets/                     ← logo, brand
├── compliance_matrix.md
└── .gitignore
```

Folders are auto-numbered in the order you selected.
