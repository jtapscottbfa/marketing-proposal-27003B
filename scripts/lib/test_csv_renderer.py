"""Tests for scripts/lib/csv_renderer.py

Run from engine root:
    python -m unittest scripts.lib.test_csv_renderer -v
or with pytest:
    pytest scripts/lib/test_csv_renderer.py -v
"""
from __future__ import annotations

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.lib.csv_renderer import (  # noqa: E402
    VERIFY_MARKER,
    read_csv,
    render_personnel_role_block,
    render_project_one_liner,
)


def _write_csv(dirpath: Path, name: str, body: str) -> Path:
    """Drop a CSV at <dirpath>/<name> with the given body (dedented)."""
    p = dirpath / name
    p.write_text(textwrap.dedent(body).lstrip("\n"), encoding="utf-8")
    return p


# Header lines, kept in one place so individual test bodies stay short.
_PROJECT_HEADER = (
    "id,name,client,agency_type,location,firm_role,eor_disciplines,"
    "start_date,complete_date,contract_value,gross_sf,scope_summary,"
    "relevance_tags"
)
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
_PAST_PERFORMANCE_HEADER = (
    "project_id,eval_type,eval_period,score_overall,score_quality,"
    "score_schedule,score_cost,score_management,client_poc_name,"
    "client_poc_phone,client_poc_email,verification_status,notes"
)
_PERSONNEL_PROJECTS_HEADER = "personnel_id,project_id,role,listing_order"
_PROJECT_CONTACTS_HEADER = (
    "project_id,role,firm,name,title,addr,email,phone,fax"
)
_PROJECT_DESIGNERS_HEADER = "project_id,discipline,firm,individual,role"


class ReadCsvProjectTests(unittest.TestCase):
    def test_reads_well_formed_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_csv(
                Path(tmp), "projects.csv",
                f"""
                {_PROJECT_HEADER}
                V-1,Hampton VAMC HVAC,Department of Veterans Affairs,federal,"Hampton, VA",Prime A/E,mechanical;electrical,2018-06-01,2019-12-15,4500000,38000,Replaced steam plant with high-efficiency hot-water plant.,hvac;chiller;hospital
                """
            )
            rows = read_csv(p)
            self.assertEqual(len(rows), 1)
            row = rows[0]
            self.assertEqual(row["id"], "V-1")
            self.assertEqual(row["agency_type"], "federal")
            self.assertEqual(row["contract_value"], 4500000)
            self.assertEqual(row["gross_sf"], 38000)
            self.assertEqual(row["eor_disciplines"], ["mechanical", "electrical"])
            self.assertEqual(row["relevance_tags"], ["hvac", "chiller", "hospital"])

    def test_header_only_returns_empty_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_csv(Path(tmp), "projects.csv", f"{_PROJECT_HEADER}\n")
            self.assertEqual(read_csv(p), [])

    def test_empty_optional_cell_is_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_csv(
                Path(tmp), "projects.csv",
                f"""
                {_PROJECT_HEADER}
                V-1,Site A,Client,federal,"City, ST",Prime A/E,,2020-01-01,2021-01-01,,,A scope.,
                """
            )
            row = read_csv(p)[0]
            self.assertIsNone(row["contract_value"])
            self.assertIsNone(row["gross_sf"])
            # Empty list-column with no items round-trips to None, not [].
            self.assertIsNone(row["eor_disciplines"])
            self.assertIsNone(row["relevance_tags"])

    def test_required_cell_with_verify_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_csv(
                Path(tmp), "projects.csv",
                f"""
                {_PROJECT_HEADER}
                V-1,Site A,{VERIFY_MARKER},federal,"City, ST",Prime A/E,,2020-01-01,2021-01-01,,,A scope.,
                """
            )
            with self.assertRaisesRegex(ValueError, r"required column 'client'"):
                read_csv(p)

    def test_required_cell_empty_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_csv(
                Path(tmp), "projects.csv",
                f"""
                {_PROJECT_HEADER}
                V-1,Site A,,federal,"City, ST",Prime A/E,,2020-01-01,2021-01-01,,,A scope.,
                """
            )
            with self.assertRaisesRegex(ValueError, r"required column 'client'"):
                read_csv(p)

    def test_invalid_enum_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_csv(
                Path(tmp), "projects.csv",
                f"""
                {_PROJECT_HEADER}
                V-1,Site A,Client,municipal,"City, ST",Prime A/E,,2020-01-01,2021-01-01,,,A scope.,
                """
            )
            with self.assertRaisesRegex(ValueError, r"agency_type.*'municipal'"):
                read_csv(p)

    def test_int_column_with_non_int_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_csv(
                Path(tmp), "projects.csv",
                f"""
                {_PROJECT_HEADER}
                V-1,Site A,Client,federal,"City, ST",Prime A/E,,2020-01-01,2021-01-01,4.5M,,A scope.,
                """
            )
            with self.assertRaisesRegex(ValueError, r"contract_value"):
                read_csv(p)

    def test_optional_verify_marker_preserved(self):
        # `relevance_tags` is optional; [VERIFY] is allowed and stored as-is.
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_csv(
                Path(tmp), "projects.csv",
                f"""
                {_PROJECT_HEADER}
                V-1,Site A,Client,federal,"City, ST",Prime A/E,,2020-01-01,2021-01-01,,,A scope.,{VERIFY_MARKER}
                """
            )
            row = read_csv(p)[0]
            self.assertEqual(row["relevance_tags"], VERIFY_MARKER)


