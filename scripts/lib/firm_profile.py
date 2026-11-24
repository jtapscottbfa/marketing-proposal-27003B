"""scripts/lib/firm_profile.py

Loader for firm-level metadata stored in `~/.bfa/firm_profile.yml`
(per ARCH-11). One firm profile is shared across every pursuit on a
workstation; pursuit-specific data lives in `proposal_config.yml`.

Public API:
    DEFAULT_PATH                       # Path: ~/.bfa/firm_profile.yml
    PLACEHOLDER_PREFIX                 # str:  "PLACEHOLDER"
    load_firm_profile(path=None) -> dict
    resolve_profile_path(path=None) -> Path

Why a dedicated loader:
    Several engine scripts (populate_ae_forms.py, color_team_review.sh
    via a shim, new_proposal.sh pre-fill) need the same firm metadata
    and the same validation: every required field is present, no field
    still carries the `"PLACEHOLDER: ..."` template-marker, and
    personnel-count rows are well-formed `[int, int, int, int]` shapes.
    Centralizing the read avoids three subtly different validators that
    drift apart.

USAGE:
    from scripts.lib.firm_profile import load_firm_profile

    profile = load_firm_profile()                   # ~/.bfa/firm_profile.yml
    name = profile["firm"]["name"]
    counts = profile["personnel_counts"]["mechanical"]

Schema (canonical reference: `00_admin/firm_profile.yml.example`):

    firm:
      name, short_name, legal_form, established        — required
      addr1, addr2, phone, website                     — required
      fein, scc_id, apelscidla                         — required
      fax, other_names, parent_name, parent_addr,
      parent_phone, parent_fax,
      years_under_current_name                         — optional
    ownership:
      large_business, small_business, micro_business,
      minority_owned, women_owned, veteran_owned,
      service_disabled_veteran_owned                   — required bool
      dsbsd_cert_number                                — optional
    contacts:
      primary:   {name, title, email, phone}           — required
      secondary: {name, title, email, phone}           — optional block
    personnel_counts:
      <discipline>: [licensed_office, unlicensed_office,
                     licensed_firm, unlicensed_firm]   — 14 disciplines, ints
    insurance:                                         — optional block (AE-1A)
      narrative                                        — required when present
    swam:                                              — optional block (AE-1A)
      default_percentage                               — required when present (0-100)
      narrative                                        — required when present
    agency_contracts:                                  — optional list (AE-1A)
      [{agency, description}, ...]                     — both fields required per entry
    narratives:                                        — optional block (AE-3)
      staff_availability                               — required when present
      project_methodology                              — required when present
      quality_assurance                                — required when present
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

DEFAULT_PATH = Path.home() / ".bfa" / "firm_profile.yml"
PLACEHOLDER_PREFIX = "PLACEHOLDER"

_REQUIRED_FIRM_FIELDS = (
    "name", "short_name", "legal_form", "established",
    "addr1", "addr2", "phone", "website",
    "fein", "scc_id", "apelscidla",
)

_REQUIRED_OWNERSHIP_FIELDS = (
    "large_business", "small_business", "micro_business",
    "minority_owned", "women_owned", "veteran_owned",
    "service_disabled_veteran_owned",
)

_REQUIRED_CONTACT_FIELDS = ("name", "title", "email", "phone")

_PERSONNEL_DISCIPLINES = (
    "project_management", "architecture", "civil", "structural",
    "mechanical", "electrical", "soils", "landscape",
    "interior_design", "asbestos", "surveyor",
    "construction_admin", "cadd", "specifications",
)


def resolve_profile_path(path: Path | str | None = None) -> Path:
    """Pick the firm-profile path: explicit arg > `BFA_FIRM_PROFILE` env > default.

    Args:
        path: Explicit path override. Wins over the environment variable
            when set.

    Returns:
        The selected `Path`. Existence is **not** checked here — the
        caller (or `load_firm_profile`) handles missing-file errors so
        the resolution and the I/O can fail with distinct messages.
    """
    if path is not None:
        return Path(path)
    env = os.environ.get("BFA_FIRM_PROFILE")
    if env:
        return Path(env)
    return DEFAULT_PATH


def load_firm_profile(path: Path | str | None = None) -> dict[str, Any]:
    """Load and validate the firm profile YAML.

    Validation rules:
        - All `_REQUIRED_FIRM_FIELDS` are present and not the
          `PLACEHOLDER:` template marker.
        - All `_REQUIRED_OWNERSHIP_FIELDS` are present and are bools.
        - The `contacts.primary` block exists and every
          `_REQUIRED_CONTACT_FIELDS` field is filled (no PLACEHOLDER).
        - The `contacts.secondary` block, if present, must have every
          field filled if any are filled (all-or-nothing).
        - Every discipline in `_PERSONNEL_DISCIPLINES` has a 4-element
          int list under `personnel_counts`.

    Args:
        path: Optional explicit profile path. When `None`, resolution
            follows `resolve_profile_path()`.

    Returns:
        The parsed dict — the structure is preserved verbatim from the
        YAML; this function validates but does not transform.

    Raises:
        FileNotFoundError: Profile file does not exist at the resolved path.
            Error message includes a pointer to the example template.
        ValueError: YAML parses but fails any validation rule. Error
            message identifies the offending field.
        yaml.YAMLError: YAML is malformed.
    """
    p = resolve_profile_path(path)
    if not p.is_file():
        raise FileNotFoundError(
            f"firm_profile.yml not found at {p}. "
            f"Copy 00_admin/firm_profile.yml.example to {p} and fill it in. "
            f"See ARCH-11 for the firm-profile pattern."
        )

    with p.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    if not isinstance(raw, dict):
        raise ValueError(
            f"{p}: top-level YAML must be a mapping, got {type(raw).__name__}"
        )

    _validate_firm_block(raw.get("firm"), source=p)
    _validate_ownership_block(raw.get("ownership"), source=p)
    _validate_contacts_block(raw.get("contacts"), source=p)
    _validate_personnel_counts(raw.get("personnel_counts"), source=p)

    # Optional AE-1A blocks. Absent block → no validation. Present-but-malformed
    # block → ValueError. Loader does not require these to be filled in (firms
    # that don't submit AE-1A leave them absent); the AE-1A populator does its
    # own filled-content check at run time.
    if "insurance" in raw:
        _validate_insurance_block(raw["insurance"], source=p)
    if "swam" in raw:
        _validate_swam_block(raw["swam"], source=p)
    if "agency_contracts" in raw:
        _validate_agency_contracts(raw["agency_contracts"], source=p)
    if "narratives" in raw:
        _validate_narratives_block(raw["narratives"], source=p)

    return raw


def _validate_firm_block(firm: Any, *, source: Path) -> None:
    if not isinstance(firm, dict):
        raise ValueError(f"{source}: 'firm' block missing or not a mapping.")
    for field in _REQUIRED_FIRM_FIELDS:
        _require_filled(firm, field, parent="firm", source=source)


def _validate_ownership_block(ownership: Any, *, source: Path) -> None:
    if not isinstance(ownership, dict):
        raise ValueError(
            f"{source}: 'ownership' block missing or not a mapping."
        )
    for field in _REQUIRED_OWNERSHIP_FIELDS:
        if field not in ownership:
            raise ValueError(
                f"{source}: required field 'ownership.{field}' is missing."
            )
        if not isinstance(ownership[field], bool):
            raise ValueError(
                f"{source}: 'ownership.{field}' must be true/false, "
                f"got {ownership[field]!r}."
            )


def _validate_contacts_block(contacts: Any, *, source: Path) -> None:
    if not isinstance(contacts, dict):
        raise ValueError(f"{source}: 'contacts' block missing or not a mapping.")
    primary = contacts.get("primary")
    if not isinstance(primary, dict):
        raise ValueError(
            f"{source}: 'contacts.primary' block is required."
        )
    for field in _REQUIRED_CONTACT_FIELDS:
        _require_filled(primary, field, parent="contacts.primary", source=source)

    secondary = contacts.get("secondary")
    if secondary is None:
        return
    if not isinstance(secondary, dict):
        raise ValueError(
            f"{source}: 'contacts.secondary' must be a mapping when present."
        )
    # All-or-nothing: if any secondary field is filled, all must be.
    filled = {f: secondary.get(f) for f in _REQUIRED_CONTACT_FIELDS}
    has_any = any(_is_filled(v) for v in filled.values())
    if not has_any:
        return
    for field in _REQUIRED_CONTACT_FIELDS:
        _require_filled(
            secondary, field, parent="contacts.secondary", source=source,
        )


def _validate_personnel_counts(counts: Any, *, source: Path) -> None:
    if not isinstance(counts, dict):
        raise ValueError(
            f"{source}: 'personnel_counts' block missing or not a mapping."
        )
    for disc in _PERSONNEL_DISCIPLINES:
        if disc not in counts:
            raise ValueError(
                f"{source}: 'personnel_counts.{disc}' is missing."
            )
        row = counts[disc]
        if not isinstance(row, list) or len(row) != 4:
            raise ValueError(
                f"{source}: 'personnel_counts.{disc}' must be a 4-element "
                f"list [licensed_office, unlicensed_office, licensed_firm, "
                f"unlicensed_firm], got {row!r}."
            )
        for i, n in enumerate(row):
            if not isinstance(n, int) or isinstance(n, bool):
                raise ValueError(
                    f"{source}: 'personnel_counts.{disc}[{i}]' must be int, "
                    f"got {n!r}."
                )


def _validate_insurance_block(insurance: Any, *, source: Path) -> None:
    """Validate the optional `insurance:` block when present.

    Schema: `{narrative: <str>}`. Narrative is required when the block is
    present; PLACEHOLDER values are rejected so a partially-edited template
    can't ship into AE-1A.
    """
    if not isinstance(insurance, dict):
        raise ValueError(
            f"{source}: 'insurance' must be a mapping when present, "
            f"got {type(insurance).__name__}."
        )
    _require_filled(insurance, "narrative", parent="insurance", source=source)


def _validate_swam_block(swam: Any, *, source: Path) -> None:
    """Validate the optional `swam:` block when present.

    Schema: `{default_percentage: int, narrative: <str>}`. Both fields
    required when the block is present. `default_percentage` must be an
    int in [0, 100]; narrative rejects PLACEHOLDER.
    """
    if not isinstance(swam, dict):
        raise ValueError(
            f"{source}: 'swam' must be a mapping when present, "
            f"got {type(swam).__name__}."
        )
    if "default_percentage" not in swam:
        raise ValueError(
            f"{source}: 'swam.default_percentage' is required when "
            f"the swam block is present."
        )
    pct = swam["default_percentage"]
    if not isinstance(pct, int) or isinstance(pct, bool):
        raise ValueError(
            f"{source}: 'swam.default_percentage' must be int, got {pct!r}."
        )
    if pct < 0 or pct > 100:
        raise ValueError(
            f"{source}: 'swam.default_percentage' must be in [0, 100], "
            f"got {pct}."
        )
    _require_filled(swam, "narrative", parent="swam", source=source)


_NARRATIVE_FIELDS = (
    "staff_availability",
    "project_methodology",
    "quality_assurance",
)


def _validate_narratives_block(narratives: Any, *, source: Path) -> None:
    """Validate the optional `narratives:` block when present.

    Schema: a mapping with three required string fields when the block
    is present:
        staff_availability   — AE-3 Section 2
        project_methodology  — AE-3 Section 3
        quality_assurance    — AE-3 Section 4

    Each field rejects PLACEHOLDER and empty strings. Unknown extra
    fields are allowed (forward-compatible — additional populators can
    consume more narrative slots without a loader update).
    """
    if not isinstance(narratives, dict):
        raise ValueError(
            f"{source}: 'narratives' must be a mapping when present, "
            f"got {type(narratives).__name__}."
        )
    for field in _NARRATIVE_FIELDS:
        _require_filled(narratives, field, parent="narratives", source=source)


def _validate_agency_contracts(contracts: Any, *, source: Path) -> None:
    """Validate the optional `agency_contracts:` list when present.

    Schema: `list[{agency: str, description: str}]`. Empty list is fine.
    Each entry must be a mapping with both `agency` and `description`
    filled (PLACEHOLDER rejected).
    """
    if not isinstance(contracts, list):
        raise ValueError(
            f"{source}: 'agency_contracts' must be a list when present, "
            f"got {type(contracts).__name__}."
        )
    for i, entry in enumerate(contracts):
        if not isinstance(entry, dict):
            raise ValueError(
                f"{source}: 'agency_contracts[{i}]' must be a mapping, "
                f"got {type(entry).__name__}."
            )
        for field in ("agency", "description"):
            _require_filled(
                entry, field, parent=f"agency_contracts[{i}]", source=source,
            )


def _require_filled(
    block: dict[str, Any], field: str, *, parent: str, source: Path,
) -> None:
    if field not in block:
        raise ValueError(
            f"{source}: required field '{parent}.{field}' is missing."
        )
    val = block[field]
    if not _is_filled(val):
        raise ValueError(
            f"{source}: required field '{parent}.{field}' is empty."
        )
    if isinstance(val, str) and val.lstrip().startswith(PLACEHOLDER_PREFIX):
        raise ValueError(
            f"{source}: '{parent}.{field}' still holds the {PLACEHOLDER_PREFIX!r} "
            f"template marker — replace with the firm's actual value."
        )


def _is_filled(val: Any) -> bool:
    if val is None:
        return False
    if isinstance(val, str) and val.strip() == "":
        return False
    return True
