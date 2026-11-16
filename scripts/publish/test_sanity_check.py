"""Tests for scripts/publish/sanity_check.py

Run from engine root:
    python -m unittest scripts.publish.test_sanity_check -v
or with pytest:
    pytest scripts/publish/test_sanity_check.py -v
"""
from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
import zipfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from textwrap import dedent

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.publish.sanity_check import (  # noqa: E402
    CheckResult,
    Severity,
    _docx_text,
    _discover_volume_dirs,
    build_context,
    check_addendum_acknowledged,
    check_firm_forms_present,
    check_markdown_as_text,
    check_personnel_forms_present,
    check_placeholder_residue,
    check_proof_points_present,
    check_prohibited_content,
    check_verify_residue,
    format_text_report,
    has_blocking_failure,
    main,
    run_all_checks,
)


# ── Test helpers ──────────────────────────────────────────────────────────────


_PERSONNEL_HEADER = (
    "id,name,title,office,years_total,years_firm,education,discipline,"
    "license_type,license_state,license_number,license_year,cpsm_status,"
    "cpsm_date,notes"
)
_FIRM_HEADER = (
    "id,name,addr1,addr2,phone,fein,scc_id,apelscidla,dsbsd_cert,"
    "ownership_class,primary_function,parent_firm,years_in_practice,"
    "poc_name,poc_title,poc_email,poc_phone,insurance_status,"
    "prior_projects_with_prime"
)


def _build_repo(tmp: Path) -> Path:
    """Lay out a minimal proposal repo skeleton at `tmp` and return its path.

    Includes:
      - 00_admin/proposal_config.yml (empty mapping; volumes inferred from disk)
      - content_library/ with header-only personnel.csv and firms.csv
      - One empty volume dir (01_executive_summary/)
      - _output/ directory (no rendered files yet)
    """
    (tmp / "00_admin").mkdir()
    (tmp / "00_admin" / "proposal_config.yml").write_text("opportunity:\n  rfp_number: TEST-001\n", encoding="utf-8")
    (tmp / "content_library").mkdir()
    (tmp / "content_library" / "personnel.csv").write_text(_PERSONNEL_HEADER + "\n", encoding="utf-8")
    (tmp / "content_library" / "firms.csv").write_text(_FIRM_HEADER + "\n", encoding="utf-8")
    (tmp / "01_executive_summary").mkdir()
    (tmp / "_output").mkdir()
    return tmp


def _write_docx(path: Path, paragraphs: list[str]) -> None:
    """Write a minimal valid .docx whose body contains `paragraphs`.

    Only word/document.xml is populated — that's all `_docx_text` reads.
    """
    body = "".join(
        f"<w:p><w:r><w:t>{_xml_escape(p)}</w:t></w:r></w:p>" for p in paragraphs
    )
    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{body}</w:body></w:document>"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("word/document.xml", document_xml)


def _xml_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


# ── docx text extraction ──────────────────────────────────────────────────────


class DocxTextTests(unittest.TestCase):
    def test_returns_each_paragraph_on_its_own_line(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t) / "x.docx"
            _write_docx(d, ["First paragraph.", "Second paragraph."])
            text = _docx_text(d)
        self.assertIn("First paragraph.", text)
        self.assertIn("Second paragraph.", text)
        # Paragraphs separated by newline, so paragraph-anchored regex work
        self.assertEqual(text, "First paragraph.\nSecond paragraph.")

    def test_raises_on_non_docx_zip(self):
        with tempfile.TemporaryDirectory() as t:
            bogus = Path(t) / "bogus.docx"
            with zipfile.ZipFile(bogus, "w") as z:
                z.writestr("not-document.xml", "<x/>")
            with self.assertRaises(ValueError):
                _docx_text(bogus)


# ── Volume discovery ──────────────────────────────────────────────────────────


class DiscoverVolumeDirsTests(unittest.TestCase):
    def test_falls_back_to_disk_glob_when_no_config(self):
        with tempfile.TemporaryDirectory() as t:
            root = _build_repo(Path(t))
            (root / "02_technical_volume").mkdir()
            dirs = _discover_volume_dirs(root, proposal_config={})
        names = [d.name for d in dirs]
        self.assertIn("01_executive_summary", names)
        self.assertIn("02_technical_volume", names)

    def test_disk_fallback_excludes_admin_dir(self):
        # 00_admin contains drafting scaffold (template_backlog, reference_proposals)
        # that legitimately holds [VERIFY] markers; never include it as a volume.
        with tempfile.TemporaryDirectory() as t:
            root = _build_repo(Path(t))
            dirs = _discover_volume_dirs(root, proposal_config={})
        names = [d.name for d in dirs]
        self.assertNotIn("00_admin", names)

    def test_reads_volumes_block_with_active_filter(self):
        with tempfile.TemporaryDirectory() as t:
            root = _build_repo(Path(t))
            (root / "02_technical_volume").mkdir()
            cfg = {
                "volumes": [
                    {"id": "exec", "folder": "01_executive_summary", "active": True, "order": 1},
                    {"id": "tech", "folder": "02_technical_volume", "active": False, "order": 2},
                ]
            }
            dirs = _discover_volume_dirs(root, proposal_config=cfg)
        self.assertEqual([d.name for d in dirs], ["01_executive_summary"])