class ReadCsvPersonnelTests(unittest.TestCase):
    def test_reads_personnel_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_csv(
                Path(tmp), "personnel.csv",
                f"""
                {_PERSONNEL_HEADER}
                doe,"Jane Doe, PE",Senior Engineer,"Richmond, VA",18,12,"BS Mech Eng UVA 2007",mechanical,PE,Virginia,0402-12345,2012,Yes,2018-06-01,Responsible charge for HVAC.
                """
            )
            row = read_csv(p)[0]
            self.assertEqual(row["years_total"], 18)
            self.assertEqual(row["years_firm"], 12)
            self.assertEqual(row["license_year"], 2012)
            self.assertEqual(row["discipline"], "mechanical")
            self.assertEqual(row["license_type"], "PE")

    def test_unlicensed_personnel_optional_fields_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_csv(
                Path(tmp), "personnel.csv",
                f"""
                {_PERSONNEL_HEADER}
                smith,Pat Smith,CADD Lead,"Norfolk, VA",10,5,"AAS Drafting TCC 2014",cadd,,,,,,,
                """
            )
            row = read_csv(p)[0]
            self.assertIsNone(row["license_type"])
            self.assertIsNone(row["license_state"])
            self.assertIsNone(row["license_year"])


class ReadCsvFirmTests(unittest.TestCase):
    def test_reads_firm_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_csv(
                Path(tmp), "firms.csv",
                f"""
                {_FIRM_HEADER}
                bsg,Building Sciences Group,123 Main,"Richmond, VA 23219",555-1212,12-3456789,SCC123,APE456,DSBSD789,small,Building envelope consulting.,,15,Pat Lead,Principal,pat@bsg.com,555-2323,Standard PI 2M,3
                """
            )
            row = read_csv(p)[0]
            self.assertEqual(row["ownership_class"], "small")
            self.assertEqual(row["years_in_practice"], 15)
            self.assertEqual(row["prior_projects_with_prime"], 3)


class ReadCsvPastPerformanceTests(unittest.TestCase):
    def test_verify_marker_allowed_on_verification_status(self):
        # Special case: [VERIFY] is a *valid* enum value for verification_status.
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_csv(
                Path(tmp), "past_performance.csv",
                f"""
                {_PAST_PERFORMANCE_HEADER}
                V-1,CPARS,2023-Q3,Very Good,,,,,,,,{VERIFY_MARKER},
                """
            )
            row = read_csv(p)[0]
            self.assertEqual(row["verification_status"], VERIFY_MARKER)

    def test_verify_on_other_required_column_still_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_csv(
                Path(tmp), "past_performance.csv",
                f"""
                {_PAST_PERFORMANCE_HEADER}
                V-1,CPARS,2023-Q3,{VERIFY_MARKER},,,,,,,,verified,
                """
            )
            with self.assertRaisesRegex(ValueError, r"score_overall"):
                read_csv(p)


