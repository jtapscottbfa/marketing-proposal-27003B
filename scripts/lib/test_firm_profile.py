"""Tests for scripts/lib/firm_profile.py

Run from engine root:
    python -m unittest scripts.lib.test_firm_profile -v
or with pytest:
    pytest scripts/lib/test_firm_profile.py -v
"""
from __future__ import annotations

import os
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.lib.firm_profile import (  # noqa: E402
    DEFAULT_PATH,
    PLACEHOLDER_PREFIX,
    load_firm_profile,
    resolve_profile_path,
)


def _good_profile() -> str:
    """A complete, valid firm profile YAML body."""
    return textwrap.dedent("""
        firm:
          name: "Acme Engineering, Inc."
          short_name: "Acme"
          legal_form: "Professional Corporation"
          established: "2010"
          addr1: "123 Main St"
          addr2: "Anytown, ST 12345"
          phone: "555-555-5555"
          fax: ""
          website: "https://acme.example"
          fein: "12-3456789"
          scc_id: "0142781-4"
          apelscidla: "0407007067"
          other_names: ""
          parent_name: ""
          parent_addr: ""
        ownership:
          large_business: false
          small_business: true
          micro_business: true
          minority_owned: false
          women_owned: false
          veteran_owned: false
          service_disabled_veteran_owned: false
          dsbsd_cert_number: "699774"
        contacts:
          primary:
            name: "Pat Lead, PE"
            title: "President"
            email: "pat@acme.example"
            phone: "555-111-2222"
        personnel_counts:
          project_management: [0, 1, 0, 1]
          architecture: [0, 0, 0, 0]
          civil: [0, 0, 0, 0]
          structural: [0, 0, 0, 0]
          mechanical: [1, 1, 1, 1]
          electrical: [1, 2, 1, 2]
          soils: [0, 0, 0, 0]
          landscape: [0, 0, 0, 0]
          interior_design: [0, 0, 0, 0]
          asbestos: [0, 0, 0, 0]
          surveyor: [0, 0, 0, 0]
          construction_admin: [0, 1, 0, 1]
          cadd: [0, 1, 0, 1]
          specifications: [0, 0, 0, 0]
    """).lstrip("\n")


def _write_profile(dirpath: Path, body: str) -> Path:
    p = dirpath / "firm_profile.yml"
    p.write_text(body, encoding="utf-8")
    return p