# ── verify_residue ────────────────────────────────────────────────────────────


class VerifyResidueTests(unittest.TestCase):
    def test_passes_when_no_markers(self):
        with tempfile.TemporaryDirectory() as t:
            root = _build_repo(Path(t))
            (root / "01_executive_summary" / "intro.md").write_text("Clean prose.\n", encoding="utf-8")
            ctx = build_context(root)
            results = check_verify_residue(ctx)
        self.assertTrue(all(r.passed for r in results), [r for r in results if not r.passed])
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].id.startswith("verify_residue.md:"))

    def test_fails_on_marker_in_md(self):
        with tempfile.TemporaryDirectory() as t:
            root = _build_repo(Path(t))
            (root / "01_executive_summary" / "intro.md").write_text(
                "Some text [VERIFY] more text.\n", encoding="utf-8",
            )
            ctx = build_context(root)
            results = check_verify_residue(ctx)
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0].passed)
        self.assertEqual(results[0].severity, Severity.CRITICAL)
        self.assertIn("[VERIFY]", results[0].message)

    def test_fails_on_marker_in_docx(self):
        with tempfile.TemporaryDirectory() as t:
            root = _build_repo(Path(t))
            _write_docx(root / "_output" / "out.docx", ["Body with [VERIFY: pricing] still in it."])
            ctx = build_context(root)
            results = check_verify_residue(ctx)
        docx_results = [r for r in results if "docx" in r.id]
        self.assertEqual(len(docx_results), 1)
        self.assertFalse(docx_results[0].passed)


# ── placeholder_residue ───────────────────────────────────────────────────────


class PlaceholderResidueTests(unittest.TestCase):
    def test_no_op_when_no_docx(self):
        with tempfile.TemporaryDirectory() as t:
            root = _build_repo(Path(t))
            ctx = build_context(root)
            results = check_placeholder_residue(ctx)
        self.assertEqual(results, [])

    def test_finds_each_pattern(self):
        with tempfile.TemporaryDirectory() as t:
            root = _build_repo(Path(t))
            _write_docx(
                root / "_output" / "out.docx",
                [
                    "PLACEHOLDER intro",
                    "Estimated cost [TBD]",
                    "[FIXME: numbers]",
                    "[INSERT signature here]",
                    "*End of draft*",
                ],
            )
            ctx = build_context(root)
            results = check_placeholder_residue(ctx)
        failed = {r.id.split(":", 1)[0] for r in results if not r.passed}
        # At minimum these specific sub-checks should fail
        self.assertIn("placeholder_residue.placeholder", failed)
        self.assertIn("placeholder_residue.tbd", failed)
        self.assertIn("placeholder_residue.fixme", failed)
        self.assertIn("placeholder_residue.insert", failed)
        self.assertIn("placeholder_residue.end_of_draft", failed)

    def test_passes_clean_docx(self):
        with tempfile.TemporaryDirectory() as t:
            root = _build_repo(Path(t))
            _write_docx(
                root / "_output" / "out.docx",
                ["Clean prose with no draft markers."],
            )
            ctx = build_context(root)
            results = check_placeholder_residue(ctx)
        self.assertTrue(results)
        self.assertTrue(all(r.passed for r in results), [r for r in results if not r.passed])


# ── markdown_as_text ──────────────────────────────────────────────────────────


class MarkdownAsTextTests(unittest.TestCase):
    def test_flags_raw_heading_and_bold(self):
        with tempfile.TemporaryDirectory() as t:
            root = _build_repo(Path(t))
            _write_docx(
                root / "_output" / "out.docx",
                [
                    "## Raw heading should not be here",
                    "Some **bold markers** in body",
                ],
            )
            ctx = build_context(root)
            results = check_markdown_as_text(ctx)
        failed = {r.id.split(":", 1)[0] for r in results if not r.passed}
        self.assertIn("markdown_as_text.h2_or_deeper", failed)
        self.assertIn("markdown_as_text.bold", failed)

    def test_passes_clean_docx(self):
        with tempfile.TemporaryDirectory() as t:
            root = _build_repo(Path(t))
            _write_docx(root / "_output" / "out.docx", ["Plain rendered prose."])
            ctx = build_context(root)
            results = check_markdown_as_text(ctx)
        self.assertTrue(all(r.passed for r in results), [r for r in results if not r.passed])

    def test_severity_is_major(self):
        with tempfile.TemporaryDirectory() as t:
            root = _build_repo(Path(t))
            _write_docx(root / "_output" / "out.docx", ["## leaked heading"])
            ctx = build_context(root)
            results = check_markdown_as_text(ctx)
        for r in results:
            self.assertEqual(r.severity, Severity.MAJOR)


