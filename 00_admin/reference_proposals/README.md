# 00_admin/reference_proposals/

Drop prior proposal PDFs (or `.txt` files) here, then run:

```bash
bash scripts/proposal_digest.sh
```

The script extracts every project / past-performance entry from each
source proposal, scores the resulting pool against the active RFP's win
themes and evaluation criteria, and writes a ranked **Project Selector**
to `00_admin/project_selector.md`.

## What gets created

For each source PDF dropped into this directory:

```
reference_proposals/
├── proposal-2023-vamc.pdf            # your input (root)
└── proposal-2023-vamc/               # ← created by the script
    ├── proposal-2023-vamc.pdf        # source moved here after digest
    └── project_digest.md             # typed digest (schema below)
```

Plus, across all digests:

- `_claimed_clients.md` — attestation checklist of every unique client
  name extracted. **Unchecked entries cannot be referenced in the active
  pursuit's narrative until verified.** (Closes DISC-19.)
- `00_admin/project_selector.md` — ranked alignment matrix mapping each
  project to win themes and tier (Lead / Supporting / Skip).

## project_digest.md schema

Each project record is a YAML frontmatter block followed by a markdown
body. Records are separated by blank lines.

```markdown
---
id: "PROJ-001"
name: "Hampton VAMC HVAC Conversion"
client: "Department of Veterans Affairs"
client_type: "federal"
year_completed: "2019"
contract_value: "[VERIFY]"
contract_size: "medium"
delivery: "design-bid-build"
discipline_tags: ["mechanical", "electrical", "BAS"]
building_type_tags: ["healthcare", "government"]
source_proposal: "proposal-2023-vamc.pdf"
---

**Scope Summary**

[2–3 sentence description of what was designed and why.]

**Notable Aspects**

- [discriminating detail — certifications, awards, measurable outcomes]
- [bullet]

**Raw Excerpt**

> [verbatim paragraph from source proposal — copy into pursuit narrative
> as starting material, then tailor]
```

### Field reference

| Field | Type | Notes |
|---|---|---|
| `id` | string | Sequential — `PROJ-001`, `PROJ-002`, … per source proposal |
| `name` | string | Project name as it appears in source proposal |
| `client` | string | Client / owner organization. Goes into `_claimed_clients.md` |
| `client_type` | enum | `higher_ed` / `state_local` / `federal` / `private` / `healthcare` / `k12` / `military` |
| `year_completed` | string | `YYYY` or `[VERIFY]` |
| `contract_value` | string | USD amount or `[VERIFY]` |
| `contract_size` | enum | `small` (<$500K) / `medium` ($500K–$2M) / `large` (>$2M) / `unknown` |
| `delivery` | enum | `design-bid-build` / `design-build` / `CM-at-risk` / `term-contract` / `indefinite-delivery` / `other` |
| `discipline_tags` | list[string] | mechanical, electrical, plumbing, BAS, commissioning, fire-protection, civil, structural, etc. |
| `building_type_tags` | list[string] | higher-ed, k12, healthcare, laboratory, office, residential, athletic, historic, etc. |
| `source_proposal` | string | Filename of the source PDF |

## `[VERIFY]` markers

Any field whose source-document value is unclear, missing, or ambiguous is
marked with the literal string `[VERIFY]`. The `populate_ae_forms.py`
pre-flight (ARCH-02) and `sanity_check.py` publish gate (ARCH-05) both
refuse to ship a docx that draws on a `[VERIFY]`-tagged record. Resolve
each marker by editing the digest manually before referencing the project
in narrative.

## Re-running the script

| Command | Behavior |
|---|---|
| `bash scripts/proposal_digest.sh` | Digest all new PDFs in this dir, then score |
| `bash scripts/proposal_digest.sh --digest-only` | Extract projects, skip scoring |
| `bash scripts/proposal_digest.sh --score-only` | Re-score using existing digests (e.g., after adding new win themes) |
| `bash scripts/proposal_digest.sh --file <path>` | Digest one specific file (does not score) |

The script is idempotent for digestion — if `<slug>/project_digest.md`
already exists, that source is skipped. Delete the digest file to force
re-extraction.
