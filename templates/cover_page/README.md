# Cover Page

The cover page is generated separately from the volume Markdown files and merged during final production.

## Files

| File | Description |
|---|---|
| `cover_page.md` | Markdown source for Pandoc-generated cover page |
| `cover_page_variables.yml` | YAML metadata injected into the cover page template |

## Cover Page Elements (SLED / HED best practice)

A compliant proposal cover page typically includes:

1. **Solicitation Number / RFP Number** — prominently displayed
2. **Solicitation Title** — full official title from the RFP
3. **Issued By** — agency / institution name
4. **Submitted By** — your firm name, address, contact
5. **Submission Date**
6. **PROPRIETARY notice** — if applicable
7. **Volume designation** — if multi-volume submission
8. Your firm logo and optionally the client's logo

## Usage

```bash
# Cover page is built automatically as part of full proposal build
bash scripts/publish/build_docx.sh

# Or build cover page standalone
bash scripts/publish/build_single.sh templates/cover_page/cover_page.md
```