# ── prohibited_content ────────────────────────────────────────────────────────


class ProhibitedContentTests(unittest.TestCase):
    def test_no_op_when_config_absent(self):
        with tempfile.TemporaryDirectory() as t:
            root = _build_repo(Path(t))
            (root / "01_executive_summary" / "x.md").write_text("anything", encoding="utf-8")
            ctx = build_context(root)
            results = check_prohibited_content(ctx)
        self.assertEqual(results, [])

    def test_flags_pattern_in_docx(self):
        with tempfile.TemporaryDirectory() as t:
            root = _build_repo(Path(t))
            (root / "00_admin" / "sanity_config.yml").write_text(
                dedent("""\
                    prohibited_patterns:
                      - pattern: "TCI"
                        label: "TCI (withdrew)"
                        severity: critical
                """),
                encoding="utf-8",
            )
            _write_docx(root / "_output" / "out.docx", ["Subconsultant TCI led the substations work."])
            ctx = build_context(root)
            results = check_prohibited_content(ctx)
        # one md source (none) + one docx source — only docx run since md empty
        failed = [r for r in results if not r.passed]
        self.assertEqual(len(failed), 1)
        self.assertEqual(failed[0].severity, Severity.CRITICAL)
        self.assertIn("TCI", failed[0].message)


# ── proof_points_present ──────────────────────────────────────────────────────


class ProofPointsPresentTests(unittest.TestCase):
    def test_no_op_without_config(self):
        with tempfile.TemporaryDirectory() as t:
            root = _build_repo(Path(t))
            _write_docx(root / "_output" / "out.docx", ["body"])
            ctx = build_context(root)
            results = check_proof_points_present(ctx)
        self.assertEqual(results, [])

    def test_flags_missing_proof_point(self):
        with tempfile.TemporaryDirectory() as t:
            root = _build_repo(Path(t))
            (root / "00_admin" / "sanity_config.yml").write_text(
                dedent("""\
                    proof_points:
                      - pattern: "32%"
                        label: "V-8 generator under budget"
                        severity: critical
                      - pattern: "DSBSD"
                        label: "DSBSD certification language"
                        severity: critical
                """),
                encoding="utf-8",
            )
            _write_docx(root / "_output" / "out.docx", ["DSBSD-certified subconsultants throughout."])
            ctx = build_context(root)
            results = check_proof_points_present(ctx)
        passed_ids = {r.id for r in results if r.passed}
        failed_ids = {r.id for r in results if not r.passed}
        self.assertIn("proof_points_present.DSBSD certification language", passed_ids)
        self.assertIn("proof_points_present.V-8 generator under budget", failed_ids)


# ── addendum_acknowledged ─────────────────────────────────────────────────────


class AddendumAcknowledgedTests(unittest.TestCase):
    def test_no_op_when_no_addendums(self):
        with tempfile.TemporaryDirectory() as t:
            root = _build_repo(Path(t))
            _write_docx(root / "_output" / "out.docx", ["body"])
            ctx = build_context(root)
            results = check_addendum_acknowledged(ctx)
        self.assertEqual(results, [])

    def test_flags_unacknowledged(self):
        with tempfile.TemporaryDirectory() as t:
            root = _build_repo(Path(t))
            addendums = root / "00_admin" / "rfp_intake" / "addendums"
            addendums.mkdir(parents=True)
            (addendums / "Addendum_01.pdf").write_bytes(b"%PDF-1.4 fake")
            (addendums / "Addendum_02.pdf").write_bytes(b"%PDF-1.4 fake")
            _write_docx(
                root / "_output" / "out.docx",
                ["This proposal acknowledges Addendum_01 in full."],
            )
            ctx = build_context(root)
            results = check_addendum_acknowledged(ctx)
        by_passed = {r.id: r.passed for r in results}
        self.assertTrue(by_passed["addendum_acknowledged.Addendum_01"])
        self.assertFalse(by_passed["addendum_acknowledged.Addendum_02"])


# ── personnel / firm forms present ────────────────────────────────────────────


