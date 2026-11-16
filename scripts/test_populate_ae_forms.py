"""Tests for scripts/populate_ae_forms.py.

The first three classes (LoadFormSpecsTests, FilterFormsTests,
DispatchErrorHandlingTests) cover the dispatcher framework: form-spec
loading, --only filtering, and exception handling. Everything below
them (PopulateAE1*Tests, PopulateAE1A*Tests, PopulateAE3*Tests, ...)
exercises the per-tab populators.

Run from engine root:
    python -m unittest scripts.test_populate_ae_forms -v
or with pytest:
    pytest scripts/test_populate_ae_forms.py -v
"""
from __future__ import annotations

import io
import sys
import tempfile
import textwrap
import unittest
from contextlib import redirect_stderr
from pathlib import Path

import openpyxl

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.populate_ae_forms import (  # noqa: E402
    _AE1_PERSONNEL_ROWS,
    _AE3_FIXED_SLOTS,
    _AE4_PROJECT_ROWS,
    _AE5_CODE_CELLS,
    _AE5_DESIGNER_ROWS,
    _AE6_TAB_MAX_CHARS,
    _AE6_TAB_NAME_MAX,
    AEFormSpec,
    PopulationContext,
    _derive_registration_line,
    _dispatch,
    _filter_forms,
    _format_discipline_for_reg_line,
    _format_project_date,
    _format_submission_date,
    _iter_ae4_slots,
    _legal_form_checkbox_cells,
    _load_form_specs,
    _paginate_ae6_sections,
    _parse_ae6_sections,
    _populate_ae1,
    _populate_ae1a,
    _populate_ae2,
    _populate_ae3,
    _populate_ae4,
    _populate_ae5,
    _populate_ae6,
    _project_year,
    _resolve_key_personnel_slot,
    _select_personnel_projects,
    _strip_internal_refs,
    _strip_markdown,
)


def _write_proposal_type(repo_root: Path, body: str) -> Path:
    """Create scripts/scaffold/proposal_types/ae_term_contract.yml under repo_root."""
    p = repo_root / "scripts" / "scaffold" / "proposal_types" / "ae_term_contract.yml"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(body).lstrip("\n"), encoding="utf-8")
    return p


def _good_proposal_type_body() -> str:
    return """
        description: "AE term contract"
        ae_forms:
          - code: AE-1
            description: "Firm Data"
            cardinality: once
            enabled: true
          - code: AE-2
            description: "Subconsultant Data"
            cardinality: per_firm
            enabled: false
          - code: AE-4
            description: "Personnel"
            cardinality: per_personnel
            enabled: true
    """


class LoadFormSpecsTests(unittest.TestCase):
    def test_loads_well_formed_specs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_proposal_type(root, _good_proposal_type_body())
            specs = _load_form_specs(root)
            self.assertEqual(len(specs), 3)
            self.assertEqual(specs[0].code, "AE-1")
            self.assertTrue(specs[0].enabled)
            self.assertFalse(specs[1].enabled)
            self.assertEqual(specs[2].cardinality, "per_personnel")

    def test_missing_proposal_type_file_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                _load_form_specs(Path(tmp))

    def test_empty_ae_forms_block_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_proposal_type(root, """
                description: "x"
                ae_forms: []
            """)
            with self.assertRaisesRegex(ValueError, "ae_forms"):
                _load_form_specs(root)

    def test_invalid_cardinality_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_proposal_type(root, """
                description: "x"
                ae_forms:
                  - code: AE-1
                    description: "Firm Data"
                    cardinality: not_a_thing
                    enabled: true
            """)
            with self.assertRaisesRegex(ValueError, "cardinality"):
                _load_form_specs(root)

    def test_missing_field_in_entry_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_proposal_type(root, """
                description: "x"
                ae_forms:
                  - code: AE-1
                    description: "Firm Data"
                    enabled: true
            """)
            with self.assertRaisesRegex(ValueError, "cardinality"):
                _load_form_specs(root)

    def test_committed_proposal_type_yml_validates(self):
        # The real, committed AE term-contract preset must parse cleanly —
        # otherwise the script can't run from a freshly scaffolded pursuit.
        specs = _load_form_specs(_REPO_ROOT)
        codes = [s.code for s in specs]
        self.assertEqual(
            codes, ["AE-1", "AE-1A", "AE-2", "AE-3", "AE-4", "AE-5", "AE-6"],
        )


class FilterFormsTests(unittest.TestCase):
    def setUp(self):
        self.specs = [
            AEFormSpec("AE-1", "x", "once", True),
            AEFormSpec("AE-2", "x", "per_firm", False),
            AEFormSpec("AE-3", "x", "once", True),
        ]

    def test_default_keeps_only_enabled(self):
        kept = _filter_forms(self.specs, None)
        self.assertEqual([s.code for s in kept], ["AE-1", "AE-3"])

    def test_only_overrides_disabled(self):
        # --only AE-2 force-includes a form that's disabled by default.
        kept = _filter_forms(self.specs, "AE-2")
        self.assertEqual([s.code for s in kept], ["AE-2"])

    def test_only_subset(self):
        kept = _filter_forms(self.specs, "AE-1,AE-3")
        self.assertEqual({s.code for s in kept}, {"AE-1", "AE-3"})

    def test_unknown_code_in_only_raises(self):
        with self.assertRaises(SystemExit):
            _filter_forms(self.specs, "AE-99")


class DispatchErrorHandlingTests(unittest.TestCase):
    """`_dispatch` catches populator exceptions and counts them as failures.

    All AE populators are implemented as of issue #8 PR 8/n, so there
    are no stubs left to test. This class instead exercises the
    dispatcher's general exception-handling branch using a real
    populator with input that forces an error.
    """
    def _make_ctx(self, root: Path) -> PopulationContext:
        return PopulationContext(
            repo_root=root,
            proposal_config={},
            firm_profile={},
            personnel=[],
            firms=[],
            projects=[],
            templates_dir=root,
            output_dir=root,
        )

    def test_populator_raising_returns_nonzero(self):
        # _populate_ae1 raises FileNotFoundError when its template is
        # missing — exercises _dispatch's catch-all exception handler.
        with tempfile.TemporaryDirectory() as tmp:
            ctx = self._make_ctx(Path(tmp))
            specs = [AEFormSpec("AE-1", "x", "once", True)]
            self.assertEqual(_dispatch(ctx, specs), 1)


# ─────────────────────────────────────────────────────────────────────────
# AE-1 populator tests
# ─────────────────────────────────────────────────────────────────────────

def _good_firm_profile() -> dict:
    """A complete firm_profile dict that AE-1 can populate without warnings."""
    return {
        "firm": {
            "name": "Acme Engineering, Inc.",
            "short_name": "Acme",
            "legal_form": "Professional Corporation",
            "established": "2010",
            "addr1": "123 Main St",
            "addr2": "Anytown, ST 12345",
            "phone": "555-1212",
            "fax": "555-1213",
            "fein": "12-3456789",
            "scc_id": "0142781-4",
            "apelscidla": "0407007067",
            "other_names": "Old Acme (1990-2010)",
            "years_under_current_name": 9,
            "parent_name": "",
            "parent_addr": "",
            "parent_phone": "",
            "parent_fax": "",
        },
        "ownership": {
            "large_business": False,
            "small_business": True,
            "micro_business": True,
            "minority_owned": True,
            "women_owned": False,
            "veteran_owned": False,
            "service_disabled_veteran_owned": False,
            "dsbsd_cert_number": "699774",
        },
        "contacts": {
            "primary": {
                "name": "Pat Lead, PE",
                "title": "President",
                "email": "pat@acme.example",
                "phone": "555-1100",
            },
            "secondary": {
                "name": "Alex Two",
                "title": "VP",
                "email": "alex@acme.example",
                "phone": "555-1101",
            },
        },
        "personnel_counts": {
            "project_management":   [0, 1, 0, 1],
            "architecture":         [0, 0, 0, 0],
            "civil":                [0, 0, 0, 0],
            "structural":           [0, 0, 0, 0],
            "mechanical":           [1, 1, 1, 1],
            "electrical":           [1, 2, 1, 2],
            "soils":                [0, 0, 0, 0],
            "landscape":            [0, 0, 0, 0],
            "interior_design":      [0, 0, 0, 0],
            "asbestos":             [0, 0, 0, 0],
            "surveyor":             [0, 0, 0, 0],
            "construction_admin":   [0, 1, 0, 1],
            "cadd":                 [0, 1, 0, 1],
            "specifications":       [0, 0, 0, 0],
        },
    }


def _make_ae1_ctx(
    root: Path,
    *,
    firm_profile: dict | None = None,
    proposal_config: dict | None = None,
) -> PopulationContext:
    """Set up template + ctx for AE-1 population tests.

    Creates an empty `<root>/ae1_firm_data/AE-1.xlsx` with sheet name
    "AE-1" so `_populate_ae1` has somewhere to write. Output goes to the
    same `root`.
    """
    template_dir = root / "ae1_firm_data"
    template_dir.mkdir(parents=True, exist_ok=True)
    wb = openpyxl.Workbook()
    wb.active.title = "AE-1"
    wb.save(template_dir / "AE-1.xlsx")

    return PopulationContext(
        repo_root=root,
        proposal_config=proposal_config or {
            "opportunity": {
                "rfp_number": "443882616",
                "rfp_title": "Term Contract for ME Engineering Services",
            },
        },
        firm_profile=firm_profile or _good_firm_profile(),
        personnel=[], firms=[], projects=[],
        templates_dir=root,
        output_dir=root,
    )


def _read_ae1_output(root: Path, short_name: str = "Acme"):
    out = root / "ae1_firm_data" / "filled" / f"AE-1_{short_name}.xlsx"
    return openpyxl.load_workbook(out), out


