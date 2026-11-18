# docx_reference

This folder holds the **Pandoc reference document** (`reference.docx`) — the master Word file
whose styles are used when building all proposal volumes via `scripts/publish/build_docx.sh`.

## How It Works

Pandoc's `--reference-doc` flag extracts styles from this file and applies them to generated output.
The content of reference.docx is ignored; only the named styles matter.

## Setup (First Time)

1. Generate a base reference.docx:
   ```bash
   pandoc --print-default-data-file reference.docx > templates/docx_reference/reference.docx
   ```
2. Open `reference.docx` in Microsoft Word.
3. Modify the following named styles to match your brand (`assets/brand/brand_guidelines.md`):
   - `Heading 1`, `Heading 2`, `Heading 3`
   - `Normal` (body text)
   - `Table`, `Table Header`
   - `Caption`
   - `Header`, `Footer`
   - `Title`, `Subtitle` (for cover page)
4. Save and close. Do NOT add content — styles only.
5. Commit `reference.docx` to the repo.

## Files

| File | Description |
|---|---|
| `reference.docx` | `PLACEHOLDER — Generate and brand this file (see Setup above)` |

## ⚠️ Important

- reference.docx is a **binary file**. Git tracks it but cannot diff it meaningfully.
- When you update brand styles, commit with a clear message: `git commit -m "style: update heading colours to match new brand palette"`
