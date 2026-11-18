"""scripts/lib/ae_form_helpers.py

Cell-write and layout helpers for DGS-30-004 AE-form population. Wraps
openpyxl with a thin set of contracts that absorb the quirks of the DGS
template (merged cells, formula cells in templates, fixed-cell headers,
auto-fit row heights for wrapped text).

Public API:
    write_cell(ws, ref, val)
    fit_merged_rows(ws, *, chars_per_line=100, pt_per_line=13.5, min_chars=80)
    load_template(path) -> openpyxl.Workbook
    fill_dgs_header(ws, *, rfp, submitted_by, project_title, pc=None)
    save_workbook(wb, out_path) -> Path

Why this lives in scripts/lib/:
    populate_ae_forms.py and any future SF330-Part-2 / agency-specific
    form populator share the same template-wrangling primitives. Pulling
    them into a library keeps the populators readable cell-map files
    instead of mixed openpyxl + business-logic.

USAGE:
    from scripts.lib.ae_form_helpers import (
        write_cell, fit_merged_rows, load_template,
        fill_dgs_header, save_workbook,
    )

    wb = load_template(template_dir / "AE-1.xlsx")
    ws = wb["AE-1"]
    fill_dgs_header(ws, rfp="443882616",
                    submitted_by="Bowman, Foster & Associates, Inc.",
                    project_title="Term Contract for ME Engineering Services")
    write_cell(ws, "C8", "Bowman, Foster & Associates, Inc.")
    fit_merged_rows(ws)
    save_workbook(wb, out_dir / "AE-1_BFA.xlsx")
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import openpyxl
from openpyxl.styles import Alignment
from openpyxl.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet

# DGS-30-004 fixed header cell anchors.
# RFP number, submitting firm, project title, and project code (PC) live
# at the same coordinates on every AE-1..AE-6 sheet. Keep the constants
# co-located so a template revision only touches one place.
_DGS_HEADER_RFP = "AN3"
_DGS_HEADER_SUBMITTED_BY = "M5"
_DGS_HEADER_PROJECT_TITLE = "M6"
_DGS_HEADER_PROJECT_CODE = "AL6"


def write_cell(ws: Worksheet, ref: str, val: Any) -> None:
    """Write `val` to the top-left cell of a (possibly merged) range.

    Idempotent on empty values: when `val` is `None` or the empty string,
    the cell is left untouched. This preserves any formula or static text
    already in the template — the convention across DGS forms is that an
    untouched cell renders as blank.

    Notes:
        - To intentionally clear a templated cell, pass a single space
          (`" "`) — that survives the empty-check and overwrites.
        - The function does not validate that `ref` is the top-left of a
          merged range; openpyxl silently no-ops a write to a non-anchor
          merged cell, which matches the VT-script behavior.
        - Multi-line strings (containing `\\n`) are written as-is; openpyxl
          renders them as in-cell line breaks when the cell's
          `wrap_text` alignment is enabled (see `fit_merged_rows`).

    Args:
        ws: openpyxl Worksheet to write into.
        ref: A1-style cell reference (e.g., `"C8"`).
        val: Value to write. `None` and `""` are skipped; ints, floats,
            and strings are written verbatim.
    """
    if val is None or val == "":
        return
    ws[ref] = val


def fit_merged_rows(
    ws: Worksheet,
    *,
    chars_per_line: int = 100,
    pt_per_line: float = 13.5,
    min_chars: int = 80,
) -> None:
    """Expand row heights for long wrapped text in merged cells.

    Walk the worksheet's merged ranges; for any range that (a) spans 2+
    rows and (b) holds a string of `min_chars` or more, enable
    `wrap_text` and distribute enough vertical room across the merged
    rows to show all lines.

    The line-count estimate counts both implicit wrapping (length /
    chars_per_line) and explicit newlines. The wider of the two is used,
    so a long single-paragraph string and a multi-paragraph string both
    fit. Heights below 14pt (Calibri 11 default) are clamped to 14pt.

    Tuning:
        Default `chars_per_line=100` matches the C8:AS52 narrative box on
        DGS AE-6 (45 rows × 12.75pt at Calibri 11pt, ~7" content area).
        Override per-form when the merged box has different dimensions.

    Args:
        ws: openpyxl Worksheet to post-process. Mutates in place.
        chars_per_line: Approximate characters that fit per line at the
            template's font size and column width.
        pt_per_line: Vertical space per text line in points.
        min_chars: Minimum string length to trigger row expansion.
            Shorter strings are left at their template-default row height.
    """
    for merge_range in ws.merged_cells.ranges:
        cell = ws.cell(merge_range.min_row, merge_range.min_col)
        val = cell.value
        if not isinstance(val, str) or len(val) < min_chars:
            continue

        n_rows = merge_range.max_row - merge_range.min_row + 1
        if n_rows < 2:
            continue

        cell.alignment = Alignment(wrap_text=True, vertical="top")

        wrap_lines = math.ceil(len(val) / chars_per_line)
        explicit_lines = val.count("\n") + 1
        n_lines = max(wrap_lines, explicit_lines) + 1
        row_height = max(14.0, (n_lines * pt_per_line) / n_rows)

        for r in range(merge_range.min_row, merge_range.max_row + 1):
            ws.row_dimensions[r].height = row_height


def load_template(path: Path | str) -> Workbook:
    """Open a template `.xlsx` for population.

    Args:
        path: Path to the template workbook. Must exist.

    Returns:
        An openpyxl Workbook opened from `path`. Caller is responsible
        for selecting the correct sheet and saving the result with
        `save_workbook`.

    Raises:
        FileNotFoundError: `path` does not exist.
    """
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"AE-form template not found: {p}")
    return openpyxl.load_workbook(p)


def fill_dgs_header(
    ws: Worksheet,
    *,
    rfp: str,
    submitted_by: str,
    project_title: str,
    pc: str | None = None,
) -> None:
    """Fill the four header cells common to every DGS-30-004 AE form.

    DGS template anchors:
        - AN3: RFP number
        - M5:  submitting firm name
        - M6:  project title
        - AL6: project code (optional)

    Args:
        ws: openpyxl Worksheet (the AE-N sheet, not the workbook).
        rfp: RFP number string. Required; empty raises.
        submitted_by: Firm submitting the form. Required; empty raises.
        project_title: Project / contract title. Required; empty raises.
        pc: Optional project code. `None` or `""` leaves AL6 untouched.

    Raises:
        ValueError: Any required argument is empty or whitespace-only.
    """
    for label, value in (
        ("rfp", rfp),
        ("submitted_by", submitted_by),
        ("project_title", project_title),
    ):
        if not value or not value.strip():
            raise ValueError(
                f"fill_dgs_header: {label!r} is required and must be non-empty."
            )

    write_cell(ws, _DGS_HEADER_RFP, rfp)
    write_cell(ws, _DGS_HEADER_SUBMITTED_BY, submitted_by)
    write_cell(ws, _DGS_HEADER_PROJECT_TITLE, project_title)
    if pc:
        write_cell(ws, _DGS_HEADER_PROJECT_CODE, pc)


def save_workbook(wb: Workbook, out_path: Path | str) -> Path:
    """Save `wb` to `out_path`, replacing any existing file at that path.

    Creates the parent directory tree if missing. Returns the resolved
    output path so callers can log or chain on it.

    Args:
        wb: openpyxl Workbook to save.
        out_path: Target `.xlsx` path. Parent directory is created if
            absent. An existing file at this path is overwritten.

    Returns:
        The resolved `Path` that was written.
    """
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists():
        p.unlink()
    wb.save(p)
    return p