class ReadCsvPersonnelProjectsTests(unittest.TestCase):
    def test_reads_link_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_csv(
                Path(tmp), "personnel_projects.csv",
                f"""
                {_PERSONNEL_PROJECTS_HEADER}
                williams,S1,Principal-in-Charge / Electrical EOR,1
                """
            )
            row = read_csv(p)[0]
            self.assertEqual(row["personnel_id"], "williams")
            self.assertEqual(row["project_id"], "S1")
            self.assertEqual(row["role"], "Principal-in-Charge / Electrical EOR")
            self.assertEqual(row["listing_order"], 1)

    def test_listing_order_optional(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_csv(
                Path(tmp), "personnel_projects.csv",
                f"""
                {_PERSONNEL_PROJECTS_HEADER}
                williams,S1,Electrical EOR,
                """
            )
            row = read_csv(p)[0]
            self.assertIsNone(row["listing_order"])

    def test_role_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_csv(
                Path(tmp), "personnel_projects.csv",
                f"""
                {_PERSONNEL_PROJECTS_HEADER}
                williams,S1,,1
                """
            )
            with self.assertRaisesRegex(ValueError, "role"):
                read_csv(p)

    def test_personnel_id_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_csv(
                Path(tmp), "personnel_projects.csv",
                f"""
                {_PERSONNEL_PROJECTS_HEADER}
                ,S1,Engineer,1
                """
            )
            with self.assertRaisesRegex(ValueError, "personnel_id"):
                read_csv(p)


class ReadCsvProjectsExtendedTests(unittest.TestCase):
    """Lock in the AE-5 schema additions to projects.csv: ints + codes_used list."""

    def test_extended_int_columns(self):
        with tempfile.TemporaryDirectory() as tmp:
            extended_header = (
                _PROJECT_HEADER
                + ",project_type,building_type,design_start_date,"
                "design_complete_date,num_floors,owner_budget,ae_estimate,"
                "low_bid,num_change_orders,cost_change_orders,"
                "substantial_completion,codes_used,codes_other,"
                "swam_proposed_pct,swam_final_pct,swam_description"
            )
            p = _write_csv(
                Path(tmp), "projects.csv",
                f"""
                {extended_header}
                S1,Site,Client,state,"X, ST",Prime A/E,,2024-01-01,2024-08-30,,65420,Scope.,,K-12,Educational,2023-01-01,2023-12-15,1,5500000,5300000,4980557,0,0,2024-08-30,VUSBC;IBC,NFPA 90A,98,98,98% SWaM.
                """
            )
            row = read_csv(p)[0]
            self.assertEqual(row["num_floors"], 1)
            self.assertEqual(row["owner_budget"], 5500000)
            self.assertEqual(row["ae_estimate"], 5300000)
            self.assertEqual(row["low_bid"], 4980557)
            self.assertEqual(row["num_change_orders"], 0)
            self.assertEqual(row["swam_proposed_pct"], 98)

    def test_codes_used_parsed_as_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            extended_header = (
                _PROJECT_HEADER + ",codes_used"
            )
            p = _write_csv(
                Path(tmp), "projects.csv",
                f"""
                {extended_header}
                S1,Site,Client,state,"X, ST",Prime A/E,,2024-01-01,2024-08-30,,,Scope.,,VUSBC;IBC;life_safety
                """
            )
            row = read_csv(p)[0]
            self.assertEqual(row["codes_used"], ["VUSBC", "IBC", "life_safety"])


class ReadCsvProjectContactsTests(unittest.TestCase):
    def test_reads_admin_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_csv(
                Path(tmp), "project_contacts.csv",
                f"""
                {_PROJECT_CONTACTS_HEADER}
                S1,admin,,Robert Scott,Plant Supervisor,"312 Cedar Rd",rs@cps.example,757-547-0139,
                """
            )
            row = read_csv(p)[0]
            self.assertEqual(row["role"], "admin")
            self.assertEqual(row["name"], "Robert Scott")

    def test_invalid_role_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_csv(
                Path(tmp), "project_contacts.csv",
                f"""
                {_PROJECT_CONTACTS_HEADER}
                S1,owner,,X,,,,,
                """
            )
            with self.assertRaisesRegex(ValueError, "role"):
                read_csv(p)

    def test_role_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_csv(
                Path(tmp), "project_contacts.csv",
                f"""
                {_PROJECT_CONTACTS_HEADER}
                S1,,,X,,,,,
                """
            )
            with self.assertRaisesRegex(ValueError, "role"):
                read_csv(p)


class ReadCsvProjectDesignersTests(unittest.TestCase):
    def test_reads_designer_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_csv(
                Path(tmp), "project_designers.csv",
                f"""
                {_PROJECT_DESIGNERS_HEADER}
                S1,prime_ae,BFA,"Williams, PE",PIC / Electrical EOR
                """
            )
            row = read_csv(p)[0]
            self.assertEqual(row["discipline"], "prime_ae")
            self.assertEqual(row["firm"], "BFA")
            self.assertEqual(row["role"], "PIC / Electrical EOR")

    def test_invalid_discipline_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_csv(
                Path(tmp), "project_designers.csv",
                f"""
                {_PROJECT_DESIGNERS_HEADER}
                S1,landscape,BFA,X,Designer
                """
            )
            with self.assertRaisesRegex(ValueError, "discipline"):
                read_csv(p)

    def test_individual_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_csv(
                Path(tmp), "project_designers.csv",
                f"""
                {_PROJECT_DESIGNERS_HEADER}
                S1,prime_ae,BFA,,EOR
                """
            )
            with self.assertRaisesRegex(ValueError, "individual"):
                read_csv(p)


class ReadCsvDispatchTests(unittest.TestCase):
    def test_missing_file_raises_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            read_csv("/no/such/path/that/exists/projects.csv")

    def test_unknown_filename_without_schema_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_csv(Path(tmp), "weird.csv", "a,b\n1,2\n")
            with self.assertRaisesRegex(ValueError, r"no schema known"):
                read_csv(p)

    def test_unknown_filename_with_explicit_schema_works(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_csv(Path(tmp), "weird.csv", "a,b,c\n1,foo,x;y\n")
            schema = {
                "required": {"a"},
                "enums": {"b": {"foo", "bar"}},
                "ints": {"a"},
                "lists": {"c"},
            }
            row = read_csv(p, schema=schema)[0]
            self.assertEqual(row["a"], 1)
            self.assertEqual(row["b"], "foo")
            self.assertEqual(row["c"], ["x", "y"])


class RenderProjectOneLinerTests(unittest.TestCase):
    def test_basic_format(self):
        row = {
            "name": "Hampton VAMC HVAC Conversion",
            "client": "Department of Veterans Affairs",
            "start_date": "2018-06-01",
            "complete_date": "2019-12-15",
        }
        self.assertEqual(
            render_project_one_liner(row),
            "Hampton VAMC HVAC Conversion (Department of Veterans Affairs, 2019)",
        )

    def test_in_progress_falls_back_to_start_year(self):
        row = {
            "name": "Active Project",
            "client": "Some Agency",
            "start_date": "2024-03-01",
            "complete_date": "In Progress",
        }
        self.assertEqual(
            render_project_one_liner(row),
            "Active Project (Some Agency, 2024)",
        )

    def test_no_dates_returns_nd(self):
        row = {"name": "Old Project", "client": "Client"}
        self.assertEqual(
            render_project_one_liner(row),
            "Old Project (Client, n.d.)",
        )


class RenderPersonnelRoleBlockTests(unittest.TestCase):
    def test_full_block(self):
        row = {
            "name": "Jane Doe, PE",
            "title": "Senior Engineer",
            "years_total": 18,
            "years_firm": 12,
            "education": "BS Mech Eng UVA 2007",
            "license_type": "PE",
            "license_state": "Virginia",
            "license_number": "0402-12345",
            "license_year": 2012,
            "notes": "Responsible charge for HVAC.",
        }
        out = render_personnel_role_block(row, role="Mechanical Lead")
        self.assertIn("Jane Doe, PE — Senior Engineer", out)
        self.assertIn("Role on this contract: Mechanical Lead", out)
        self.assertIn("Experience: 18 years total / 12 with current firm", out)
        self.assertIn("Education: BS Mech Eng UVA 2007", out)
        self.assertIn("Registration: PE #0402-12345 (Virginia, 2012)", out)
        self.assertIn("Notes: Responsible charge for HVAC.", out)

    def test_unlicensed_skips_registration_line(self):
        row = {
            "name": "Pat Smith",
            "title": "CADD Lead",
            "years_total": 10,
            "years_firm": 5,
            "education": "AAS Drafting TCC 2014",
            "license_type": None,
        }
        out = render_personnel_role_block(row, role="CADD Production")
        self.assertNotIn("Registration:", out)
        self.assertNotIn("Notes:", out)

    def test_license_type_none_string_treated_as_unlicensed(self):
        row = {
            "name": "Jr Engineer",
            "title": "Designer",
            "years_total": 3,
            "years_firm": 3,
            "education": "BS",
            "license_type": "none",
        }
        out = render_personnel_role_block(row, role="Designer")
        self.assertNotIn("Registration:", out)


if __name__ == "__main__":
    unittest.main()