class FormsPresentTests(unittest.TestCase):
    def test_personnel_no_op_on_header_only_csv(self):
        with tempfile.TemporaryDirectory() as t:
            root = _build_repo(Path(t))
            ctx = build_context(root)
            results = check_personnel_forms_present(ctx)
        self.assertEqual(results, [])

    def test_personnel_flags_missing_form(self):
        with tempfile.TemporaryDirectory() as t:
            root = _build_repo(Path(t))
            csv = root / "content_library" / "personnel.csv"
            csv.write_text(
                _PERSONNEL_HEADER + "\n"
                "williams,Williams PE,Principal,Roanoke VA,30,15,BSME Virginia Tech 1995; PE,electrical,PE,Virginia,12345,1998,No,,note\n"
                "ogrady,O'Grady PE,Senior Engineer,Roanoke VA,20,10,BSEE 2000; PE,mechanical,PE,Virginia,67890,2005,No,,\n",
                encoding="utf-8",
            )
            forms_dir = root / "ae4_key_personnel" / "filled"
            forms_dir.mkdir(parents=True)
            (forms_dir / "AE-4_williams.xlsx").write_bytes(b"PK")  # presence-only check
            ctx = build_context(root)
            results = check_personnel_forms_present(ctx)
        by_id_passed = {r.id: r.passed for r in results}
        self.assertTrue(by_id_passed["personnel_forms_present.williams"])
        self.assertFalse(by_id_passed["personnel_forms_present.ogrady"])

    def test_firm_no_op_on_header_only_csv(self):
        with tempfile.TemporaryDirectory() as t:
            root = _build_repo(Path(t))
            ctx = build_context(root)
            results = check_firm_forms_present(ctx)
        self.assertEqual(results, [])


# ── Driver: exit code + json output ───────────────────────────────────────────


class ExitCodeContractTests(unittest.TestCase):
    def test_default_only_critical_blocks(self):
        results = [
            CheckResult(id="a", severity=Severity.MAJOR, passed=False, message=""),
            CheckResult(id="b", severity=Severity.WARN, passed=False, message=""),
        ]
        self.assertFalse(has_blocking_failure(results, strict=False))

    def test_critical_blocks(self):
        results = [
            CheckResult(id="a", severity=Severity.CRITICAL, passed=False, message=""),
        ]
        self.assertTrue(has_blocking_failure(results, strict=False))

    def test_strict_promotes_major(self):
        results = [
            CheckResult(id="a", severity=Severity.MAJOR, passed=False, message=""),
        ]
        self.assertTrue(has_blocking_failure(results, strict=True))

    def test_strict_does_not_promote_warn(self):
        results = [
            CheckResult(id="a", severity=Severity.WARN, passed=False, message=""),
        ]
        self.assertFalse(has_blocking_failure(results, strict=True))


class CliTests(unittest.TestCase):
    def test_clean_repo_exits_zero(self):
        with tempfile.TemporaryDirectory() as t:
            root = _build_repo(Path(t))
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = main(["--repo-root", str(root)])
        self.assertEqual(rc, 0)

    def test_dirty_md_exits_one(self):
        with tempfile.TemporaryDirectory() as t:
            root = _build_repo(Path(t))
            (root / "01_executive_summary" / "x.md").write_text(
                "[VERIFY] still pending", encoding="utf-8",
            )
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = main(["--repo-root", str(root)])
        self.assertEqual(rc, 1)

    def test_json_emits_parseable_array(self):
        with tempfile.TemporaryDirectory() as t:
            root = _build_repo(Path(t))
            buf = io.StringIO()
            with redirect_stdout(buf):
                main(["--repo-root", str(root), "--json"])
            data = json.loads(buf.getvalue())
        self.assertIsInstance(data, list)
        for entry in data:
            self.assertIn("id", entry)
            self.assertIn("severity", entry)
            self.assertIn("passed", entry)

    def test_missing_repo_exits_two(self):
        with tempfile.TemporaryDirectory() as t:
            empty = Path(t) / "no_admin_here"
            empty.mkdir()
            err = io.StringIO()
            with redirect_stderr(err):
                rc = main(["--repo-root", str(empty)])
        self.assertEqual(rc, 2)


# ── End-to-end run_all_checks ─────────────────────────────────────────────────


class RunAllChecksTests(unittest.TestCase):
    def test_clean_repo_all_pass(self):
        with tempfile.TemporaryDirectory() as t:
            root = _build_repo(Path(t))
            results = run_all_checks(root)
        self.assertTrue(all(r.passed for r in results), [r for r in results if not r.passed])

    def test_format_text_report_includes_status_groups(self):
        with tempfile.TemporaryDirectory() as t:
            root = _build_repo(Path(t))
            (root / "01_executive_summary" / "x.md").write_text(
                "[VERIFY] still pending", encoding="utf-8",
            )
            results = run_all_checks(root)
        text = format_text_report(results, strict=False)
        self.assertIn("FAIL", text)
        self.assertIn("BLOCKING FAILURE", text)


if __name__ == "__main__":
    unittest.main()
