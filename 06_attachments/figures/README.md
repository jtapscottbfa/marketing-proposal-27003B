# Figures

Place all figures, diagrams, and charts here as PNG or SVG files.

> Files here are assembled separately from the narrative build. Depending on pursuit needs, they may be folded into the compiled document or submitted as standalone attachments/appendices.

## Naming Convention

```
fig_01_design_deliverable.png
fig_02_project_locations.png
fig_03_org_chart.png
fig_04_qaqc_review.png
fig_05_project_schedule.png
fig_XX_<descriptive_name>.<ext>
```

## Files in This Folder

Figures are referenced from the narrative with **descriptive captions (no "Figure N"
numbers)** so graphics can be added or removed without renumbering. Drop a pending
file here and it renders on the next build. ✅ = in place; ⏳ = pending.

| File | Description | Used In | Status |
|---|---|---|---|
| `fig_cover.jpg` | Cover banner — OIT building exterior (downsized) | `templates/cover_page/cover_page.md` | ✅ |
| `fig_exec_hero.jpg` | Hero banner — MV feeder install, McGuire VAMC | `01_executive_summary/executive_summary.md` | ✅ |
| `fig_mech_deliverables.jpg` | 2×2 montage — mech plan, details, sequences of operations | `02_technical_volume/01_technical_approach.md §2.1` | ✅ |
| `fig_01_design_deliverable.png` | Electrical one-line (redacted) | `02_technical_volume/01_technical_approach.md §3.0` | ✅ |
| `fig_02_project_locations.png` | VA / Hampton Roads locations map (build from `project_locations.*`) | `02_technical_volume/02_annex_a_sector_capability_matrix.md` | ⏳ export from data below |
| `fig_03_org_chart.png` | BFA organization chart | `03_management_volume/01_management_approach.md §1.3` | ✅ |
| `fig_design_process.png` | Project-delivery process flow | `03_management_volume/04_annex_c_project_plan.md §1` | ✅ |
| `fig_05_project_schedule.png` | Project schedule / milestone Gantt | `03_management_volume/04_annex_c_project_plan.md §2` | ✅ |
| `fig_s1_school.jpg` | Rena B. Wright school exterior (K-12) | `04_past_performance/references/ref_s1_chesapeake_rena_wright.md` | ✅ |
| `fig_s1_install.jpg` | Rena B. Wright rooftop-unit crane lift | `04_past_performance/references/ref_s1_chesapeake_rena_wright.md` | ✅ |
| `fig_06_mcguire_generator_plant.jpg` | Completed generator plant photo | `04_past_performance/references/ref_v1_mcguire_vamc_generator.md` | ✅ |
| `fig_mcguire_aerial.jpg` | Aerial — generator building delivery | `04_past_performance/references/ref_v1_mcguire_vamc_generator.md` | ✅ |

> Until a pending file exists, Pandoc skips that figure with a non-fatal warning, and
> the table post-processor leaves figure containers unstyled (no burgundy border).

### Project-locations map data (source for `fig_02_project_locations.png`)

- `project_locations.csv` — 26 projects with lat/lon, contract value, sector. Regenerate with `python scripts/publish/gen_project_locations.py`.
- `project_locations.kml` — same data as Google Earth placemarks, color-coded by sector.

To build the map/heat map for `fig_02`:
- **kepler.gl** (true heat map): upload the CSV → add a *Heatmap* layer → set lat/lon, weight = `value_usd` → screenshot/export PNG.
- **Google My Maps**: import CSV, set lat/lon columns, style points by `sector` (density view, not a true heat map).
- **Google Earth Pro**: open the KML (placemarks; no native heat map).
- **QGIS**: load the CSV as a delimited-text layer → Heatmap renderer.

### Uploaded source assets retained

- `richmond_generator_*.jpg`, `OIT Space.png` — full-res photo originals; downsized derivatives above are what the build embeds.
- `Org Chart BFA.png`, `Gantt2.png`, `process flow.png` — originals copied to their `fig_*` names.
- `mech plan.png`, `mech_details.png`, `soo.png`, `soo2.png` — composited into `fig_mech_deliverables.jpg`.
- `Rena B Wright/` — full photo set; `fig_s1_school.jpg` (exterior) and `fig_s1_install.jpg` (IMG_0681 crane lift) are the two selected and downsized.

## Export Settings

- **Format:** PNG (preferred) or SVG
- **Resolution:** Minimum 150 DPI for print-quality .docx output
- **Dimensions:** Max width ~6.5 inches at final document scale (fits within 1" margins on US Letter)