class PopulateAE1IdentityTests(unittest.TestCase):
    def test_writes_section1_firm_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae1_ctx(root)
            _populate_ae1(ctx, AEFormSpec("AE-1", "x", "once", True))
            wb, _ = _read_ae1_output(root)
            ws = wb["AE-1"]
            self.assertEqual(ws["C8"].value, "Acme Engineering, Inc.")
            self.assertEqual(ws["AR8"].value, 9)
            self.assertEqual(ws["C9"].value, "123 Main St")
            self.assertEqual(ws["C10"].value, "Anytown, ST 12345")
            self.assertEqual(ws["AC10"].value, "Old Acme (1990-2010)")
            self.assertEqual(ws["H12"].value, "555-1212")
            self.assertEqual(ws["T12"].value, "555-1213")
            self.assertEqual(ws["H13"].value, "12-3456789")
            self.assertEqual(ws["X14"].value, "0142781-4")

    def test_dgs_header_anchors_filled(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae1_ctx(root)
            _populate_ae1(ctx, AEFormSpec("AE-1", "x", "once", True))
            wb, _ = _read_ae1_output(root)
            ws = wb["AE-1"]
            self.assertEqual(ws["AN3"].value, "443882616")
            self.assertEqual(ws["M5"].value, "Acme Engineering, Inc.")
            self.assertEqual(
                ws["M6"].value,
                "Term Contract for ME Engineering Services",
            )

    def test_output_filename_uses_short_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae1_ctx(root)
            _populate_ae1(ctx, AEFormSpec("AE-1", "x", "once", True))
            self.assertTrue(
                (root / "ae1_firm_data" / "filled" / "AE-1_Acme.xlsx").is_file()
            )

    def test_optional_fields_left_blank_when_missing(self):
        # Strip every optional field; cells must remain None.
        profile = _good_firm_profile()
        profile["firm"]["fax"] = ""
        profile["firm"]["other_names"] = ""
        profile["firm"]["years_under_current_name"] = 0  # falsy → skipped
        profile["firm"].pop("parent_phone")
        profile["firm"].pop("parent_fax")
        profile["firm"]["parent_name"] = ""
        profile["firm"]["parent_addr"] = ""
        profile["contacts"].pop("secondary")
        profile["ownership"]["dsbsd_cert_number"] = ""

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae1_ctx(root, firm_profile=profile)
            _populate_ae1(ctx, AEFormSpec("AE-1", "x", "once", True))
            wb, _ = _read_ae1_output(root)
            ws = wb["AE-1"]
            for ref in ("T12", "AC10", "AR8", "C17", "C18",
                        "H23", "T23", "AL23",
                        "C28", "N28", "Y28", "AL28"):
                self.assertIsNone(ws[ref].value, f"{ref} should be blank")


class PopulateAE1OwnershipTests(unittest.TestCase):
    def test_micro_minority_checkboxes_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae1_ctx(root)
            _populate_ae1(ctx, AEFormSpec("AE-1", "x", "once", True))
            wb, _ = _read_ae1_output(root)
            ws = wb["AE-1"]
            self.assertEqual(ws["AL17"].value, "X")
            self.assertEqual(ws["AL20"].value, "X")

    def test_unchecked_ownership_cells_left_blank(self):
        # Flip both flags off; the populator writes "" which write_cell
        # treats as a no-op, leaving cells at their template default (None).
        profile = _good_firm_profile()
        profile["ownership"]["micro_business"] = False
        profile["ownership"]["minority_owned"] = False
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae1_ctx(root, firm_profile=profile)
            _populate_ae1(ctx, AEFormSpec("AE-1", "x", "once", True))
            wb, _ = _read_ae1_output(root)
            ws = wb["AE-1"]
            self.assertIsNone(ws["AL17"].value)
            self.assertIsNone(ws["AL20"].value)

    def test_apelscidla_and_dsbsd_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae1_ctx(root)
            _populate_ae1(ctx, AEFormSpec("AE-1", "x", "once", True))
            wb, _ = _read_ae1_output(root)
            ws = wb["AE-1"]
            self.assertEqual(ws["AL22"].value, "0407007067")
            self.assertEqual(ws["AL23"].value, "699774")


class PopulateAE1LegalFormTests(unittest.TestCase):
    def test_professional_corporation_checks_ad20(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae1_ctx(root)
            _populate_ae1(ctx, AEFormSpec("AE-1", "x", "once", True))
            wb, _ = _read_ae1_output(root)
            ws = wb["AE-1"]
            self.assertEqual(ws["AD20"].value, "X")

    def test_unrecognized_legal_form_warns_and_leaves_blank(self):
        profile = _good_firm_profile()
        profile["firm"]["legal_form"] = "Limited Liability Company"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae1_ctx(root, firm_profile=profile)
            buf = io.StringIO()
            with redirect_stderr(buf):
                _populate_ae1(ctx, AEFormSpec("AE-1", "x", "once", True))
            self.assertIn("legal_form", buf.getvalue())
            self.assertIn("Limited Liability Company", buf.getvalue())
            wb, _ = _read_ae1_output(root)
            self.assertIsNone(wb["AE-1"]["AD20"].value)

    def test_empty_legal_form_does_not_warn(self):
        profile = _good_firm_profile()
        profile["firm"]["legal_form"] = ""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae1_ctx(root, firm_profile=profile)
            buf = io.StringIO()
            with redirect_stderr(buf):
                _populate_ae1(ctx, AEFormSpec("AE-1", "x", "once", True))
            self.assertNotIn("legal_form", buf.getvalue())

    def test_legal_form_match_is_case_insensitive(self):
        cells = _legal_form_checkbox_cells("PROFESSIONAL Corporation")
        self.assertEqual(cells, ["AD20"])

    def test_unknown_legal_form_returns_no_cells(self):
        self.assertEqual(_legal_form_checkbox_cells("Joint Venture"), [])


class PopulateAE1ContactsTests(unittest.TestCase):
    def test_primary_contact_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae1_ctx(root)
            _populate_ae1(ctx, AEFormSpec("AE-1", "x", "once", True))
            wb, _ = _read_ae1_output(root)
            ws = wb["AE-1"]
            self.assertEqual(ws["C27"].value, "Pat Lead, PE")
            self.assertEqual(ws["N27"].value, "President")
            self.assertEqual(ws["Y27"].value, "pat@acme.example")
            self.assertEqual(ws["AL27"].value, "555-1100")

    def test_secondary_contact_written_when_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae1_ctx(root)
            _populate_ae1(ctx, AEFormSpec("AE-1", "x", "once", True))
            wb, _ = _read_ae1_output(root)
            ws = wb["AE-1"]
            self.assertEqual(ws["C28"].value, "Alex Two")
            self.assertEqual(ws["N28"].value, "VP")


class PopulateAE1PersonnelCountsTests(unittest.TestCase):
    def test_all_14_disciplines_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae1_ctx(root)
            _populate_ae1(ctx, AEFormSpec("AE-1", "x", "once", True))
            wb, _ = _read_ae1_output(root)
            ws = wb["AE-1"]
            counts = _good_firm_profile()["personnel_counts"]
            for discipline, row in _AE1_PERSONNEL_ROWS.items():
                expected = counts[discipline]
                # Zero values are falsy → write_cell skips → cell stays None.
                # Non-zero values are written.
                for col, val in zip(("P", "X", "AF", "AN"), expected):
                    actual = ws[f"{col}{row}"].value
                    if val == 0:
                        self.assertIsNone(
                            actual,
                            f"{discipline} row {row} col {col}: zero should "
                            f"leave cell blank, got {actual!r}",
                        )
                    else:
                        self.assertEqual(
                            actual, val,
                            f"{discipline} row {row} col {col}",
                        )

    def test_personnel_row_mapping_covers_every_schema_discipline(self):
        # Future-proofing: if firm_profile schema adds a new discipline,
        # this test fails until _AE1_PERSONNEL_ROWS gets the new key.
        from scripts.lib.firm_profile import _PERSONNEL_DISCIPLINES
        self.assertEqual(
            set(_AE1_PERSONNEL_ROWS), set(_PERSONNEL_DISCIPLINES),
        )


class PopulateAE1ErrorTests(unittest.TestCase):
    def test_missing_template_raises_filenotfound(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # ctx is built without creating the template file.
            ctx = PopulationContext(
                repo_root=root, proposal_config={},
                firm_profile=_good_firm_profile(),
                personnel=[], firms=[], projects=[],
                templates_dir=root, output_dir=root,
            )
            with self.assertRaises(FileNotFoundError):
                _populate_ae1(ctx, AEFormSpec("AE-1", "x", "once", True))


# ─────────────────────────────────────────────────────────────────────────
# AE-1A populator tests
# ─────────────────────────────────────────────────────────────────────────

def _good_ae1a_profile() -> dict:
    """Firm profile with all AE-1A-required blocks filled in."""
    base = _good_firm_profile()
    base["insurance"] = {
        "narrative": "E&O: Carrier - 1M/1M/25k. CGL: 1M each occurrence."
    }
    base["swam"] = {
        "default_percentage": 85,
        "narrative": "DSBSD-certified SWaM Micro/Minority Business.",
    }
    base["agency_contracts"] = [
        {"agency": "Chesapeake Public Schools",
         "description": "M&E Term Contract 2017-2026"},
        {"agency": "VA DMA",
         "description": "M&E Engineering Services - Readiness Centers"},
    ]
    return base


def _good_ae1a_proposal_config() -> dict:
    return {
        "opportunity": {
            "rfp_number": "443882616",
            "submission_date": "2026-04-23",
        },
        "representative_projects": ["S1", "V-1"],
    }


def _good_ae1a_projects() -> list[dict]:
    return [
        {"id": "S1", "name": "Rena B. Wright Primary",
         "location": "Chesapeake, VA",
         "complete_date": "2024-08-30", "start_date": "2023-01-01"},
        {"id": "V-1", "name": "Hampton VAMC HVAC",
         "location": "Hampton, VA",
         "complete_date": "In Progress", "start_date": "2024-03-01"},
    ]


def _make_ae1a_ctx(
    root: Path,
    *,
    firm_profile: dict | None = None,
    proposal_config: dict | None = None,
    projects: list[dict] | None = None,
) -> PopulationContext:
    """Set up template + ctx for AE-1A population tests."""
    template_dir = root / "ae1a_swam_certifications"
    template_dir.mkdir(parents=True, exist_ok=True)
    wb = openpyxl.Workbook()
    wb.active.title = "AE-1A"
    wb.save(template_dir / "AE-1A.xlsx")

    return PopulationContext(
        repo_root=root,
        proposal_config=proposal_config or _good_ae1a_proposal_config(),
        firm_profile=firm_profile or _good_ae1a_profile(),
        personnel=[],
        firms=[],
        projects=projects or _good_ae1a_projects(),
        templates_dir=root,
        output_dir=root,
    )


def _read_ae1a_output(root: Path, short_name: str = "Acme"):
    out = root / "ae1a_swam_certifications" / "filled" / f"AE-1A_{short_name}.xlsx"
    return openpyxl.load_workbook(out), out


class PopulateAE1AHeaderTests(unittest.TestCase):
    def test_writes_an3_and_m5_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae1a_ctx(root)
            _populate_ae1a(ctx, AEFormSpec("AE-1A", "x", "once", True))
            wb, _ = _read_ae1a_output(root)
            ws = wb["AE-1A"]
            self.assertEqual(ws["AN3"].value, "443882616")
            self.assertEqual(ws["M5"].value, "Acme Engineering, Inc.")

    def test_does_not_overwrite_m6_or_al6(self):
        # M6 + AL6 hold Section 8 template header text on AE-1A. The
        # populator must NOT use fill_dgs_header (which writes M6/AL6).
        # We pre-populate those cells to simulate template content.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template_dir = root / "ae1a_swam_certifications"
            template_dir.mkdir(parents=True, exist_ok=True)
            wb = openpyxl.Workbook()
            wb.active.title = "AE-1A"
            wb.active["M6"] = "8. PROFESSIONAL LIABILITY INSURANCE"
            wb.active["AL6"] = "(template guard)"
            wb.save(template_dir / "AE-1A.xlsx")

            ctx = PopulationContext(
                repo_root=root,
                proposal_config=_good_ae1a_proposal_config(),
                firm_profile=_good_ae1a_profile(),
                personnel=[], firms=[],
                projects=_good_ae1a_projects(),
                templates_dir=root, output_dir=root,
            )
            _populate_ae1a(ctx, AEFormSpec("AE-1A", "x", "once", True))
            wb_out, _ = _read_ae1a_output(root)
            ws = wb_out["AE-1A"]
            self.assertEqual(
                ws["M6"].value, "8. PROFESSIONAL LIABILITY INSURANCE",
            )
            self.assertEqual(ws["AL6"].value, "(template guard)")


class PopulateAE1ASectionsTests(unittest.TestCase):
    def test_section_8_insurance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae1a_ctx(root)
            _populate_ae1a(ctx, AEFormSpec("AE-1A", "x", "once", True))
            wb, _ = _read_ae1a_output(root)
            self.assertIn(
                "Carrier - 1M/1M/25k", wb["AE-1A"]["C7"].value,
            )

    def test_section_9_swam(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae1a_ctx(root)
            _populate_ae1a(ctx, AEFormSpec("AE-1A", "x", "once", True))
            wb, _ = _read_ae1a_output(root)
            ws = wb["AE-1A"]
            self.assertEqual(ws["V13"].value, 85)
            self.assertIn("SWaM Micro/Minority", ws["C14"].value)

    def test_section_10_agency_contracts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae1a_ctx(root)
            _populate_ae1a(ctx, AEFormSpec("AE-1A", "x", "once", True))
            wb, _ = _read_ae1a_output(root)
            ws = wb["AE-1A"]
            self.assertEqual(ws["C25"].value, "Chesapeake Public Schools")
            self.assertEqual(ws["V25"].value, "M&E Term Contract 2017-2026")
            self.assertEqual(ws["C26"].value, "VA DMA")

    def test_section_10_truncates_above_20_with_warning(self):
        profile = _good_ae1a_profile()
        profile["agency_contracts"] = [
            {"agency": f"Agency {i}", "description": f"Contract {i}"}
            for i in range(25)
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae1a_ctx(root, firm_profile=profile)
            buf = io.StringIO()
            with redirect_stderr(buf):
                _populate_ae1a(ctx, AEFormSpec("AE-1A", "x", "once", True))
            self.assertIn("agency_contracts", buf.getvalue())
            self.assertIn("25", buf.getvalue())
            wb, _ = _read_ae1a_output(root)
            ws = wb["AE-1A"]
            # Row 44 is the 20th entry (Agency 19, zero-indexed).
            self.assertEqual(ws["C44"].value, "Agency 19")
            # Row 45 must be untouched (template default = None).
            self.assertIsNone(ws["C45"].value)

    def test_empty_agency_contracts_writes_nothing(self):
        profile = _good_ae1a_profile()
        profile["agency_contracts"] = []
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae1a_ctx(root, firm_profile=profile)
            _populate_ae1a(ctx, AEFormSpec("AE-1A", "x", "once", True))
            wb, _ = _read_ae1a_output(root)
            self.assertIsNone(wb["AE-1A"]["C25"].value)

    def test_section_11_representative_projects(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae1a_ctx(root)
            _populate_ae1a(ctx, AEFormSpec("AE-1A", "x", "once", True))
            wb, _ = _read_ae1a_output(root)
            ws = wb["AE-1A"]
            self.assertEqual(ws["C50"].value, "Rena B. Wright Primary")
            self.assertEqual(ws["AB50"].value, "2024")
            self.assertEqual(ws["AJ50"].value, "Chesapeake, VA")
            # In-progress project → year falls back to start_date.
            self.assertEqual(ws["C51"].value, "Hampton VAMC HVAC")
            self.assertEqual(ws["AB51"].value, "2024")

    def test_section_11_missing_project_id_warns_and_blanks(self):
        config = _good_ae1a_proposal_config()
        config["representative_projects"] = ["S1", "MISSING-ID"]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae1a_ctx(root, proposal_config=config)
            buf = io.StringIO()
            with redirect_stderr(buf):
                _populate_ae1a(ctx, AEFormSpec("AE-1A", "x", "once", True))
            self.assertIn("MISSING-ID", buf.getvalue())
            wb, _ = _read_ae1a_output(root)
            ws = wb["AE-1A"]
            self.assertEqual(ws["C50"].value, "Rena B. Wright Primary")
            self.assertIsNone(ws["C51"].value)

    def test_section_11_truncates_above_5_with_warning(self):
        config = _good_ae1a_proposal_config()
        config["representative_projects"] = [f"P{i}" for i in range(7)]
        projects = [
            {"id": f"P{i}", "name": f"Project {i}", "location": "X, ST",
             "complete_date": "2024-01-01", "start_date": "2023-01-01"}
            for i in range(7)
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae1a_ctx(
                root, proposal_config=config, projects=projects,
            )
            buf = io.StringIO()
            with redirect_stderr(buf):
                _populate_ae1a(ctx, AEFormSpec("AE-1A", "x", "once", True))
            self.assertIn("representative_projects", buf.getvalue())
            wb, _ = _read_ae1a_output(root)
            ws = wb["AE-1A"]
            # Row 54 is the 5th entry (P4).
            self.assertEqual(ws["C54"].value, "Project 4")
            # Row 55 must be untouched.
            self.assertIsNone(ws["C55"].value)


class PopulateAE1ASignatureTests(unittest.TestCase):
    def test_signature_lines_filled(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae1a_ctx(root)
            _populate_ae1a(ctx, AEFormSpec("AE-1A", "x", "once", True))
            wb, _ = _read_ae1a_output(root)
            ws = wb["AE-1A"]
            self.assertEqual(ws["I59"].value, "Pat Lead, PE")
            self.assertEqual(ws["I61"].value, "President")
            self.assertEqual(ws["AD61"].value, "April 23, 2026")

    def test_missing_submission_date_leaves_ad61_blank(self):
        config = _good_ae1a_proposal_config()
        config["opportunity"].pop("submission_date")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae1a_ctx(root, proposal_config=config)
            _populate_ae1a(ctx, AEFormSpec("AE-1A", "x", "once", True))
            wb, _ = _read_ae1a_output(root)
            self.assertIsNone(wb["AE-1A"]["AD61"].value)


class PopulateAE1AErrorTests(unittest.TestCase):
    def test_missing_insurance_narrative_raises(self):
        profile = _good_ae1a_profile()
        profile.pop("insurance")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae1a_ctx(root, firm_profile=profile)
            with self.assertRaisesRegex(ValueError, "insurance.narrative"):
                _populate_ae1a(ctx, AEFormSpec("AE-1A", "x", "once", True))

    def test_missing_swam_block_raises(self):
        profile = _good_ae1a_profile()
        profile.pop("swam")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae1a_ctx(root, firm_profile=profile)
            with self.assertRaisesRegex(ValueError, "swam"):
                _populate_ae1a(ctx, AEFormSpec("AE-1A", "x", "once", True))

    def test_missing_template_raises_filenotfound(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = PopulationContext(
                repo_root=root,
                proposal_config=_good_ae1a_proposal_config(),
                firm_profile=_good_ae1a_profile(),
                personnel=[], firms=[], projects=_good_ae1a_projects(),
                templates_dir=root, output_dir=root,
            )
            with self.assertRaises(FileNotFoundError):
                _populate_ae1a(ctx, AEFormSpec("AE-1A", "x", "once", True))


class ProjectYearHelperTests(unittest.TestCase):
    """`_project_year` extracts a year token from project rows."""

    def test_complete_date_yyyymmdd_returns_year(self):
        self.assertEqual(
            _project_year({"complete_date": "2024-08-30"}), "2024",
        )

    def test_complete_date_in_progress_falls_back_to_start(self):
        self.assertEqual(
            _project_year({
                "complete_date": "In Progress",
                "start_date": "2023-06-01",
            }),
            "2023",
        )

    def test_no_dates_returns_nd(self):
        self.assertEqual(_project_year({}), "n.d.")


class FormatSubmissionDateTests(unittest.TestCase):
    def test_iso_yyyymmdd_renders_long_form(self):
        self.assertEqual(
            _format_submission_date("2026-04-23"),
            "April 23, 2026",
        )

    def test_iso_with_leading_zero_day(self):
        self.assertEqual(
            _format_submission_date("2026-04-05"),
            "April 5, 2026",
        )

    def test_non_iso_passes_through(self):
        # The form accepts free text — TBD, quarters, etc. should not error.
        self.assertEqual(_format_submission_date("Q2 2026"), "Q2 2026")
        self.assertEqual(_format_submission_date("TBD"), "TBD")


# ─────────────────────────────────────────────────────────────────────────
# AE-3 populator tests
# ─────────────────────────────────────────────────────────────────────────

def _good_ae3_profile() -> dict:
    """Firm profile with AE-3 narratives populated."""
    base = _good_firm_profile()
    base["narratives"] = {
        "staff_availability": "Standing core team with surge capacity.",
        "project_methodology": "Same-day acknowledgment, 2-day scope, 5-day site visit.",
        "quality_assurance": "Two-layer review; Principal-in-Charge sign-off.",
    }
    return base


def _good_ae3_personnel() -> list[dict]:
    return [
        {"id": "peralta",  "name": "Ian Peralta",            "title": "VP of Engineering"},
        {"id": "ogrady",   "name": "Robert OGrady, PE",      "title": "Senior Mechanical Engineer"},
        {"id": "williams", "name": "Richard Williams, PE",   "title": "President"},
    ]


def _good_ae3_proposal_config() -> dict:
    return {
        "opportunity": {
            "rfp_number": "443882616",
            "rfp_title": "Term Contract for ME Services",
            "submission_date": "2026-04-23",
        },
        "key_personnel": {
            "pm":         {"personnel_id": "peralta"},
            "architect":  {"name": "Valerie Brown", "title": "Principal",
                           "firm": "A+M Architects"},
            "structural": {"name": "Marcos Freeman, PE", "title": "VP",
                           "firm": "McPherson"},
            "mechanical": {"personnel_id": "ogrady", "title": "Mechanical EOR"},
            "electrical": {"personnel_id": "williams"},
            "civil":      None,
            "other": [
                {"title": "Fire Protection Engineer",
                 "name": "Aaron Fried", "firm": "Jensen Hughes"},
            ],
        },
    }


def _make_ae3_ctx(
    root: Path,
    *,
    firm_profile: dict | None = None,
    proposal_config: dict | None = None,
    personnel: list[dict] | None = None,
) -> PopulationContext:
    template_dir = root / "ae3_firm_experience"
    template_dir.mkdir(parents=True, exist_ok=True)
    wb = openpyxl.Workbook()
    wb.active.title = "AE-3"
    wb.save(template_dir / "AE-3.xlsx")

    return PopulationContext(
        repo_root=root,
        proposal_config=proposal_config or _good_ae3_proposal_config(),
        firm_profile=firm_profile or _good_ae3_profile(),
        personnel=personnel or _good_ae3_personnel(),
        firms=[], projects=[],
        templates_dir=root, output_dir=root,
    )


def _read_ae3_output(root: Path, short_name: str = "Acme"):
    out = root / "ae3_firm_experience" / "filled" / f"AE-3_{short_name}.xlsx"
    return openpyxl.load_workbook(out), out


class PopulateAE3Section1Tests(unittest.TestCase):
    """Section 1 — key personnel table; this is the DISC-09 close."""

    def test_personnel_id_resolves_with_prime_firm(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae3_ctx(root)
            _populate_ae3(ctx, AEFormSpec("AE-3", "x", "once", True))
            wb, _ = _read_ae3_output(root)
            ws = wb["AE-3"]
            self.assertEqual(ws["L11"].value, "Ian Peralta")
            self.assertEqual(ws["W11"].value, "VP of Engineering")
            self.assertEqual(ws["AI11"].value, "Acme Engineering, Inc.")

    def test_inline_slot_uses_inline_firm(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae3_ctx(root)
            _populate_ae3(ctx, AEFormSpec("AE-3", "x", "once", True))
            wb, _ = _read_ae3_output(root)
            ws = wb["AE-3"]
            self.assertEqual(ws["L12"].value, "Valerie Brown")
            self.assertEqual(ws["AI12"].value, "A+M Architects")

    def test_title_override_on_personnel_id(self):
        # Mechanical slot: personnel_id=ogrady, title="Mechanical EOR"
        # Override should win over personnel.csv title.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae3_ctx(root)
            _populate_ae3(ctx, AEFormSpec("AE-3", "x", "once", True))
            wb, _ = _read_ae3_output(root)
            self.assertEqual(wb["AE-3"]["W14"].value, "Mechanical EOR")

    def test_null_slot_leaves_row_blank(self):
        # Civil slot is null → row 16 untouched.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae3_ctx(root)
            _populate_ae3(ctx, AEFormSpec("AE-3", "x", "once", True))
            wb, _ = _read_ae3_output(root)
            ws = wb["AE-3"]
            for col in ("L", "W", "AI"):
                self.assertIsNone(ws[f"{col}16"].value)

    def test_other_row_writes_label_and_person(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae3_ctx(root)
            _populate_ae3(ctx, AEFormSpec("AE-3", "x", "once", True))
            wb, _ = _read_ae3_output(root)
            ws = wb["AE-3"]
            self.assertEqual(ws["C17"].value, "Fire Protection Engineer")
            self.assertEqual(ws["L17"].value, "Aaron Fried")
            self.assertEqual(ws["AI17"].value, "Jensen Hughes")

    def test_multiple_other_warns_and_writes_first(self):
        config = _good_ae3_proposal_config()
        config["key_personnel"]["other"] = [
            {"title": "Fire Protection",  "name": "A", "firm": "F1"},
            {"title": "Commissioning",    "name": "B", "firm": "F2"},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae3_ctx(root, proposal_config=config)
            buf = io.StringIO()
            with redirect_stderr(buf):
                _populate_ae3(ctx, AEFormSpec("AE-3", "x", "once", True))
            self.assertIn("Other row", buf.getvalue())
            wb, _ = _read_ae3_output(root)
            ws = wb["AE-3"]
            self.assertEqual(ws["L17"].value, "A")

    def test_other_without_title_raises(self):
        config = _good_ae3_proposal_config()
        config["key_personnel"]["other"] = [
            {"name": "X", "firm": "F"},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae3_ctx(root, proposal_config=config)
            with self.assertRaisesRegex(
                ValueError, "key_personnel.other.0.*title",
            ):
                _populate_ae3(ctx, AEFormSpec("AE-3", "x", "once", True))


class PopulateAE3SectionsTests(unittest.TestCase):
    def test_narratives_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae3_ctx(root)
            _populate_ae3(ctx, AEFormSpec("AE-3", "x", "once", True))
            wb, _ = _read_ae3_output(root)
            ws = wb["AE-3"]
            self.assertIn("core team", ws["C20"].value)
            self.assertIn("Same-day", ws["C28"].value)
            self.assertIn("Two-layer", ws["C44"].value)

    def test_signature_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae3_ctx(root)
            _populate_ae3(ctx, AEFormSpec("AE-3", "x", "once", True))
            wb, _ = _read_ae3_output(root)
            ws = wb["AE-3"]
            self.assertEqual(ws["I58"].value, "Pat Lead, PE")
            self.assertEqual(ws["I60"].value, "President")
            self.assertEqual(ws["AE60"].value, "April 23, 2026")

    def test_dgs_header_anchors_filled(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae3_ctx(root)
            _populate_ae3(ctx, AEFormSpec("AE-3", "x", "once", True))
            wb, _ = _read_ae3_output(root)
            ws = wb["AE-3"]
            self.assertEqual(ws["AN3"].value, "443882616")
            self.assertEqual(
                ws["M6"].value, "Term Contract for ME Services",
            )


class PopulateAE3ErrorTests(unittest.TestCase):
    def test_missing_narrative_raises(self):
        profile = _good_ae3_profile()
        profile["narratives"].pop("quality_assurance")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae3_ctx(root, firm_profile=profile)
            with self.assertRaisesRegex(
                ValueError, "narratives.quality_assurance",
            ):
                _populate_ae3(ctx, AEFormSpec("AE-3", "x", "once", True))

    def test_empty_narrative_raises(self):
        profile = _good_ae3_profile()
        profile["narratives"]["staff_availability"] = "   "
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae3_ctx(root, firm_profile=profile)
            with self.assertRaisesRegex(
                ValueError, "narratives.staff_availability",
            ):
                _populate_ae3(ctx, AEFormSpec("AE-3", "x", "once", True))


class ResolveKeyPersonnelSlotTests(unittest.TestCase):
    """Direct tests on _resolve_key_personnel_slot — covers the DISC-09 contract.

    Every guard rejects "plausible-but-wrong" inputs explicitly so the
    populator can never silently produce a half-row.
    """
    def setUp(self):
        self.personnel_by_id = {
            "peralta": {"id": "peralta", "name": "Ian Peralta",
                        "title": "VP of Engineering"},
        }
        self.prime = "Acme Engineering, Inc."

    def _resolve(self, slot, label="pm"):
        return _resolve_key_personnel_slot(
            slot, label,
            personnel_by_id=self.personnel_by_id,
            prime_firm_name=self.prime,
        )

    def test_none_returns_none(self):
        self.assertIsNone(self._resolve(None))

    def test_personnel_id_resolves(self):
        out = self._resolve({"personnel_id": "peralta"})
        self.assertEqual(out["name"],  "Ian Peralta")
        self.assertEqual(out["title"], "VP of Engineering")
        self.assertEqual(out["firm"],  self.prime)

    def test_title_override_with_personnel_id(self):
        out = self._resolve({
            "personnel_id": "peralta", "title": "PM on this contract",
        })
        self.assertEqual(out["title"], "PM on this contract")
        self.assertEqual(out["name"],  "Ian Peralta")

    def test_personnel_id_with_inline_name_raises(self):
        with self.assertRaisesRegex(ValueError, r"personnel_id.*name"):
            self._resolve({
                "personnel_id": "peralta", "name": "Other Name",
            })

    def test_personnel_id_with_inline_firm_raises(self):
        with self.assertRaisesRegex(ValueError, r"personnel_id.*firm"):
            self._resolve({
                "personnel_id": "peralta", "firm": "Wrong Firm",
            })

    def test_personnel_id_not_in_csv_raises(self):
        with self.assertRaisesRegex(ValueError, "ghost"):
            self._resolve({"personnel_id": "ghost"})

    def test_inline_complete(self):
        out = self._resolve({
            "name": "Valerie Brown", "title": "Principal",
            "firm": "A+M Architects",
        })
        self.assertEqual(out["firm"], "A+M Architects")

    def test_inline_missing_field_raises(self):
        with self.assertRaisesRegex(ValueError, "firm"):
            self._resolve({"name": "X", "title": "T"})

    def test_non_mapping_raises(self):
        with self.assertRaisesRegex(ValueError, "must be a mapping"):
            self._resolve("a string")


class AE3SlotMapTests(unittest.TestCase):
    """Lock in: the AE-3 fixed slot list matches what proposal_config.example documents."""

    def test_six_fixed_slots_in_order(self):
        codes = [k for k, _ in _AE3_FIXED_SLOTS]
        self.assertEqual(
            codes,
            ["pm", "architect", "structural", "mechanical", "electrical", "civil"],
        )


# ─────────────────────────────────────────────────────────────────────────
# AE-4 populator tests
# ─────────────────────────────────────────────────────────────────────────

def _good_ae4_personnel() -> list[dict]:
    return [
        {"id": "peralta", "name": "Ian Peralta", "title": "VP",
         "office": "Virginia Beach", "years_total": 36, "years_firm": 27,
         "education": "AAS Electrical Sci.", "discipline": "pm",
         "license_type": "none", "cpsm_status": "Yes",
         "cpsm_date": "2024-03-01"},
        {"id": "ogrady", "name": "Robert OGrady, PE", "title": "Sr ME",
         "office": "Virginia Beach", "years_total": 40, "years_firm": 1,
         "education": "BS ME", "discipline": "mechanical",
         "license_type": "PE", "license_state": "Virginia",
         "license_number": "402035684", "license_year": 2005,
         "cpsm_status": "No"},
        {"id": "williams", "name": "Richard Williams, PE", "title": "President",
         "office": "Virginia Beach", "years_total": 18, "years_firm": 9,
         "education": "BS EE", "discipline": "electrical",
         "license_type": "PE", "license_state": "Virginia",
         "license_number": "402048025", "license_year": 2011,
         "cpsm_status": "Yes", "cpsm_date": "2021-01-01"},
        {"id": "huber", "name": "J Huber, EIT", "title": "ME",
         "office": "Virginia Beach", "years_total": 4, "years_firm": 3,
         "education": "BS Eng Tech", "discipline": "mechanical",
         "license_type": "EIT", "license_state": "Virginia",
         "cpsm_status": "No"},
        {"id": "oberry", "name": "R OBerry, CPD", "title": "Designer",
         "office": "Virginia Beach", "years_total": 35, "years_firm": 35,
         "education": "ASPE CPD", "discipline": "plumbing",
         "license_type": "CPD", "license_number": "63680",
         "cpsm_status": "No"},
    ]


def _good_ae4_personnel_projects() -> list[dict]:
    return [
        {"personnel_id": "peralta", "project_id": "S1",
         "role": "Project Manager", "listing_order": 1},
        {"personnel_id": "peralta", "project_id": "V-1",
         "role": "Project Manager", "listing_order": 2},
        {"personnel_id": "ogrady", "project_id": "S1",
         "role": "Mechanical EOR", "listing_order": 0},
        {"personnel_id": "williams", "project_id": "S1",
         "role": "Principal-in-Charge", "listing_order": 0},
    ]


def _good_ae4_projects() -> list[dict]:
    return [
        {"id": "S1", "name": "Rena B. Wright HVAC",
         "complete_date": "2024-08-30"},
        {"id": "V-1", "name": "Hampton VAMC",
         "complete_date": "In Progress"},
    ]


def _good_ae4_proposal_config() -> dict:
    return {
        "opportunity": {
            "rfp_number": "443882616",
            "rfp_title": "Term Contract",
            "submission_date": "2026-04-23",
        },
        "key_personnel": {
            "pm": {
                "personnel_id": "peralta",
                "duty": "Project Management; Client Coordination",
                "assignment": "Project Manager",
                "pct": 50,
            },
            "mechanical": {
                "personnel_id": "ogrady",
                "duty": "Senior Mechanical Engineer",
                "assignment": "Mechanical EOR",
                "pct": 40,
            },
            "electrical": {
                "personnel_id": "williams",
                "duty": "Principal-in-Charge",
                "assignment": "PIC / Electrical EOR",
                "pct": 25,
            },
            "architect": {"name": "X", "title": "Y", "firm": "Z"},  # inline → no AE-4
            "civil": None,
            "other": [
                {"title": "Fire Protection", "name": "A", "firm": "F"},
                {"personnel_id": "huber", "title": "EIT support",
                 "duty": "EIT", "assignment": "EIT", "pct": 10},
            ],
        },
    }


def _good_ae4_firm_profile() -> dict:
    return {
        "firm": {"name": "BFA, Inc.", "short_name": "BFA"},
        "contacts": {"primary": {"name": "Williams, PE", "title": "President"}},
    }


def _make_ae4_ctx(
    root: Path,
    *,
    proposal_config: dict | None = None,
    firm_profile: dict | None = None,
    personnel: list[dict] | None = None,
    projects: list[dict] | None = None,
    personnel_projects: list[dict] | None = None,
) -> PopulationContext:
    template_dir = root / "ae4_key_personnel"
    template_dir.mkdir(parents=True, exist_ok=True)
    wb = openpyxl.Workbook()
    wb.active.title = "AE-4"
    wb.save(template_dir / "AE-4.xlsx")

    return PopulationContext(
        repo_root=root,
        proposal_config=proposal_config or _good_ae4_proposal_config(),
        firm_profile=firm_profile or _good_ae4_firm_profile(),
        personnel=personnel or _good_ae4_personnel(),
        firms=[],
        projects=projects or _good_ae4_projects(),
        personnel_projects=(
            personnel_projects if personnel_projects is not None
            else _good_ae4_personnel_projects()
        ),
        templates_dir=root, output_dir=root,
    )


def _read_ae4_output(root: Path, person_id: str):
    out = root / "ae4_key_personnel" / "filled" / f"AE-4_{person_id}.xlsx"
    return openpyxl.load_workbook(out), out


class IterAE4SlotsTests(unittest.TestCase):
    def test_yields_personnel_id_slots_only(self):
        config = _good_ae4_proposal_config()["key_personnel"]
        slots = _iter_ae4_slots(config)
        labels = [label for label, _ in slots]
        # pm, mechanical, electrical (3 fixed); plus other[1] (huber)
        self.assertEqual(
            labels, ["pm", "mechanical", "electrical", "other[1]"],
        )

    def test_skips_inline_subs_and_nulls(self):
        config = {
            "pm": {"personnel_id": "x"},
            "architect": {"name": "X", "title": "Y", "firm": "Z"},
            "civil": None,
            "structural": {},  # empty mapping, no personnel_id
            "other": [],
        }
        labels = [label for label, _ in _iter_ae4_slots(config)]
        self.assertEqual(labels, ["pm"])

    def test_empty_config_yields_nothing(self):
        self.assertEqual(_iter_ae4_slots({}), [])


class FormatProjectDateTests(unittest.TestCase):
    def test_iso_yyyymmdd_renders_us_format(self):
        self.assertEqual(_format_project_date("2024-08-30"), "8/30/2024")
        self.assertEqual(_format_project_date("2023-01-05"), "1/5/2023")

    def test_in_progress_passes_through(self):
        self.assertEqual(_format_project_date("In Progress"), "In Progress")
        self.assertEqual(_format_project_date("Ongoing"), "Ongoing")

    def test_none_or_empty_returns_none(self):
        self.assertIsNone(_format_project_date(None))
        self.assertIsNone(_format_project_date(""))
        self.assertIsNone(_format_project_date("   "))


class FormatDisciplineForRegLineTests(unittest.TestCase):
    def test_engineer_disciplines_capitalize(self):
        self.assertEqual(_format_discipline_for_reg_line("electrical"), "Electrical")
        self.assertEqual(_format_discipline_for_reg_line("mechanical"), "Mechanical")
        self.assertEqual(_format_discipline_for_reg_line("plumbing"), "Plumbing")
        self.assertEqual(_format_discipline_for_reg_line("controls"), "Controls")

    def test_non_engineer_disciplines_blank(self):
        # The "Professional X Engineer" pattern doesn't apply to PM, CADD, other.
        self.assertEqual(_format_discipline_for_reg_line("pm"), "")
        self.assertEqual(_format_discipline_for_reg_line("cadd"), "")
        self.assertEqual(_format_discipline_for_reg_line("other"), "")
        self.assertEqual(_format_discipline_for_reg_line(""), "")


class DeriveRegistrationLineTests(unittest.TestCase):
    def test_pe_full_pattern(self):
        line = _derive_registration_line({
            "license_type": "PE", "license_state": "Virginia",
            "license_year": 2011, "discipline": "electrical",
        }, slot_label="electrical")
        self.assertEqual(line, "2011 / Virginia / Professional Electrical Engineer")

    def test_pe_missing_year_warns_and_returns_blank(self):
        buf = io.StringIO()
        with redirect_stderr(buf):
            line = _derive_registration_line({
                "license_type": "PE", "license_state": "Virginia",
                "discipline": "electrical",
            }, slot_label="x")
        self.assertEqual(line, "")
        self.assertIn("PE registration line could not be derived", buf.getvalue())

    def test_eit_pattern(self):
        line = _derive_registration_line({
            "license_type": "EIT", "license_state": "Virginia",
            "discipline": "mechanical",
        }, slot_label="mechanical")
        self.assertIn("Virginia EIT", line)
        self.assertIn("Mechanical", line)

    def test_cpd_with_license_number(self):
        line = _derive_registration_line({
            "license_type": "CPD", "license_number": "63680",
            "discipline": "plumbing",
        }, slot_label="plumbing")
        self.assertEqual(
            line, "ASPE Certified Plumbing Designer (CPD) — License #63680",
        )

    def test_cpd_without_license_number(self):
        line = _derive_registration_line({
            "license_type": "CPD", "discipline": "plumbing",
        }, slot_label="plumbing")
        self.assertEqual(line, "ASPE Certified Plumbing Designer (CPD)")

    def test_unlicensed_returns_blank_with_warning(self):
        buf = io.StringIO()
        with redirect_stderr(buf):
            line = _derive_registration_line({
                "license_type": "none", "discipline": "pm",
            }, slot_label="pm")
        self.assertEqual(line, "")
        self.assertIn("unlicensed", buf.getvalue())


def _bare_ctx(
    *,
    personnel_projects: list[dict],
    projects: list[dict],
) -> PopulationContext:
    """A PopulationContext for unit tests that don't need a template on disk."""
    return PopulationContext(
        repo_root=Path("/nonexistent"),
        proposal_config={}, firm_profile={},
        personnel=[], firms=[], projects=projects,
        personnel_projects=personnel_projects,
        templates_dir=Path("/nonexistent"),
        output_dir=Path("/nonexistent"),
    )


class SelectPersonnelProjectsTests(unittest.TestCase):
    def test_filters_by_personnel_id(self):
        ctx = _bare_ctx(
            personnel_projects=_good_ae4_personnel_projects(),
            projects=_good_ae4_projects(),
        )
        rows = _select_personnel_projects(
            ctx, personnel_id="ogrady", slot_label="x",
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["project_id"], "S1")

    def test_sorts_by_listing_order_then_complete_date_desc(self):
        ctx = _bare_ctx(
            personnel_projects=[
                # Same listing_order=0; expect complete_date desc.
                {"personnel_id": "x", "project_id": "P-OLD",
                 "role": "r", "listing_order": 0},
                {"personnel_id": "x", "project_id": "P-NEW",
                 "role": "r", "listing_order": 0},
                {"personnel_id": "x", "project_id": "P-PRIORITY",
                 "role": "r", "listing_order": -1},
            ],
            projects=[
                {"id": "P-OLD",     "name": "old",  "complete_date": "2018-01-01"},
                {"id": "P-NEW",     "name": "new",  "complete_date": "2024-01-01"},
                {"id": "P-PRIORITY","name": "prio", "complete_date": "2010-01-01"},
            ],
        )
        rows = _select_personnel_projects(ctx, personnel_id="x", slot_label="x")
        ids = [r["project_id"] for r in rows]
        # P-PRIORITY first (listing_order -1), then newer projects.
        self.assertEqual(ids, ["P-PRIORITY", "P-NEW", "P-OLD"])

    def test_zero_rows_warns_and_returns_empty(self):
        ctx = _bare_ctx(personnel_projects=[], projects=[])
        buf = io.StringIO()
        with redirect_stderr(buf):
            rows = _select_personnel_projects(
                ctx, personnel_id="ghost", slot_label="ghost",
            )
        self.assertEqual(rows, [])
        self.assertIn("ghost", buf.getvalue())

    def test_more_than_six_warns(self):
        many = [
            {"personnel_id": "x", "project_id": f"P{i}",
             "role": "r", "listing_order": i}
            for i in range(8)
        ]
        ctx = _bare_ctx(
            personnel_projects=many,
            projects=[{"id": f"P{i}", "name": f"p{i}",
                       "complete_date": "2020-01-01"} for i in range(8)],
        )
        buf = io.StringIO()
        with redirect_stderr(buf):
            rows = _select_personnel_projects(
                ctx, personnel_id="x", slot_label="x",
            )
        self.assertEqual(len(rows), 8)  # returns all; caller truncates
        self.assertIn("8 rows", buf.getvalue())


class PopulateAE4Tests(unittest.TestCase):
    def test_generates_one_form_per_personnel_id_slot(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae4_ctx(root)
            _populate_ae4(ctx, AEFormSpec("AE-4", "x", "per_personnel", True))
            out_dir = root / "ae4_key_personnel" / "filled"
            files = sorted(f.name for f in out_dir.glob("AE-4_*.xlsx"))
            # pm + mechanical + electrical + other[1]=huber → 4 forms
            self.assertEqual(
                files, ["AE-4_huber.xlsx", "AE-4_ogrady.xlsx",
                        "AE-4_peralta.xlsx", "AE-4_williams.xlsx"],
            )

    def test_inline_sub_does_not_generate_form(self):
        # Architect is inline → no AE-4_*.xlsx for that slot's name.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae4_ctx(root)
            _populate_ae4(ctx, AEFormSpec("AE-4", "x", "per_personnel", True))
            out_dir = root / "ae4_key_personnel" / "filled"
            self.assertFalse((out_dir / "AE-4_X.xlsx").exists())

    def test_per_person_cells(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae4_ctx(root)
            _populate_ae4(ctx, AEFormSpec("AE-4", "x", "per_personnel", True))
            wb, _ = _read_ae4_output(root, "ogrady")
            ws = wb["AE-4"]
            self.assertEqual(ws["G9"].value, "Robert OGrady, PE")
            self.assertEqual(ws["P11"].value, "Senior Mechanical Engineer")
            self.assertEqual(ws["P14"].value, "Mechanical EOR")
            self.assertEqual(ws["AH17"].value, 40)
            self.assertEqual(ws["J20"].value, "BFA, Inc.")
            self.assertEqual(ws["J24"].value, 40)
            self.assertEqual(ws["AB24"].value, 1)
            self.assertEqual(
                ws["C33"].value,
                "2005 / Virginia / Professional Mechanical Engineer",
            )
            self.assertEqual(ws["AA38"].value, "402035684")

    def test_section_6_project_table(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae4_ctx(root)
            _populate_ae4(ctx, AEFormSpec("AE-4", "x", "per_personnel", True))
            wb, _ = _read_ae4_output(root, "peralta")
            ws = wb["AE-4"]
            # Peralta has 2 projects; row 49 (S1, listing_order 1) first,
            # row 51 (V-1, listing_order 2) second.
            self.assertEqual(ws["C49"].value, "Rena B. Wright HVAC")
            self.assertEqual(ws["Y49"].value, "Project Manager")
            self.assertEqual(ws["AL49"].value, "8/30/2024")
            self.assertEqual(ws["C51"].value, "Hampton VAMC")
            self.assertEqual(ws["AL51"].value, "In Progress")

    def test_signature(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae4_ctx(root)
            _populate_ae4(ctx, AEFormSpec("AE-4", "x", "per_personnel", True))
            wb, _ = _read_ae4_output(root, "williams")
            ws = wb["AE-4"]
            self.assertEqual(ws["I65"].value, "Williams, PE")
            self.assertEqual(ws["I67"].value, "President")
            self.assertEqual(ws["AF67"].value, "April 23, 2026")

    def test_blank_duty_warns_but_form_still_writes(self):
        config = _good_ae4_proposal_config()
        config["key_personnel"]["pm"].pop("duty")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae4_ctx(root, proposal_config=config)
            buf = io.StringIO()
            with redirect_stderr(buf):
                _populate_ae4(ctx, AEFormSpec("AE-4", "x", "per_personnel", True))
            self.assertIn("pm.duty", buf.getvalue())
            wb, _ = _read_ae4_output(root, "peralta")
            self.assertIsNone(wb["AE-4"]["P11"].value)

    def test_personnel_id_not_in_csv_raises(self):
        config = _good_ae4_proposal_config()
        config["key_personnel"]["pm"]["personnel_id"] = "ghost"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae4_ctx(root, proposal_config=config)
            with self.assertRaisesRegex(ValueError, "ghost"):
                _populate_ae4(ctx, AEFormSpec("AE-4", "x", "per_personnel", True))

    def test_no_resolvable_slots_warns_and_skips(self):
        # All slots inline → nothing to render → warning, no error.
        config = {
            "opportunity": {"rfp_number": "x", "rfp_title": "x"},
            "key_personnel": {
                "pm": {"name": "X", "title": "Y", "firm": "Z"},
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae4_ctx(root, proposal_config=config)
            buf = io.StringIO()
            with redirect_stderr(buf):
                _populate_ae4(
                    ctx, AEFormSpec("AE-4", "x", "per_personnel", True),
                )
            self.assertIn("no key_personnel slot", buf.getvalue())
            out_dir = root / "ae4_key_personnel" / "filled"
            self.assertFalse(out_dir.exists() and any(out_dir.iterdir()))


class AE4ProjectRowsTests(unittest.TestCase):
    """Lock in the AE-4 cell layout — six rows on a 2-row pitch."""

    def test_six_rows_on_two_row_pitch(self):
        self.assertEqual(_AE4_PROJECT_ROWS, (49, 51, 53, 55, 57, 59))


# ─────────────────────────────────────────────────────────────────────────
# AE-5 populator tests
# ─────────────────────────────────────────────────────────────────────────

def _good_ae5_projects() -> list[dict]:
    return [{
        "id": "S1",
        "name": "Rena B. Wright HVAC",
        "client": "Chesapeake Public Schools",
        "agency_type": "state",
        "location": "Chesapeake, VA",
        "firm_role": "Prime A/E",
        "start_date": "2024-01-15",
        "complete_date": "2024-08-30",
        "gross_sf": 65420,
        "scope_summary": "Full HVAC system replacement.",
        "project_type": "K-12 HVAC Replacement",
        "building_type": "Educational",
        "design_start_date": "2023-01-15",
        "design_complete_date": "2023-12-15",
        "num_floors": 1,
        "owner_budget": 5500000,
        "ae_estimate": 5300000,
        "low_bid": 4980557,
        "num_change_orders": 0,
        "cost_change_orders": 0,
        "substantial_completion": "2024-08-30",
        "codes_used": ["VUSBC", "IBC", "life_safety"],
        "codes_other": "NFPA 90A, NFPA 96",
        "swam_proposed_pct": 98,
        "swam_final_pct": 98,
        "swam_description": "98% SWaM design-phase participation.",
    }]


def _good_ae5_project_contacts() -> list[dict]:
    return [
        {"project_id": "S1", "role": "admin",
         "name": "Robert Scott", "title": "School Plant Supervisor",
         "addr": "312 Cedar Road, Chesapeake, VA 23322",
         "email": "rs@cpschools.example", "phone": "757-547-0139"},
        {"project_id": "S1", "role": "construction_prime_pm",
         "firm": "Virtexco Corporation", "name": "Don Adams",
         "phone": "757-466-1114"},
        {"project_id": "S1", "role": "construction_supt",
         "name": "Richard Whittington"},
    ]


def _good_ae5_project_designers() -> list[dict]:
    return [
        {"project_id": "S1", "discipline": "prime_ae", "firm": "BFA",
         "individual": "Williams, PE", "role": "PIC / Electrical EOR"},
        {"project_id": "S1", "discipline": "mechanical", "firm": "BFA",
         "individual": "OGrady, PE", "role": "Mechanical EOR"},
        {"project_id": "S1", "discipline": "electrical", "firm": "BFA",
         "individual": "Shur", "role": "Senior Electrical Engineer"},
        {"project_id": "S1", "discipline": "other", "firm": "BFA",
         "individual": "OBerry, CPD", "role": "Plumbing"},
    ]


def _good_ae5_proposal_config() -> dict:
    return {
        "opportunity": {
            "rfp_number": "443882616",
            "rfp_title": "Term Contract",
            "submission_date": "2026-04-23",
        },
        "representative_projects": ["S1"],
    }


def _good_ae5_firm_profile() -> dict:
    return {
        "firm": {"name": "BFA, Inc.", "short_name": "BFA"},
        "contacts": {"primary": {"name": "Williams, PE", "title": "President"}},
    }


def _make_ae5_ctx(
    root: Path,
    *,
    proposal_config: dict | None = None,
    firm_profile: dict | None = None,
    projects: list[dict] | None = None,
    project_contacts: list[dict] | None = None,
    project_designers: list[dict] | None = None,
) -> PopulationContext:
    template_dir = root / "ae5_example_projects"
    template_dir.mkdir(parents=True, exist_ok=True)
    wb = openpyxl.Workbook()
    wb.active.title = "AE-5"
    wb.save(template_dir / "AE-5.xlsx")

    return PopulationContext(
        repo_root=root,
        proposal_config=proposal_config or _good_ae5_proposal_config(),
        firm_profile=firm_profile or _good_ae5_firm_profile(),
        personnel=[], firms=[],
        projects=projects or _good_ae5_projects(),
        project_contacts=(
            project_contacts if project_contacts is not None
            else _good_ae5_project_contacts()
        ),
        project_designers=(
            project_designers if project_designers is not None
            else _good_ae5_project_designers()
        ),
        templates_dir=root, output_dir=root,
    )


def _read_ae5_output(root: Path, project_id: str = "S1"):
    out = root / "ae5_example_projects" / "filled" / f"AE-5_{project_id}.xlsx"
    return openpyxl.load_workbook(out), out


class PopulateAE5IdentityTests(unittest.TestCase):
    def test_section_2_project_identification(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae5_ctx(root)
            _populate_ae5(ctx, AEFormSpec("AE-5", "x", "per_project", True))
            wb, _ = _read_ae5_output(root)
            ws = wb["AE-5"]
            self.assertEqual(ws["J7"].value, "Rena B. Wright HVAC")
            self.assertEqual(ws["J9"].value, "K-12 HVAC Replacement")
            self.assertEqual(ws["AD9"].value, "Chesapeake, VA")
            self.assertEqual(ws["G10"].value, "Chesapeake Public Schools")

    def test_admin_contact_cells(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae5_ctx(root)
            _populate_ae5(ctx, AEFormSpec("AE-5", "x", "per_project", True))
            wb, _ = _read_ae5_output(root)
            ws = wb["AE-5"]
            self.assertEqual(ws["L11"].value, "Robert Scott")
            self.assertEqual(ws["AE11"].value, "School Plant Supervisor")
            self.assertEqual(ws["AI12"].value, "rs@cpschools.example")
            self.assertEqual(ws["AI13"].value, "757-547-0139")

    def test_construction_prime_cells(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae5_ctx(root)
            _populate_ae5(ctx, AEFormSpec("AE-5", "x", "per_project", True))
            wb, _ = _read_ae5_output(root)
            ws = wb["AE-5"]
            self.assertEqual(ws["L15"].value, "Virtexco Corporation")
            self.assertEqual(ws["J16"].value, "Don Adams")
            self.assertEqual(ws["AI16"].value, "757-466-1114")
            self.assertEqual(ws["J17"].value, "Richard Whittington")

    def test_missing_admin_leaves_cells_blank(self):
        contacts = [
            c for c in _good_ae5_project_contacts() if c["role"] != "admin"
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae5_ctx(root, project_contacts=contacts)
            _populate_ae5(ctx, AEFormSpec("AE-5", "x", "per_project", True))
            wb, _ = _read_ae5_output(root)
            self.assertIsNone(wb["AE-5"]["L11"].value)
            # construction prime still written
            self.assertEqual(wb["AE-5"]["L15"].value, "Virtexco Corporation")


class PopulateAE5DesignersTests(unittest.TestCase):
    def test_designer_rows_by_discipline(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae5_ctx(root)
            _populate_ae5(ctx, AEFormSpec("AE-5", "x", "per_project", True))
            wb, _ = _read_ae5_output(root)
            ws = wb["AE-5"]
            # prime_ae → row 21
            self.assertEqual(ws["K21"].value, "BFA")
            self.assertEqual(ws["X21"].value, "Williams, PE")
            # mechanical → row 24
            self.assertEqual(ws["K24"].value, "BFA")
            self.assertEqual(ws["X24"].value, "OGrady, PE")
            # electrical → row 25
            self.assertEqual(ws["X25"].value, "Shur")
            # other → row 27 (with role text in col C as discipline label)
            self.assertEqual(ws["C27"].value, "Plumbing")
            self.assertEqual(ws["X27"].value, "OBerry, CPD")
            # architectural / structural / civil missing → rows blank
            self.assertIsNone(ws["K22"].value)
            self.assertIsNone(ws["K23"].value)
            self.assertIsNone(ws["K26"].value)

    def test_duplicate_discipline_warns_last_wins(self):
        designers = [
            {"project_id": "S1", "discipline": "mechanical", "firm": "First",
             "individual": "First Person", "role": "ME"},
            {"project_id": "S1", "discipline": "mechanical", "firm": "Second",
             "individual": "Second Person", "role": "ME 2"},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae5_ctx(root, project_designers=designers)
            buf = io.StringIO()
            with redirect_stderr(buf):
                _populate_ae5(ctx, AEFormSpec("AE-5", "x", "per_project", True))
            self.assertIn("multiple project_designers", buf.getvalue())
            wb, _ = _read_ae5_output(root)
            self.assertEqual(wb["AE-5"]["K24"].value, "Second")


class PopulateAE5CodesTests(unittest.TestCase):
    def test_known_codes_check_their_cells(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae5_ctx(root)
            _populate_ae5(ctx, AEFormSpec("AE-5", "x", "per_project", True))
            wb, _ = _read_ae5_output(root)
            ws = wb["AE-5"]
            # codes_used = [VUSBC, IBC, life_safety]
            self.assertEqual(ws["C30"].value, "X")
            self.assertEqual(ws["H30"].value, "X")
            self.assertEqual(ws["L30"].value, "X")
            # ASAD/ADAAG not in list → blank
            self.assertIsNone(ws["S30"].value)
            self.assertIsNone(ws["X30"].value)
            # codes_other free text
            self.assertEqual(ws["AI30"].value, "NFPA 90A, NFPA 96")

    def test_unknown_code_token_warns(self):
        projects = _good_ae5_projects()
        projects[0]["codes_used"] = ["VUSBC", "NEC"]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae5_ctx(root, projects=projects)
            buf = io.StringIO()
            with redirect_stderr(buf):
                _populate_ae5(ctx, AEFormSpec("AE-5", "x", "per_project", True))
            self.assertIn("NEC", buf.getvalue())
            wb, _ = _read_ae5_output(root)
            self.assertEqual(wb["AE-5"]["C30"].value, "X")  # VUSBC still mapped


class PopulateAE5ConstructionDataTests(unittest.TestCase):
    def test_dates_and_money_cells(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae5_ctx(root)
            _populate_ae5(ctx, AEFormSpec("AE-5", "x", "per_project", True))
            wb, _ = _read_ae5_output(root)
            ws = wb["AE-5"]
            self.assertEqual(ws["I41"].value, "Educational")
            self.assertEqual(ws["I42"].value, 65420)
            self.assertEqual(ws["AF42"].value, "1/15/2023")
            self.assertEqual(ws["AK42"].value, "12/15/2023")
            self.assertEqual(ws["AF43"].value, "1/15/2024")
            self.assertEqual(ws["AK43"].value, "8/30/2024")
            self.assertEqual(ws["K45"].value, 5500000)
            self.assertEqual(ws["K46"].value, 5300000)
            self.assertEqual(ws["K47"].value, 4980557)
            self.assertEqual(ws["AH47"].value, "8/30/2024")

    def test_swam_section(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae5_ctx(root)
            _populate_ae5(ctx, AEFormSpec("AE-5", "x", "per_project", True))
            wb, _ = _read_ae5_output(root)
            ws = wb["AE-5"]
            self.assertEqual(ws["L50"].value, 98)
            self.assertEqual(ws["Z50"].value, 98)
            self.assertIn("98%", ws["C51"].value)


class PopulateAE5SignatureTests(unittest.TestCase):
    def test_signature(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae5_ctx(root)
            _populate_ae5(ctx, AEFormSpec("AE-5", "x", "per_project", True))
            wb, _ = _read_ae5_output(root)
            ws = wb["AE-5"]
            self.assertEqual(ws["I58"].value, "Williams, PE")
            self.assertEqual(ws["I60"].value, "President")
            self.assertEqual(ws["AD60"].value, "April 23, 2026")


class PopulateAE5DispatchTests(unittest.TestCase):
    def test_empty_representative_projects_warns_and_returns(self):
        config = _good_ae5_proposal_config()
        config["representative_projects"] = []
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae5_ctx(root, proposal_config=config)
            buf = io.StringIO()
            with redirect_stderr(buf):
                _populate_ae5(
                    ctx, AEFormSpec("AE-5", "x", "per_project", True),
                )
            self.assertIn("representative_projects", buf.getvalue())
            out_dir = root / "ae5_example_projects" / "filled"
            self.assertFalse(out_dir.exists() and any(out_dir.iterdir()))

    def test_unknown_project_id_raises(self):
        config = _good_ae5_proposal_config()
        config["representative_projects"] = ["GHOST"]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae5_ctx(root, proposal_config=config)
            with self.assertRaisesRegex(ValueError, "GHOST"):
                _populate_ae5(
                    ctx, AEFormSpec("AE-5", "x", "per_project", True),
                )

    def test_one_form_per_representative_project(self):
        # Two projects in the rep list → two AE-5_*.xlsx files.
        projects = [
            {**_good_ae5_projects()[0], "id": "S1"},
            {**_good_ae5_projects()[0], "id": "S2",
             "name": "Second Project"},
        ]
        config = _good_ae5_proposal_config()
        config["representative_projects"] = ["S1", "S2"]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae5_ctx(
                root, projects=projects, proposal_config=config,
            )
            _populate_ae5(ctx, AEFormSpec("AE-5", "x", "per_project", True))
            out_dir = root / "ae5_example_projects" / "filled"
            files = sorted(f.name for f in out_dir.glob("AE-5_*.xlsx"))
            self.assertEqual(files, ["AE-5_S1.xlsx", "AE-5_S2.xlsx"])


class AE5MapTests(unittest.TestCase):
    """Lock in the discipline-row and code-cell maps."""

    def test_designer_rows_in_discipline_order(self):
        rows = list(_AE5_DESIGNER_ROWS.values())
        self.assertEqual(rows, [21, 22, 23, 24, 25, 26, 27])

    def test_designer_disciplines_match_csv_schema(self):
        from scripts.lib.csv_renderer import _PROJECT_DESIGNERS_SCHEMA
        self.assertEqual(
            set(_AE5_DESIGNER_ROWS),
            _PROJECT_DESIGNERS_SCHEMA["enums"]["discipline"],
        )

    def test_code_cells_match_documented_set(self):
        # Five standard codes; codes_other is handled separately at AI30.
        self.assertEqual(
            set(_AE5_CODE_CELLS),
            {"VUSBC", "IBC", "life_safety", "ASAD", "ADAAG"},
        )


# ─────────────────────────────────────────────────────────────────────────
# AE-6 helper tests
# ─────────────────────────────────────────────────────────────────────────

class StripMarkdownTests(unittest.TestCase):
    def test_drops_h2_lines(self):
        out = _strip_markdown("## Section 1 — Title\n\nBody.")
        self.assertEqual(out, "Body.")

    def test_strips_h3_marker_keeps_text(self):
        out = _strip_markdown("### Subsection\nbody")
        self.assertIn("Subsection", out)
        self.assertNotIn("###", out)

    def test_drops_horizontal_rules(self):
        out = _strip_markdown("Line one\n\n---\n\nLine two")
        self.assertNotIn("---", out)

    def test_strips_blockquote_prefix(self):
        out = _strip_markdown("> quoted text\nfollow-up")
        self.assertEqual(out, "quoted text\nfollow-up")

    def test_strips_bold_keeps_text(self):
        self.assertEqual(
            _strip_markdown("**bold word** in line"),
            "bold word in line",
        )

    def test_strips_italic_keeps_text(self):
        self.assertEqual(
            _strip_markdown("*italic word* in line"),
            "italic word in line",
        )

    def test_double_star_not_treated_as_italic(self):
        self.assertEqual(
            _strip_markdown("**both bold** and *italic*"),
            "both bold and italic",
        )

    def test_collapses_excessive_blank_lines(self):
        out = _strip_markdown("para1\n\n\n\n\npara2")
        self.assertEqual(out, "para1\n\npara2")


class StripInternalRefsTests(unittest.TestCase):
    def test_drops_addresses_line(self):
        text = "## Section 1\n*(Addresses EVAL-001, REQ-005)*\n\nBody."
        out = _strip_internal_refs(text)
        self.assertNotIn("Addresses", out)
        self.assertNotIn("EVAL-001", out)

    def test_drops_inline_under_reference(self):
        out = _strip_internal_refs("BFA mobilizes under EVAL-001 within 24h")
        self.assertNotIn("under EVAL-001", out)
        self.assertIn("BFA mobilizes within 24h", out)

    def test_drops_factor_parenthetical(self):
        out = _strip_internal_refs(
            "evaluated factor (EVAL-007) and budget control",
        )
        self.assertNotIn("EVAL-007", out)
        self.assertIn("evaluated factor", out)

    def test_drops_bare_parenthetical_codes(self):
        out = _strip_internal_refs("Quality control (TECH-013, TECH-014).")
        self.assertNotIn("TECH-013", out)
        self.assertNotIn("TECH-014", out)
        self.assertIn("Quality control", out)

    def test_drops_bare_remaining_codes(self):
        out = _strip_internal_refs("See REQ-099 for details")
        self.assertNotIn("REQ-099", out)

    def test_collapses_double_spaces_after_removal(self):
        out = _strip_internal_refs("text  EVAL-001  more text")
        self.assertNotIn("  ", out)


class ParseAE6SectionsTests(unittest.TestCase):
    def test_missing_file_returns_verify_placeholder(self):
        sections = _parse_ae6_sections(Path("/nonexistent/draft.md"))
        self.assertEqual(len(sections), 1)
        tab, body = sections[0]
        self.assertEqual(tab, "AE-6")
        self.assertIn("[VERIFY", body)

    def test_empty_file_returns_verify_placeholder(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "draft.md"
            p.write_text("", encoding="utf-8")
            sections = _parse_ae6_sections(p)
            self.assertEqual(len(sections), 1)
            self.assertIn("[VERIFY", sections[0][1])

    def test_splits_on_section_headings(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "draft.md"
            p.write_text(textwrap.dedent("""
                ## Section 1 — First Topic

                First section body.

                ## Section 2 — Second Topic

                Second section body.
            """).strip(), encoding="utf-8")
            sections = _parse_ae6_sections(p)
            self.assertEqual(len(sections), 2)
            self.assertEqual(sections[0][0], "S1 First Topic")
            self.assertEqual(sections[1][0], "S2 Second Topic")

    def test_tab_name_truncated_to_31_chars(self):
        long_title = "A Very Very Very Long Section Title That Exceeds Excel Limit"
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "draft.md"
            p.write_text(
                f"## Section 1 — {long_title}\n\nbody",
                encoding="utf-8",
            )
            sections = _parse_ae6_sections(p)
            self.assertLessEqual(len(sections[0][0]), 31)

    def test_strips_internal_refs_and_markdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "draft.md"
            p.write_text(textwrap.dedent("""
                ## Section 1 — Topic
                *(Addresses EVAL-001)*

                **Bold lead** and *italic word*.
            """).strip(), encoding="utf-8")
            sections = _parse_ae6_sections(p)
            body = sections[0][1]
            self.assertNotIn("EVAL-001", body)
            self.assertNotIn("Addresses", body)
            self.assertNotIn("**", body)
            self.assertIn("Bold lead", body)
            self.assertIn("italic word", body)

    def test_no_section_headings_returns_single_tab(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "draft.md"
            p.write_text("Plain content. No headings.", encoding="utf-8")
            sections = _parse_ae6_sections(p)
            self.assertEqual(len(sections), 1)
            self.assertEqual(sections[0][0], "AE-6")
            self.assertIn("Plain content", sections[0][1])


class PaginateAE6SectionsTests(unittest.TestCase):
    def test_short_section_passes_through(self):
        out = _paginate_ae6_sections(
            [("S1 Topic", "short body")], max_chars=4500,
        )
        self.assertEqual(out, [("S1 Topic", "short body")])

    def test_long_section_splits_at_paragraph_boundary(self):
        para = "x" * 600
        long_body = "\n\n".join([para] * 10)  # ~6000 chars
        out = _paginate_ae6_sections(
            [("S1 Topic", long_body)], max_chars=2000,
        )
        self.assertGreater(len(out), 1)
        # Each part fits under cap.
        for _, content in out:
            self.assertLessEqual(len(content), 2000)
        # Continuation tabs labeled with parens.
        labels = [t for t, _ in out]
        self.assertEqual(labels[0], "S1 Topic")
        for label in labels[1:]:
            self.assertRegex(label, r"\(\d+\)$")

    def test_continuation_label_truncated_to_31_chars(self):
        long_tab = "A" * 30
        long_body = "\n\n".join(["x" * 1000] * 6)
        out = _paginate_ae6_sections(
            [(long_tab, long_body)], max_chars=2000,
        )
        for tab, _ in out:
            self.assertLessEqual(len(tab), 31)


# ─────────────────────────────────────────────────────────────────────────
# AE-6 populator tests
# ─────────────────────────────────────────────────────────────────────────

def _good_ae6_proposal_config(narrative_path: str = None) -> dict:
    config = {
        "opportunity": {
            "rfp_number": "443882616",
            "rfp_title": "Term Contract",
            "submission_date": "2026-04-23",
        },
    }
    if narrative_path is not None:
        config["ae6_narrative_path"] = narrative_path
    return config


def _good_ae6_firm_profile() -> dict:
    return {
        "firm": {"name": "BFA, Inc.", "short_name": "BFA"},
        "contacts": {"primary": {"name": "Williams, PE", "title": "President"}},
    }


def _make_ae6_ctx(
    root: Path,
    *,
    narrative_path: str | None = "ae6_technical_narrative/ae6_narrative_draft.md",
    narrative_content: str | None = None,
) -> PopulationContext:
    """Set up template + ctx; optionally write a narrative draft."""
    template_dir = root / "ae6_technical_narrative"
    template_dir.mkdir(parents=True, exist_ok=True)
    wb = openpyxl.Workbook()
    wb.active.title = "AE-6"
    wb.save(template_dir / "AE-6.xlsx")

    if narrative_content is not None and narrative_path is not None:
        full = root / narrative_path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(narrative_content, encoding="utf-8")

    return PopulationContext(
        repo_root=root,
        proposal_config=_good_ae6_proposal_config(narrative_path),
        firm_profile=_good_ae6_firm_profile(),
        personnel=[], firms=[], projects=[],
        templates_dir=root, output_dir=root,
    )


def _read_ae6_output(root: Path, short_name: str = "BFA"):
    out = root / "ae6_technical_narrative" / "filled" / f"AE-6_{short_name}.xlsx"
    return openpyxl.load_workbook(out), out


class PopulateAE6Tests(unittest.TestCase):
    def test_creates_one_tab_per_section(self):
        narrative = textwrap.dedent("""
            ## Section 1 — First

            First body.

            ## Section 2 — Second

            Second body.

            ## Section 3 — Third

            Third body.
        """).strip()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae6_ctx(root, narrative_content=narrative)
            _populate_ae6(ctx, AEFormSpec("AE-6", "x", "once", True))
            wb, _ = _read_ae6_output(root)
            self.assertEqual(
                wb.sheetnames,
                ["S1 First", "S2 Second", "S3 Third"],
            )

    def test_signature_only_on_last_tab(self):
        narrative = textwrap.dedent("""
            ## Section 1 — First

            Body 1.

            ## Section 2 — Second

            Body 2.
        """).strip()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae6_ctx(root, narrative_content=narrative)
            _populate_ae6(ctx, AEFormSpec("AE-6", "x", "once", True))
            wb, _ = _read_ae6_output(root)
            # First tab: no signature
            self.assertIsNone(wb["S1 First"]["I57"].value)
            # Last tab: signature filled
            self.assertEqual(wb["S2 Second"]["I57"].value, "Williams, PE")
            self.assertEqual(wb["S2 Second"]["I59"].value, "President")
            self.assertEqual(wb["S2 Second"]["AE59"].value, "April 23, 2026")

    def test_single_section_signs_only_tab(self):
        narrative = "## Section 1 — Only\n\nBody."
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae6_ctx(root, narrative_content=narrative)
            _populate_ae6(ctx, AEFormSpec("AE-6", "x", "once", True))
            wb, _ = _read_ae6_output(root)
            self.assertEqual(len(wb.sheetnames), 1)
            self.assertEqual(wb[wb.sheetnames[0]]["I57"].value, "Williams, PE")

    def test_missing_narrative_writes_verify_placeholder(self):
        # No narrative file → single tab with [VERIFY] body.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae6_ctx(root, narrative_content=None)
            _populate_ae6(ctx, AEFormSpec("AE-6", "x", "once", True))
            wb, _ = _read_ae6_output(root)
            self.assertEqual(len(wb.sheetnames), 1)
            self.assertIn("[VERIFY", wb[wb.sheetnames[0]]["C8"].value)

    def test_long_section_paginates_across_tabs(self):
        para = "x" * 600
        long_body = "\n\n".join([para] * 10)
        narrative = f"## Section 1 — Long\n\n{long_body}"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae6_ctx(root, narrative_content=narrative)
            _populate_ae6(ctx, AEFormSpec("AE-6", "x", "once", True))
            wb, _ = _read_ae6_output(root)
            self.assertGreater(len(wb.sheetnames), 1)
            # First tab is base name, continuation tabs have (N) suffixes.
            self.assertEqual(wb.sheetnames[0], "S1 Long")
            for name in wb.sheetnames[1:]:
                self.assertRegex(name, r"\(\d+\)$")

    def test_dgs_header_anchors_filled(self):
        narrative = "## Section 1 — Topic\n\nBody."
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae6_ctx(root, narrative_content=narrative)
            _populate_ae6(ctx, AEFormSpec("AE-6", "x", "once", True))
            wb, _ = _read_ae6_output(root)
            ws = wb[wb.sheetnames[0]]
            self.assertEqual(ws["AN3"].value, "443882616")
            self.assertEqual(ws["M5"].value, "BFA, Inc.")
            self.assertEqual(ws["M6"].value, "Term Contract")

    def test_internal_refs_stripped_from_content(self):
        narrative = textwrap.dedent("""
            ## Section 1 — Topic
            *(Addresses EVAL-001, REQ-005)*

            **Bold** content under TECH-013 here.
        """).strip()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae6_ctx(root, narrative_content=narrative)
            _populate_ae6(ctx, AEFormSpec("AE-6", "x", "once", True))
            wb, _ = _read_ae6_output(root)
            body = wb[wb.sheetnames[0]]["C8"].value
            self.assertNotIn("EVAL-001", body)
            self.assertNotIn("TECH-013", body)
            self.assertNotIn("Addresses", body)
            self.assertNotIn("**", body)
            self.assertIn("Bold content", body)

    def test_custom_narrative_path(self):
        narrative = "## Section 1 — Custom Path\n\nbody"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae6_ctx(
                root,
                narrative_path="custom/elsewhere/draft.md",
                narrative_content=narrative,
            )
            _populate_ae6(ctx, AEFormSpec("AE-6", "x", "once", True))
            wb, _ = _read_ae6_output(root)
            self.assertEqual(wb.sheetnames, ["S1 Custom Path"])


class AE6ConstantsTests(unittest.TestCase):
    """Lock in the AE-6 layout constants."""

    def test_excel_tab_name_limit(self):
        self.assertEqual(_AE6_TAB_NAME_MAX, 31)

    def test_pagination_threshold_documented(self):
        # Documented in the docstring as ~4500 chars per the C8:AS52
        # merged cell @ ~100 chars/line × ~45 lines.
        self.assertEqual(_AE6_TAB_MAX_CHARS, 4500)


# ─────────────────────────────────────────────────────────────────────────
# AE-2 populator tests
# ─────────────────────────────────────────────────────────────────────────

def _good_ae2_firms() -> list[dict]:
    return [
        {
            "id": "jensen-hughes", "name": "Jensen Hughes",
            "addr1": "123 Main St", "addr2": "Anytown, ST 12345",
            "phone": "555-1212", "fax": "555-1213",
            "fein": "12-3456789", "scc_id": "SCC-123",
            "apelscidla": "APE-456",
            "dsbsd_cert": "N/A (Large Business)",
            "ownership_class": "large",
            "legal_form": "Limited Liability Company",
            "years_in_practice": 30,
            "parent_firm": "Jensen Hughes Global",
            "poc_name": "Aaron Fried",
            "poc_title": "Fire Protection Engineer",
            "poc_email": "afried@jh.example", "poc_phone": "555-1100",
            "primary_function": "Fire Protection Engineering",
        },
        {
            "id": "bsg", "name": "Building Systems Group, Inc.",
            "addr1": "456 Oak Ave", "addr2": "Othertown, ST 67890",
            "phone": "555-2222",
            "fein": "98-7654321", "scc_id": "SCC-456",
            "apelscidla": "APE-789", "dsbsd_cert": "699775",
            "ownership_class": "micro",
            "legal_form": "Professional Corporation",
            "years_in_practice": 12,
            "poc_name": "Brent Capps",
            "poc_title": "Commissioning Authority",
            "poc_email": "bc@bsg.example", "poc_phone": "555-2200",
            "primary_function": "Commissioning",
        },
        {
            "id": "minority-firm", "name": "Minority Engineering Co.",
            "phone": "555-3333",
            "fein": "11-1111111", "scc_id": "SCC-789",
            "apelscidla": "APE-000",
            "ownership_class": "minority",
            "legal_form": "Professional Corporation",
            "poc_name": "Dr. X", "poc_title": "Principal",
            "poc_email": "x@m.example", "poc_phone": "555-3300",
            "primary_function": "Civil",
        },
    ]


def _good_ae2_proposal_config(sub_ids: list[str] | None = None) -> dict:
    return {
        "opportunity": {
            "rfp_number": "443882616",
            "rfp_title": "Term Contract",
        },
        "proposed_subconsultants":
            sub_ids if sub_ids is not None else ["jensen-hughes", "bsg"],
    }


def _good_ae2_firm_profile() -> dict:
    return {
        "firm": {"name": "BFA, Inc.", "short_name": "BFA"},
        "contacts": {"primary": {"name": "Williams, PE", "title": "President"}},
    }


def _make_ae2_ctx(
    root: Path,
    *,
    proposal_config: dict | None = None,
    firm_profile: dict | None = None,
    firms: list[dict] | None = None,
) -> PopulationContext:
    template_dir = root / "ae2_organizational_chart"
    template_dir.mkdir(parents=True, exist_ok=True)
    wb = openpyxl.Workbook()
    wb.active.title = "AE-2"
    wb.save(template_dir / "AE-2.xlsx")

    return PopulationContext(
        repo_root=root,
        proposal_config=proposal_config or _good_ae2_proposal_config(),
        firm_profile=firm_profile or _good_ae2_firm_profile(),
        personnel=[],
        firms=firms or _good_ae2_firms(),
        projects=[],
        templates_dir=root, output_dir=root,
    )


def _read_ae2_output(root: Path, firm_id: str):
    out = root / "ae2_organizational_chart" / "filled" / f"AE-2_{firm_id}.xlsx"
    return openpyxl.load_workbook(out), out


class PopulateAE2DispatchTests(unittest.TestCase):
    def test_one_form_per_proposed_sub(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae2_ctx(root)
            _populate_ae2(ctx, AEFormSpec("AE-2", "x", "per_firm", True))
            out_dir = root / "ae2_organizational_chart" / "filled"
            files = sorted(f.name for f in out_dir.glob("AE-2_*.xlsx"))
            self.assertEqual(
                files, ["AE-2_bsg.xlsx", "AE-2_jensen-hughes.xlsx"],
            )

    def test_empty_proposed_subs_warns_and_returns(self):
        config = _good_ae2_proposal_config(sub_ids=[])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae2_ctx(root, proposal_config=config)
            buf = io.StringIO()
            with redirect_stderr(buf):
                _populate_ae2(
                    ctx, AEFormSpec("AE-2", "x", "per_firm", True),
                )
            self.assertIn("proposed_subconsultants", buf.getvalue())
            out_dir = root / "ae2_organizational_chart" / "filled"
            self.assertFalse(out_dir.exists() and any(out_dir.iterdir()))

    def test_unknown_firm_id_raises(self):
        config = _good_ae2_proposal_config(sub_ids=["GHOST"])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae2_ctx(root, proposal_config=config)
            with self.assertRaisesRegex(ValueError, "GHOST"):
                _populate_ae2(
                    ctx, AEFormSpec("AE-2", "x", "per_firm", True),
                )


class PopulateAE2CellsTests(unittest.TestCase):
    def test_section_1_firm_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae2_ctx(root)
            _populate_ae2(ctx, AEFormSpec("AE-2", "x", "per_firm", True))
            wb, _ = _read_ae2_output(root, "bsg")
            ws = wb["AE-2"]
            self.assertEqual(ws["C8"].value, "Building Systems Group, Inc.")
            self.assertEqual(ws["AR8"].value, 12)
            self.assertEqual(ws["C9"].value, "456 Oak Ave")
            self.assertEqual(ws["C10"].value, "Othertown, ST 67890")
            self.assertEqual(ws["H12"].value, "555-2222")
            self.assertEqual(ws["H13"].value, "98-7654321")
            self.assertEqual(ws["X14"].value, "SCC-456")

    def test_header_uses_prime_firm_name(self):
        # M5 holds the "submitted by" firm — even on sub forms, that's
        # the PRIME (the firm assembling the proposal package).
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae2_ctx(root)
            _populate_ae2(ctx, AEFormSpec("AE-2", "x", "per_firm", True))
            wb, _ = _read_ae2_output(root, "bsg")
            self.assertEqual(wb["AE-2"]["M5"].value, "BFA, Inc.")

    def test_section_4_micro_checkbox(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae2_ctx(root)
            _populate_ae2(ctx, AEFormSpec("AE-2", "x", "per_firm", True))
            wb, _ = _read_ae2_output(root, "bsg")
            ws = wb["AE-2"]
            self.assertEqual(ws["AL17"].value, "X")
            self.assertEqual(ws["AD20"].value, "X")  # Professional Corp
            self.assertEqual(ws["AL23"].value, "699775")

    def test_section_4_minority_checkbox(self):
        config = _good_ae2_proposal_config(sub_ids=["minority-firm"])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae2_ctx(root, proposal_config=config)
            _populate_ae2(ctx, AEFormSpec("AE-2", "x", "per_firm", True))
            wb, _ = _read_ae2_output(root, "minority-firm")
            self.assertEqual(wb["AE-2"]["AL20"].value, "X")
            self.assertIsNone(wb["AE-2"]["AL17"].value)

    def test_large_firm_no_dbe_checkbox(self):
        # Jensen Hughes is `large` — neither AL17 nor AL20 should be checked.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae2_ctx(root)
            _populate_ae2(ctx, AEFormSpec("AE-2", "x", "per_firm", True))
            wb, _ = _read_ae2_output(root, "jensen-hughes")
            self.assertIsNone(wb["AE-2"]["AL17"].value)
            self.assertIsNone(wb["AE-2"]["AL20"].value)

    def test_legal_form_warning_for_undocumented(self):
        # Jensen Hughes is LLC → no documented checkbox → stderr warning.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae2_ctx(root)
            buf = io.StringIO()
            with redirect_stderr(buf):
                _populate_ae2(
                    ctx, AEFormSpec("AE-2", "x", "per_firm", True),
                )
            self.assertIn("legal_form", buf.getvalue())
            self.assertIn("Limited Liability Company", buf.getvalue())

    def test_undocumented_dbe_class_warns(self):
        firms = _good_ae2_firms()
        firms[2]["ownership_class"] = "veteran"  # no documented cell
        config = _good_ae2_proposal_config(sub_ids=["minority-firm"])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae2_ctx(root, firms=firms, proposal_config=config)
            buf = io.StringIO()
            with redirect_stderr(buf):
                _populate_ae2(
                    ctx, AEFormSpec("AE-2", "x", "per_firm", True),
                )
            self.assertIn("ownership_class", buf.getvalue())
            self.assertIn("veteran", buf.getvalue())

    def test_section_5_primary_poc(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae2_ctx(root)
            _populate_ae2(ctx, AEFormSpec("AE-2", "x", "per_firm", True))
            wb, _ = _read_ae2_output(root, "bsg")
            ws = wb["AE-2"]
            self.assertEqual(ws["C27"].value, "Brent Capps")
            self.assertEqual(ws["N27"].value, "Commissioning Authority")
            self.assertEqual(ws["Y27"].value, "bc@bsg.example")
            self.assertEqual(ws["AL27"].value, "555-2200")

    def test_secondary_poc_left_blank(self):
        # firms.csv has one POC; row 28 stays blank.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae2_ctx(root)
            _populate_ae2(ctx, AEFormSpec("AE-2", "x", "per_firm", True))
            wb, _ = _read_ae2_output(root, "bsg")
            ws = wb["AE-2"]
            for ref in ("C28", "N28", "Y28", "AL28"):
                self.assertIsNone(ws[ref].value)

    def test_section_7_personnel_left_blank(self):
        # AE-2 deliberately skips Section 7 — subs don't track per-discipline
        # personnel counts in the firm-level firms.csv.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae2_ctx(root)
            _populate_ae2(ctx, AEFormSpec("AE-2", "x", "per_firm", True))
            wb, _ = _read_ae2_output(root, "bsg")
            ws = wb["AE-2"]
            # P41..AN54 should all be None (rows 41-54 = 14 disciplines).
            for row in range(41, 55):
                for col in ("P", "X", "AF", "AN"):
                    self.assertIsNone(
                        ws[f"{col}{row}"].value,
                        f"AE-2 Section 7 cell {col}{row} should be blank",
                    )

    def test_optional_fields_blank_when_missing(self):
        # Strip every optional column; populator must produce a form without
        # erroring and leave the corresponding cells blank.
        sparse_firm = {
            "id": "sparse", "name": "Sparse, Inc.",
            "phone": "555-9999",
            "fein": "00-0000000", "scc_id": "X", "apelscidla": "Y",
            "ownership_class": "large",
            "poc_name": "Pat", "poc_title": "Owner",
            "poc_email": "p@s.example", "poc_phone": "555-9000",
            "primary_function": "Generic services",
        }
        config = _good_ae2_proposal_config(sub_ids=["sparse"])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _make_ae2_ctx(
                root, proposal_config=config, firms=[sparse_firm],
            )
            _populate_ae2(ctx, AEFormSpec("AE-2", "x", "per_firm", True))
            wb, _ = _read_ae2_output(root, "sparse")
            ws = wb["AE-2"]
            for ref in ("AR8", "T12", "AC10", "C17", "AL23", "C9", "C10"):
                self.assertIsNone(ws[ref].value, f"{ref} should be blank")


if __name__ == "__main__":
    unittest.main()