class ResolveProfilePathTests(unittest.TestCase):
    def test_default_when_no_arg_and_no_env(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("BFA_FIRM_PROFILE", None)
            self.assertEqual(resolve_profile_path(), DEFAULT_PATH)

    def test_explicit_arg_wins_over_env(self):
        with mock.patch.dict(os.environ, {"BFA_FIRM_PROFILE": "/from/env.yml"}):
            self.assertEqual(
                resolve_profile_path("/explicit.yml"),
                Path("/explicit.yml"),
            )

    def test_env_used_when_no_arg(self):
        with mock.patch.dict(os.environ, {"BFA_FIRM_PROFILE": "/from/env.yml"}):
            self.assertEqual(resolve_profile_path(), Path("/from/env.yml"))


class LoadFirmProfileGoodTests(unittest.TestCase):
    def test_loads_complete_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_profile(Path(tmp), _good_profile())
            profile = load_firm_profile(p)
            self.assertEqual(profile["firm"]["name"], "Acme Engineering, Inc.")
            self.assertEqual(profile["personnel_counts"]["mechanical"], [1, 1, 1, 1])

    def test_optional_secondary_contact_omitted_is_ok(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_profile(Path(tmp), _good_profile())
            load_firm_profile(p)  # would raise if optional secondary required

    def test_secondary_contact_when_complete_is_ok(self):
        body = _good_profile() + textwrap.dedent("""
              secondary:
                name: "Other Person"
                title: "VP"
                email: "vp@acme.example"
                phone: "555-333-4444"
        """).lstrip("\n").replace("\n", "\n        ")
        # Re-emit cleanly with secondary appended into contacts block.
        body = _good_profile().replace(
            'phone: "555-111-2222"',
            'phone: "555-111-2222"\n  secondary:\n    name: "Other"\n'
            '    title: "VP"\n    email: "vp@acme.example"\n'
            '    phone: "555-333-4444"',
        )
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_profile(Path(tmp), body)
            profile = load_firm_profile(p)
            self.assertEqual(
                profile["contacts"]["secondary"]["name"], "Other"
            )


class LoadFirmProfileFailureTests(unittest.TestCase):
    def test_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            load_firm_profile("/no/such/firm_profile.yml")

    def test_placeholder_in_required_field_raises(self):
        body = _good_profile().replace(
            'name: "Acme Engineering, Inc."',
            f'name: "{PLACEHOLDER_PREFIX}: Your Firm Name"',
        )
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_profile(Path(tmp), body)
            with self.assertRaisesRegex(ValueError, "firm.name"):
                load_firm_profile(p)

    def test_missing_required_firm_field_raises(self):
        body = _good_profile().replace('fein: "12-3456789"\n  ', "")
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_profile(Path(tmp), body)
            with self.assertRaisesRegex(ValueError, "firm.fein"):
                load_firm_profile(p)

    def test_empty_required_field_raises(self):
        body = _good_profile().replace(
            'name: "Acme Engineering, Inc."', 'name: ""',
        )
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_profile(Path(tmp), body)
            with self.assertRaisesRegex(ValueError, "firm.name"):
                load_firm_profile(p)

    def test_ownership_field_missing_raises(self):
        body = _good_profile().replace(
            "minority_owned: false\n  ", "",
        )
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_profile(Path(tmp), body)
            with self.assertRaisesRegex(ValueError, "ownership.minority_owned"):
                load_firm_profile(p)

    def test_ownership_field_non_bool_raises(self):
        body = _good_profile().replace(
            "small_business: true", 'small_business: "yes"',
        )
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_profile(Path(tmp), body)
            with self.assertRaisesRegex(ValueError, "ownership.small_business"):
                load_firm_profile(p)

    def test_primary_contact_missing_raises(self):
        body = _good_profile().replace(
            "contacts:\n  primary:\n    name: \"Pat Lead, PE\"\n"
            "    title: \"President\"\n    email: \"pat@acme.example\"\n"
            "    phone: \"555-111-2222\"\n",
            "contacts:\n  other: {}\n",
        )
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_profile(Path(tmp), body)
            with self.assertRaisesRegex(ValueError, "contacts.primary"):
                load_firm_profile(p)

    def test_personnel_counts_wrong_length_raises(self):
        body = _good_profile().replace(
            "mechanical: [1, 1, 1, 1]", "mechanical: [1, 1, 1]",
        )
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_profile(Path(tmp), body)
            with self.assertRaisesRegex(
                ValueError, "personnel_counts.mechanical",
            ):
                load_firm_profile(p)

    def test_personnel_counts_missing_discipline_raises(self):
        body = _good_profile().replace(
            "asbestos: [0, 0, 0, 0]\n  ", "",
        )
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_profile(Path(tmp), body)
            with self.assertRaisesRegex(
                ValueError, "personnel_counts.asbestos",
            ):
                load_firm_profile(p)

    def test_personnel_counts_non_int_raises(self):
        body = _good_profile().replace(
            "mechanical: [1, 1, 1, 1]", 'mechanical: [1, "x", 1, 1]',
        )
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_profile(Path(tmp), body)
            with self.assertRaisesRegex(
                ValueError, "personnel_counts.mechanical",
            ):
                load_firm_profile(p)


class InsuranceBlockTests(unittest.TestCase):
    """Optional `insurance:` block — required when present, rejects PLACEHOLDER."""

    def test_absent_insurance_block_is_ok(self):
        # The base good profile has no insurance block. Loader passes.
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_profile(Path(tmp), _good_profile())
            load_firm_profile(p)

    def test_filled_insurance_block_loads(self):
        body = _good_profile() + (
            "\ninsurance:\n  narrative: \"E&O: Carrier - 1M/1M/25k.\"\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_profile(Path(tmp), body)
            profile = load_firm_profile(p)
            self.assertEqual(
                profile["insurance"]["narrative"],
                "E&O: Carrier - 1M/1M/25k.",
            )

    def test_insurance_missing_narrative_raises(self):
        body = _good_profile() + "\ninsurance: {}\n"
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_profile(Path(tmp), body)
            with self.assertRaisesRegex(ValueError, "insurance.narrative"):
                load_firm_profile(p)

    def test_insurance_placeholder_narrative_raises(self):
        body = _good_profile() + (
            f"\ninsurance:\n  narrative: \"{PLACEHOLDER_PREFIX}: fill me\"\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_profile(Path(tmp), body)
            with self.assertRaisesRegex(ValueError, "insurance.narrative"):
                load_firm_profile(p)

    def test_insurance_non_mapping_raises(self):
        body = _good_profile() + "\ninsurance: \"a string\"\n"
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_profile(Path(tmp), body)
            with self.assertRaisesRegex(ValueError, "insurance"):
                load_firm_profile(p)


class SwamBlockTests(unittest.TestCase):
    """Optional `swam:` block — both fields required when present; pct in [0,100]."""

    def test_absent_swam_block_is_ok(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_profile(Path(tmp), _good_profile())
            load_firm_profile(p)

    def test_filled_swam_block_loads(self):
        body = _good_profile() + (
            "\nswam:\n  default_percentage: 85\n  narrative: \"SWaM Micro/Minority.\"\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_profile(Path(tmp), body)
            profile = load_firm_profile(p)
            self.assertEqual(profile["swam"]["default_percentage"], 85)

    def test_swam_missing_percentage_raises(self):
        body = _good_profile() + (
            "\nswam:\n  narrative: \"SWaM.\"\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_profile(Path(tmp), body)
            with self.assertRaisesRegex(ValueError, "swam.default_percentage"):
                load_firm_profile(p)

    def test_swam_non_int_percentage_raises(self):
        body = _good_profile() + (
            "\nswam:\n  default_percentage: \"85\"\n  narrative: \"SWaM.\"\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_profile(Path(tmp), body)
            with self.assertRaisesRegex(ValueError, "swam.default_percentage"):
                load_firm_profile(p)

    def test_swam_percentage_out_of_range_raises(self):
        body = _good_profile() + (
            "\nswam:\n  default_percentage: 150\n  narrative: \"SWaM.\"\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_profile(Path(tmp), body)
            with self.assertRaisesRegex(ValueError, r"\[0, 100\]"):
                load_firm_profile(p)

    def test_swam_negative_percentage_raises(self):
        body = _good_profile() + (
            "\nswam:\n  default_percentage: -1\n  narrative: \"SWaM.\"\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_profile(Path(tmp), body)
            with self.assertRaisesRegex(ValueError, r"\[0, 100\]"):
                load_firm_profile(p)

    def test_swam_missing_narrative_raises(self):
        body = _good_profile() + (
            "\nswam:\n  default_percentage: 85\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_profile(Path(tmp), body)
            with self.assertRaisesRegex(ValueError, "swam.narrative"):
                load_firm_profile(p)


class AgencyContractsTests(unittest.TestCase):
    """Optional `agency_contracts:` list — empty allowed; entries must be complete."""

    def test_absent_block_is_ok(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_profile(Path(tmp), _good_profile())
            load_firm_profile(p)

    def test_empty_list_is_ok(self):
        body = _good_profile() + "\nagency_contracts: []\n"
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_profile(Path(tmp), body)
            profile = load_firm_profile(p)
            self.assertEqual(profile["agency_contracts"], [])

    def test_filled_entries_load(self):
        body = _good_profile() + textwrap.dedent("""
            agency_contracts:
              - agency: "CPS"
                description: "M&E Term Contract"
              - agency: "VA DMA"
                description: "M&E Engineering Services"
        """)
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_profile(Path(tmp), body)
            profile = load_firm_profile(p)
            self.assertEqual(len(profile["agency_contracts"]), 2)
            self.assertEqual(profile["agency_contracts"][0]["agency"], "CPS")

    def test_non_list_raises(self):
        body = _good_profile() + "\nagency_contracts: \"not a list\"\n"
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_profile(Path(tmp), body)
            with self.assertRaisesRegex(ValueError, "agency_contracts"):
                load_firm_profile(p)

    def test_entry_missing_field_raises(self):
        body = _good_profile() + textwrap.dedent("""
            agency_contracts:
              - agency: "CPS"
        """)
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_profile(Path(tmp), body)
            with self.assertRaisesRegex(
                ValueError, r"agency_contracts\[0\].description",
            ):
                load_firm_profile(p)

    def test_entry_with_placeholder_raises(self):
        body = _good_profile() + textwrap.dedent(f"""
            agency_contracts:
              - agency: "{PLACEHOLDER_PREFIX}: Agency"
                description: "Real description"
        """)
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_profile(Path(tmp), body)
            with self.assertRaisesRegex(
                ValueError, r"agency_contracts\[0\].agency",
            ):
                load_firm_profile(p)


class NarrativesBlockTests(unittest.TestCase):
    """Optional `narratives:` block — all three fields required when present."""

    def test_absent_block_is_ok(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_profile(Path(tmp), _good_profile())
            load_firm_profile(p)

    def test_filled_block_loads(self):
        body = _good_profile() + textwrap.dedent("""
            narratives:
              staff_availability: "Standing core team."
              project_methodology: "Same-day acknowledgment."
              quality_assurance: "Two-layer review."
        """)
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_profile(Path(tmp), body)
            profile = load_firm_profile(p)
            self.assertEqual(
                profile["narratives"]["staff_availability"],
                "Standing core team.",
            )

    def test_missing_field_raises(self):
        body = _good_profile() + textwrap.dedent("""
            narratives:
              staff_availability: "x"
              project_methodology: "y"
        """)
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_profile(Path(tmp), body)
            with self.assertRaisesRegex(
                ValueError, "narratives.quality_assurance",
            ):
                load_firm_profile(p)

    def test_placeholder_field_raises(self):
        body = _good_profile() + textwrap.dedent(f"""
            narratives:
              staff_availability: "{PLACEHOLDER_PREFIX}: fill"
              project_methodology: "y"
              quality_assurance: "z"
        """)
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_profile(Path(tmp), body)
            with self.assertRaisesRegex(
                ValueError, "narratives.staff_availability",
            ):
                load_firm_profile(p)

    def test_non_mapping_raises(self):
        body = _good_profile() + "\nnarratives: \"a string\"\n"
        with tempfile.TemporaryDirectory() as tmp:
            p = _write_profile(Path(tmp), body)
            with self.assertRaisesRegex(ValueError, "narratives"):
                load_firm_profile(p)


class ExampleTemplateTests(unittest.TestCase):
    """The committed 00_admin/firm_profile.yml.example must REJECT validation.

    The example is documentation; it must not pass the loader, otherwise
    a user could ship 'PLACEHOLDER: Your Firm Name' into AE forms.
    """
    def test_committed_example_fails_validation(self):
        example = _REPO_ROOT / "00_admin" / "firm_profile.yml.example"
        self.assertTrue(example.is_file(), f"missing: {example}")
        with self.assertRaises(ValueError):
            load_firm_profile(example)


if __name__ == "__main__":
    unittest.main()
