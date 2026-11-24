# Publish Scripts

These scripts convert Markdown source files to `.docx` deliverables via Pandoc.

---

## Prerequisites

Install once, globally:

```bash
# macOS
brew install pandoc yq gettext
brew link --force gettext   # makes envsubst available in PATH

# Ubuntu / Debian
sudo apt-get install pandoc gettext-base
sudo wget -qO /usr/local/bin/yq \
  https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64
sudo chmod +x /usr/local/bin/yq

# Verify
pandoc --version
yq --version
envsubst --version
```

---

## Scripts

### `build_docx.sh` — Build all volumes

```bash
bash scripts/publish/build_docx.sh               # All volumes
bash scripts/publish/build_docx.sh --clean        # Clean _output/ first, then build all
bash scripts/publish/build_docx.sh --volumes 1,2  # Build only Vol I and Vol II
```

Output: `_output/vol_0X_<name>.docx` — one file per volume.

---

### `build_single.sh` — Build one file (fast iteration)

```bash
bash scripts/publish/build_single.sh 02_technical_volume/technical_approach.md
bash scripts/publish/build_single.sh 01_executive_summary/executive_summary.md --open
```

Use during drafting to quickly preview a section in Word without rebuilding everything.

---

### `combine_volumes.sh` — Merge all volumes into submission file

```bash
bash scripts/publish/combine_volumes.sh
bash scripts/publish/combine_volumes.sh --output "MyFirm_RFP-2025-001_Proposal.docx"
```

Output: `_output/<FirmShortName>_<RFP#>_Proposal_<YYYYMMDD>.docx`

Run after Gold Team approval, before final QC and submission.

---

## Output Directory

All build output goes to `_output/` (gitignored). Files are overwritten on each build.

```
_output/
├── vol_00_executive_summary.docx
├── vol_01_technical.docx
├── vol_02_management.docx
├── vol_03_past_performance.docx
├── vol_04_price.docx
└── MyFirm_RFP-2025-001_Proposal_20251015.docx   ← combined submission
```

---

## Styling the Reference Doc

All visual styles (fonts, colours, heading sizes, headers/footers) are controlled by
`templates/docx_reference/reference.docx`. See `templates/docx_reference/README.md`
for setup instructions.

**Rule:** Never manually format the output .docx. Fix the style in `reference.docx` and rebuild.

---

## Pandoc Markdown Extensions Used

| Extension | Purpose |
|---|---|
| `+smart` | Smart quotes, em-dashes, ellipses |
| `+yaml_metadata_block` | YAML front matter for document metadata |
| `--table-of-contents` | Auto-generated TOC |
| `--number-sections` | Numbered headings (1.0, 1.1, 2.0, etc.) |
| `--resource-path` | Resolves relative image paths from repo root |

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `pandoc: command not found` | Install pandoc: `brew install pandoc` |
| `yq: command not found` | Install yq: `brew install yq` |
| `envsubst: command not found` | Install gettext: `brew install gettext && brew link --force gettext` |
| Images not rendering in docx | Check `resource-path` and that image exists in `06_attachments/figures/` |
| Styles not applying | Verify `templates/docx_reference/reference.docx` is branded and saved |
| Config not found | Copy `00_admin/proposal_config.yml.example` → `proposal_config.yml` and fill it in |
