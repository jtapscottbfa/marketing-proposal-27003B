# Logos

Place firm and client logo files here.

## Required Files

| File | Description | Status |
|---|---|---|
| `YOUR_LOGO_PLACEHOLDER.png` | Your firm's primary logo (PNG, transparent background) | `PLACEHOLDER — replace` |
| `YOUR_LOGO_PLACEHOLDER.svg` | SVG version for vector quality in docx | `PLACEHOLDER — replace` |
| `CLIENT_LOGO_PLACEHOLDER.png` | Client/agency logo for cover page (if permitted by RFP) | `PLACEHOLDER — obtain from RFP or agency website` |

## Specs for Pandoc / docx integration

- **Format:** PNG with transparent background (preferred) or SVG
- **Resolution:** 300 DPI minimum
- **Cover page logo:** ~2 inches wide at final print size
- The `scripts/publish/build_docx.sh` script references `assets/logos/YOUR_LOGO_PLACEHOLDER.png`  
  Update the filename in that script after replacing this placeholder.
