"""Tests for scripts/lib/ae_form_helpers.py

Run from engine root:
    python -m unittest scripts.lib.test_ae_form_helpers -v
or with pytest:
    pytest scripts/lib/test_ae_form_helpers.py -v
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import openpyxl

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.lib.ae_form_helpers import (  # noqa: E402
    fill_dgs_header,
    fit_merged_rows,
    load_template,
    save_workbook,
    write_cell,
)


def _new_sheet():
    """Fresh workbook + active sheet for test isolation."""
    wb = openpyxl.Workbook()
    return wb, wb.active


class WriteCellTests(unittest.TestCase):
    def test_writes_string(self):
        _, ws = _new_sheet()
        write_cell(ws, "C8", "Acme Engineering, Inc.")
        self.assertEqual(ws["C8"].value, "Acme Engineering, Inc.")

    def test_writes_int(self):
        _, ws = _new_sheet()
        write_cell(ws, "P41", 5)
        self.assertEqual(ws["P41"].value, 5)

    def test_skips_none(self):
        _, ws = _new_sheet()
        ws["C8"] = "preserve me"
        write_cell(ws, "C8", None)
        self.assertEqual(ws["C8"].value, "preserve me")

    def test_skips_empty_string(self):
        _, ws = _new_sheet()
        ws["C8"] = "preserve me"
        write_cell(ws, "C8", "")
        self.assertEqual(ws["C8"].value, "preserve me")

    def test_writes_single_space_to_force_clear(self):
        # Single space is the documented escape hatch for clearing a cell.
        _, ws = _new_sheet()
        ws["C8"] = "old value"
        write_cell(ws, "C8", " ")
        self.assertEqual(ws["C8"].value, " ")

    def test_writes_multiline_string(self):
        # Multi-line text written as-is; renderer enables wrap_text downstream.
        _, ws = _new_sheet()
        text = "First line.\nSecond line.\nThird line."
        write_cell(ws, "C8", text)
        self.assertEqual(ws["C8"].value, text)

    def test_writes_literal_na_string(self):
        # The content_library convention is to leave cells empty for "no data";
        # but if a value of "N/A" reaches write_cell (e.g., a parent_addr field
        # that's intentionally N/A on the form), it must be written verbatim
        # rather than treated as empty.
        _, ws = _new_sheet()
        write_cell(ws, "AL22", "N/A")
        self.assertEqual(ws["AL22"].value, "N/A")


class FitMergedRowsTests(unittest.TestCase):
    def test_short_text_in_merged_range_left_alone(self):
        _, ws = _new_sheet()
        ws.merge_cells("A1:A4")
        ws["A1"] = "short"
        original_height = ws.row_dimensions[1].height
        fit_merged_rows(ws)
        self.assertEqual(ws.row_dimensions[1].height, original_height)

    def test_single_row_merge_not_expanded(self):
        # Horizontal-only merge gets no row expansion (n_rows < 2 short-circuit).
        _, ws = _new_sheet()
        ws.merge_cells("A1:E1")
        ws["A1"] = "x" * 200
        fit_merged_rows(ws)
        self.assertIsNone(ws.row_dimensions[1].height)

    def test_long_text_in_multi_row_merge_expands(self):
        _, ws = _new_sheet()
        ws.merge_cells("A1:A4")
        ws["A1"] = "x" * 400  # ~4 wrapped lines @ 100 chars/line
        fit_merged_rows(ws)
        # Each of the 4 merged rows gets ≥14pt height.
        for r in range(1, 5):
            self.assertGreaterEqual(ws.row_dimensions[r].height, 14.0)

    def test_long_text_enables_wrap_text(self):
        _, ws = _new_sheet()
        ws.merge_cells("A1:A4")
        ws["A1"] = "x" * 400
        fit_merged_rows(ws)
        self.assertTrue(ws["A1"].alignment.wrap_text)
        self.assertEqual(ws["A1"].alignment.vertical, "top")

    def test_explicit_newlines_drive_height_when_above_min_chars(self):
        # 100 chars across 8 short lines: implicit wrap @ default 100ch
        # would say "1 line", but explicit \n line count is 8. The function
        # must use max(wrap_lines, explicit_lines), so heights get set.
        _, ws = _new_sheet()
        ws.merge_cells("A1:A8")
        # 8 lines, each ~12 chars: 8×13 - 1 (last \n) = 103 chars total.
        ws["A1"] = "\n".join(f"line {i:>2}xxxxx" for i in range(1, 9))
        self.assertGreaterEqual(len(ws["A1"].value), 80)
        fit_merged_rows(ws)
        # Heights set on every merged row.
        for r in range(1, 9):
            self.assertIsNotNone(ws.row_dimensions[r].height)
            self.assertGreaterEqual(ws.row_dimensions[r].height, 14.0)

    def test_below_min_chars_threshold_skipped(self):
        # Default min_chars=80; a 79-char string in a multi-row merge is
        # left alone. (`"x" * 79`)
        _, ws = _new_sheet()
        ws.merge_cells("A1:A4")
        ws["A1"] = "x" * 79
        fit_merged_rows(ws)
        self.assertIsNone(ws.row_dimensions[1].height)

    def test_min_chars_override_works(self):
        _, ws = _new_sheet()
        ws.merge_cells("A1:A4")
        ws["A1"] = "x" * 50
        fit_merged_rows(ws, min_chars=40)
        self.assertGreaterEqual(ws.row_dimensions[1].height, 14.0)


class FillDgsHeaderTests(unittest.TestCase):
    def test_writes_required_anchors(self):
        _, ws = _new_sheet()
        fill_dgs_header(
            ws,
            rfp="443882616",
            submitted_by="Acme Engineering",
            project_title="Term Contract for ME Services",
        )
        self.assertEqual(ws["AN3"].value, "443882616")
        self.assertEqual(ws["M5"].value, "Acme Engineering")
        self.assertEqual(ws["M6"].value, "Term Contract for ME Services")

    def test_pc_optional(self):
        _, ws = _new_sheet()
        fill_dgs_header(
            ws, rfp="X", submitted_by="Y", project_title="Z",
        )
        # AL6 untouched when pc not provided.
        self.assertIsNone(ws["AL6"].value)

    def test_pc_when_provided_is_written(self):
        _, ws = _new_sheet()
        fill_dgs_header(
            ws, rfp="X", submitted_by="Y", project_title="Z", pc="PC-123",
        )
        self.assertEqual(ws["AL6"].value, "PC-123")

    def test_empty_required_field_raises(self):
        _, ws = _new_sheet()
        with self.assertRaisesRegex(ValueError, "rfp"):
            fill_dgs_header(ws, rfp="", submitted_by="Y", project_title="Z")
        with self.assertRaisesRegex(ValueError, "submitted_by"):
            fill_dgs_header(ws, rfp="X", submitted_by="   ", project_title="Z")
        with self.assertRaisesRegex(ValueError, "project_title"):
            fill_dgs_header(ws, rfp="X", submitted_by="Y", project_title="")


class LoadTemplateTests(unittest.TestCase):
    def test_loads_existing_workbook(self):
        with tempfile.TemporaryDirectory() as tmp:
            template = Path(tmp) / "AE-1.xlsx"
            wb = openpyxl.Workbook()
            wb.active["A1"] = "marker"
            wb.save(template)
            loaded = load_template(template)
            self.assertEqual(loaded.active["A1"].value, "marker")

    def test_missing_path_raises(self):
        with self.assertRaises(FileNotFoundError):
            load_template("/no/such/file.xlsx")


class SaveWorkbookTests(unittest.TestCase):
    def test_writes_to_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            wb = openpyxl.Workbook()
            wb.active["A1"] = "saved"
            out = Path(tmp) / "out" / "AE-1_filled.xlsx"
            returned = save_workbook(wb, out)
            self.assertEqual(returned, out)
            self.assertTrue(out.is_file())
            # Round-trip
            reread = openpyxl.load_workbook(out)
            self.assertEqual(reread.active["A1"].value, "saved")

    def test_overwrites_existing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "AE-1.xlsx"
            wb1 = openpyxl.Workbook()
            wb1.active["A1"] = "first"
            wb1.save(out)
            wb2 = openpyxl.Workbook()
            wb2.active["A1"] = "second"
            save_workbook(wb2, out)
            reread = openpyxl.load_workbook(out)
            self.assertEqual(reread.active["A1"].value, "second")

    def test_creates_missing_parent_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "deeply" / "nested" / "out.xlsx"
            wb = openpyxl.Workbook()
            save_workbook(wb, out)
            self.assertTrue(out.is_file())


if __name__ == "__main__":
    unittest.main()
