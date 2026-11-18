#!/usr/bin/env python3
"""scripts/populate_ae_forms.py

Populate DGS-30-004 AE-1 through AE-6 forms (and SF330 Part 2 stub) from
content_library/ + ~/.bfa/firm_profile.yml + proposal_digest output.

Architecture:
    - argument parsing + repo-root resolution
    - content_library + firm_profile pre-flight (refuse on [VERIFY] /
      PLACEHOLDER residue)
    - form-list parsing from
      scripts/scaffold/proposal_types/ae_term_contract.yml
    - populator dispatch by `code`
    See `Per-tab populator status` below for the per-form delivery state.

CLI:
    python scripts/populate_ae_forms.py
    python scripts/populate_ae_forms.py --list           # show enabled forms, exit
    python scripts/populate_ae_forms.py --only AE-1,AE-3 # subset
    python scripts/populate_ae_forms.py --repo-root DIR  # override autodetect
    python scripts/populate_ae_forms.py --templates DIR  # override template dir
    python scripts/populate_ae_forms.py --output DIR     # override output dir

Exit codes:
    0 — all selected populators ran (or `--list` printed cleanly)
    1 — pre-flight failed, or one or more populators raised
    2 — argument or config error

Pre-flight gates (closes DISC-09, ARCH-08 acceptance):
    - content_library/personnel.csv, firms.csv, projects.csv all parse
      via scripts.lib.csv_renderer; any [VERIFY] in a required cell or
      enum violation fails the run before any workbook is written.
    - ~/.bfa/firm_profile.yml loads via scripts.lib.firm_profile; any
      missing required field, leftover PLACEHOLDER, or bad
      personnel-counts row fails the run.

Form set:
    Defined in scripts/scaffold/proposal_types/ae_term_contract.yml under
    `ae_forms`. Each entry has:
        code         — AE-1, AE-1A, AE-2, AE-3, AE-4, AE-5, AE-6
        cardinality  — once | per_personnel | per_project | per_firm
        enabled      — false skips the form for this proposal type

Per-tab populator status (delivery plan for issue #8):
    AE-1     — implemented (firm_profile-driven, PR #80)
    AE-1A    — implemented (firm_profile + proposal_config.representative_projects)
    AE-2     — implemented (per-firm; mirrors AE-1 cell layout; iterates
                proposal_config.proposed_subconsultants — opt-in by default
                in scripts/scaffold/proposal_types/ae_term_contract.yml)
    AE-3     — implemented (closes DISC-09; firm_profile.narratives + proposal_config.key_personnel)
    AE-4     — implemented (per-personnel; iterates key_personnel slots with personnel_id)
    AE-5     — implemented (per-project; consumes representative_projects +
                projects.csv + project_contacts.csv + project_designers.csv)
    AE-6     — implemented (multi-tab narrative; reads ae6_narrative_path
                markdown; strips markdown + internal refs; paginates)
    SF330 P2 — ARCH-12 (separate proposal type, not this issue)
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import yaml

_REPO_ROOT_FALLBACK = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT_FALLBACK) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT_FALLBACK))

from scripts.lib.ae_form_helpers import (  # noqa: E402
    fill_dgs_header,
    fit_merged_rows,
    load_template,
    save_workbook,
    write_cell,
)
from scripts.lib.csv_renderer import read_csv  # noqa: E402
from scripts.lib.firm_profile import load_firm_profile  # noqa: E402

_PROPOSAL_TYPE_FILE = (
    "scripts/scaffold/proposal_types/ae_term_contract.yml"
)
_PROPOSAL_CONFIG_FILE = "00_admin/proposal_config.yml"

# Default on-disk layout for an AE-pursuit scaffold. Overridable via
# --templates / --output. Each populator owns its own subdirectory under
# the pursuit root; the convention `<key>/AE-N.xlsx` for templates and
# `<key>/filled/` for outputs is set here once.
_AE_DIR_KEYS: dict[str, str] = {
    "AE-1": "ae1_firm_data",
    "AE-1A": "ae1a_swam_certifications",
    "AE-2": "ae2_organizational_chart",
    "AE-3": "ae3_firm_experience",
    "AE-4": "ae4_key_personnel",
    "AE-5": "ae5_example_projects",
    "AE-6": "ae6_technical_narrative",
}


@dataclass(frozen=True)
class AEFormSpec:
    """One entry from the `ae_forms:` block in a proposal_type YAML."""
    code: str
    description: str
    cardinality: str  # once | per_personnel | per_project | per_firm
    enabled: bool


@dataclass
class PopulationContext:
    """Bundle passed to every populator with all loaded inputs.

    Future populators (issue #8 PRs 2-4) take this as their single
    argument. Adding a new input means extending this dataclass, not
    threading a new parameter through every populator signature.
    """
    repo_root: Path
    proposal_config: dict[str, Any]
    firm_profile: dict[str, Any]
    personnel: list[dict[str, Any]]
    firms: list[dict[str, Any]]
    projects: list[dict[str, Any]]
    templates_dir: Path
    output_dir: Path
    # The fields below all default to empty lists so older test
    # `PopulationContext(...)` call sites keep working. Production
    # `_build_context` always passes explicit lists.
    personnel_projects: list[dict[str, Any]] = field(default_factory=list)
    project_contacts: list[dict[str, Any]] = field(default_factory=list)
    project_designers: list[dict[str, Any]] = field(default_factory=list)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns process exit code."""
    args = _parse_args(argv)
    repo_root = args.repo_root.resolve()

    try:
        forms = _load_form_specs(repo_root)
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    selected = _filter_forms(forms, args.only)
    if not selected:
        print("error: no forms selected after applying --only filter.",
              file=sys.stderr)
        return 2

    if args.list:
        _print_form_list(selected)
        return 0

    try:
        ctx = _build_context(
            repo_root,
            templates_override=args.templates,
            output_override=args.output,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"pre-flight failed: {exc}", file=sys.stderr)
        return 1

    return _dispatch(ctx, selected)


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Populate DGS-30-004 AE forms.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--repo-root", type=Path, default=_REPO_ROOT_FALLBACK,
        help="Pursuit repo root (default: parent of this script).",
    )
    parser.add_argument(
        "--templates", type=Path, default=None,
        help="Directory containing AE-N.xlsx templates "
             "(default: <repo-root> with conventional ae*/AE-*.xlsx layout).",
    )
    parser.add_argument(
        "--output", type=Path, default=None,
        help="Output directory for filled forms "
             "(default: <repo-root> with conventional ae*/filled/ layout).",
    )
    parser.add_argument(
        "--only", default=None,
        help="Comma-separated list of form codes to populate "
             "(e.g. 'AE-1,AE-3'). Default: all enabled forms.",
    )
    parser.add_argument(
        "--list", action="store_true",
        help="Print the selected form set and exit.",
    )
    return parser.parse_args(argv)


def _load_form_specs(repo_root: Path) -> list[AEFormSpec]:
    """Read the `ae_forms:` block from the AE term-contract proposal type."""
    p = repo_root / _PROPOSAL_TYPE_FILE
    if not p.is_file():
        raise FileNotFoundError(
            f"proposal-type config not found: {p}. "
            f"Are you running this from an AE-term-contract repo root?"
        )
    with p.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    block = raw.get("ae_forms") if isinstance(raw, dict) else None
    if not isinstance(block, list) or not block:
        raise ValueError(
            f"{p}: 'ae_forms' block missing or empty."
        )

    specs: list[AEFormSpec] = []
    valid_cardinalities = {"once", "per_personnel", "per_project", "per_firm"}
    for entry in block:
        if not isinstance(entry, dict):
            raise ValueError(f"{p}: every ae_forms entry must be a mapping.")
        for field in ("code", "description", "cardinality", "enabled"):
            if field not in entry:
                raise ValueError(
                    f"{p}: ae_forms entry missing required field {field!r}: {entry!r}"
                )
        if entry["cardinality"] not in valid_cardinalities:
            raise ValueError(
                f"{p}: ae_forms entry {entry['code']!r} has invalid "
                f"cardinality {entry['cardinality']!r}; "
                f"must be one of {sorted(valid_cardinalities)}."
            )
        if not isinstance(entry["enabled"], bool):
            raise ValueError(
                f"{p}: ae_forms entry {entry['code']!r} 'enabled' "
                f"must be true/false."
            )
        specs.append(AEFormSpec(
            code=str(entry["code"]),
            description=str(entry["description"]),
            cardinality=str(entry["cardinality"]),
            enabled=bool(entry["enabled"]),
        ))
    return specs


def _filter_forms(
    forms: list[AEFormSpec], only_csv: str | None,
) -> list[AEFormSpec]:
    """Keep enabled forms, optionally restricted by --only."""
    enabled = [f for f in forms if f.enabled]
    if only_csv is None:
        return enabled
    wanted = {tok.strip() for tok in only_csv.split(",") if tok.strip()}
    by_code = {f.code: f for f in forms}
    unknown = wanted - set(by_code)
    if unknown:
        raise SystemExit(
            f"error: unknown form code(s) in --only: {sorted(unknown)}. "
            f"Known: {sorted(by_code)}."
        )
    # --only overrides `enabled: false` so a user can force-populate
    # AE-2 on a pursuit where it's normally skipped.
    return [by_code[code] for code in wanted]


def _print_form_list(forms: list[AEFormSpec]) -> None:
    width = max(len(f.code) for f in forms)
    for f in forms:
        flag = "      " if f.enabled else "[off] "
        print(f"  {flag}{f.code:<{width}}  ({f.cardinality})  {f.description}")


def _build_context(
    repo_root: Path,
    *,
    templates_override: Path | None,
    output_override: Path | None,
) -> PopulationContext:
    """Run pre-flight loads. Raises on any [VERIFY]/PLACEHOLDER residue."""
    config_path = repo_root / _PROPOSAL_CONFIG_FILE
    if not config_path.is_file():
        raise FileNotFoundError(
            f"proposal_config.yml not found at {config_path}. "
            f"This script runs from a scaffolded pursuit repo, not the engine repo."
        )
    with config_path.open("r", encoding="utf-8") as f:
        proposal_config = yaml.safe_load(f) or {}

    firm_profile = load_firm_profile()

    library = repo_root / "content_library"
    personnel = read_csv(library / "personnel.csv")
    firms = read_csv(library / "firms.csv")
    projects = read_csv(library / "projects.csv")
    # Optional content_library tables — pre-flight loads them if present.
    # Populators that don't need a given table work fine with an empty list;
    # populators that do require one raise a clear error at run time.
    personnel_projects = _read_optional_csv(library / "personnel_projects.csv")
    project_contacts = _read_optional_csv(library / "project_contacts.csv")
    project_designers = _read_optional_csv(library / "project_designers.csv")

    templates_dir = templates_override.resolve() if templates_override else repo_root
    output_dir = output_override.resolve() if output_override else repo_root

    return PopulationContext(
        repo_root=repo_root,
        proposal_config=proposal_config,
        firm_profile=firm_profile,
        personnel=personnel,
        firms=firms,
        projects=projects,
        personnel_projects=personnel_projects,
        project_contacts=project_contacts,
        project_designers=project_designers,
        templates_dir=templates_dir,
        output_dir=output_dir,
    )


def _read_optional_csv(path: Path) -> list[dict[str, Any]]:
    """Return parsed CSV rows when the file exists; empty list otherwise."""
    return read_csv(path) if path.is_file() else []


def template_path(ctx: PopulationContext, code: str) -> Path:
    """Resolve the on-disk template path for an AE form `code`.

    Convention: `<templates_dir>/<ae_dir_key>/<code>.xlsx`. The directory
    keys (e.g. `ae1_firm_data`) match the scaffold layout used by every
    AE term-contract pursuit.

    Raises:
        KeyError: `code` is not a known DGS AE form.
    """
    if code not in _AE_DIR_KEYS:
        raise KeyError(f"no template directory mapped for form {code!r}")
    return ctx.templates_dir / _AE_DIR_KEYS[code] / f"{code}.xlsx"


def output_dir_for(ctx: PopulationContext, code: str) -> Path:
    """Resolve the on-disk filled-output directory for an AE form `code`.

    Convention: `<output_dir>/<ae_dir_key>/filled/`.
    """
    if code not in _AE_DIR_KEYS:
        raise KeyError(f"no output directory mapped for form {code!r}")
    return ctx.output_dir / _AE_DIR_KEYS[code] / "filled"


def _dispatch(ctx: PopulationContext, forms: list[AEFormSpec]) -> int:
    """Run each selected populator. Returns 0 if all succeeded, 1 otherwise."""
    failed: list[str] = []
    for spec in forms:
        populator = _POPULATORS.get(spec.code)
        if populator is None:
            print(f"[error] {spec.code}: no populator registered.", file=sys.stderr)
            failed.append(spec.code)
            continue
        print(f"[run]   {spec.code}: {spec.description}")
        try:
            populator(ctx, spec)
        except Exception as exc:  # noqa: BLE001 — surface populator errors
            print(f"[error] {spec.code}: {exc}", file=sys.stderr)
            failed.append(spec.code)

    if failed:
        print(
            f"\nFinished with {len(failed)} unfinished form(s): "
            f"{', '.join(failed)}",
            file=sys.stderr,
        )
        return 1
    print("\nAll selected AE forms populated.")
    return 0


# ─────────────────────────────────────────────────────────────────────────
# Per-form populators.
#
# Each populator takes (ctx, spec) and writes one or more `.xlsx` files
# to `output_dir_for(ctx, spec.code)`. Helpers in scripts.lib.ae_form_helpers
# wrap the openpyxl quirks (merged cells, fit-rows, header anchors).
# ─────────────────────────────────────────────────────────────────────────

# DGS-30-004 12/2025 AE-1 Section 7 (personnel by discipline) row mapping.
# The 14 rows correspond exactly to the 14 disciplines in
# firm_profile.personnel_counts. Per row the form has 4 columns:
#   P{row}  — licensed at the office where work is performed
#   X{row}  — unlicensed at the office where work is performed
#   AF{row} — licensed firm-wide
#   AN{row} — unlicensed firm-wide
_AE1_PERSONNEL_ROWS: dict[str, int] = {
    "project_management": 41,
    "architecture": 42,
    "civil": 43,
    "structural": 44,
    "mechanical": 45,
    "electrical": 46,
    "soils": 47,
    "landscape": 48,
    "interior_design": 49,
    "asbestos": 50,
    "surveyor": 51,
    "construction_admin": 52,
    "cadd": 53,
    "specifications": 54,
}

# DGS-30-004 12/2025 AE-1 Section 4 — legal-form checkboxes.
# Match `firm.legal_form` to its checkbox cell. Match is case-insensitive
# substring on the keys. Only "Professional Corporation" cell (AD20) is
# documented from the VT pursuit; other legal forms render with the
# checkbox blank and a console warning so the user fills it in by hand.
_AE1_LEGAL_FORM_CHECKBOX_CELLS: dict[str, str] = {
    "professional corporation": "AD20",
}


def _populate_ae1(ctx: PopulationContext, spec: AEFormSpec) -> None:
    """Populate AE-1 (Firm Data) for the prime firm.

    Inputs:
        ctx.firm_profile      — full firm_profile.yml contents (ARCH-11)
        ctx.proposal_config   — for opportunity.rfp_number / rfp_title /
                                project_code (DGS header anchors)

    Output:
        <output_dir>/ae1_firm_data/filled/AE-1_<short_name>.xlsx

    Behavior notes:
        - Optional fields (fax, parent_*, dsbsd_cert_number, secondary
          contact, years_under_current_name) leave their cells blank
          when absent. The convention is "blank means manual completion
          OR not applicable" — never `N/A` or `null`.
        - Section 6 (Proposed Subconsultants, rows 32-36) is left blank.
          Per-pursuit sub selection lands in PR 3 alongside AE-2 / AE-3.
        - Legal-form checkbox: only Professional Corporation (AD20) has a
          documented cell. Other legal forms render with the checkbox
          blank and a stderr warning — fill in by hand on the rendered
          workbook until a future PR maps the remaining cell coordinates.
    """
    template = template_path(ctx, spec.code)
    wb = load_template(template)
    ws = wb["AE-1"]

    fp = ctx.firm_profile
    firm = fp["firm"]
    ownership = fp["ownership"]
    contacts = fp["contacts"]
    counts = fp["personnel_counts"]
    opportunity = ctx.proposal_config.get("opportunity", {}) or {}

    fill_dgs_header(
        ws,
        rfp=opportunity.get("rfp_number", ""),
        submitted_by=firm["name"],
        project_title=opportunity.get("rfp_title", ""),
        pc=opportunity.get("project_code"),
    )

    # Section 1 — Firm name & address
    write_cell(ws, "C8",   firm["name"])
    # AR8: years under current name. Treat 0 as "unset" — the form
    # convention is blank-where-no-data rather than literal "0".
    years = firm.get("years_under_current_name")
    write_cell(ws, "AR8", years if years else None)
    write_cell(ws, "C9",   firm["addr1"])
    write_cell(ws, "AC10", firm.get("other_names"))
    write_cell(ws, "C10",  firm["addr2"])
    write_cell(ws, "H12",  firm["phone"])
    write_cell(ws, "T12",  firm.get("fax"))
    write_cell(ws, "H13",  firm["fein"])
    write_cell(ws, "X14",  firm["scc_id"])

    # Section 3 — Parent / home office
    write_cell(ws, "C17", firm.get("parent_name"))
    write_cell(ws, "C18", firm.get("parent_addr"))

    # Section 4 — Ownership classifications & registrations
    legal_form = firm.get("legal_form", "") or ""
    matched_cells = _legal_form_checkbox_cells(legal_form)
    for cell in matched_cells:
        write_cell(ws, cell, "X")
    if not matched_cells and legal_form:
        print(
            f"[warn]  AE-1: legal_form {legal_form!r} has no documented "
            f"checkbox cell — fill the Section 4 legal-form box manually.",
            file=sys.stderr,
        )

    write_cell(ws, "AL17", "X" if ownership["micro_business"] else "")
    write_cell(ws, "AL20", "X" if ownership["minority_owned"] else "")
    write_cell(ws, "AL22", firm["apelscidla"])
    write_cell(ws, "H23",  firm.get("parent_phone"))
    write_cell(ws, "T23",  firm.get("parent_fax"))
    write_cell(ws, "AL23", ownership.get("dsbsd_cert_number"))

    # Section 5 — Principal POCs
    primary = contacts["primary"]
    write_cell(ws, "C27",  primary["name"])
    write_cell(ws, "N27",  primary["title"])
    write_cell(ws, "Y27",  primary["email"])
    write_cell(ws, "AL27", primary["phone"])
    secondary = contacts.get("secondary") or {}
    write_cell(ws, "C28",  secondary.get("name"))
    write_cell(ws, "N28",  secondary.get("title"))
    write_cell(ws, "Y28",  secondary.get("email"))
    write_cell(ws, "AL28", secondary.get("phone"))

    # Section 7 — Personnel by discipline (14 rows × 4 columns).
    # Form convention: zero counts render as blank, not literal "0".
    # write_cell treats 0 as a valid value to write, so this loop
    # filters before the call.
    for discipline, row in _AE1_PERSONNEL_ROWS.items():
        row_counts = counts[discipline]
        for col, val in zip(("P", "X", "AF", "AN"), row_counts):
            if val:
                write_cell(ws, f"{col}{row}", val)

    fit_merged_rows(ws)

    short_name = firm.get("short_name") or "firm"
    out_path = output_dir_for(ctx, spec.code) / f"AE-1_{short_name}.xlsx"
    save_workbook(wb, out_path)
    print(f"        wrote {out_path.relative_to(ctx.output_dir)}")


def _legal_form_checkbox_cells(legal_form: str) -> list[str]:
    """Return cell refs for any documented legal-form checkbox match.

    Match is case-insensitive substring against
    `_AE1_LEGAL_FORM_CHECKBOX_CELLS`. Returns empty list when no token
    matches — the caller decides whether to warn or proceed silently.
    """
    norm = legal_form.lower()
    return [
        cell for token, cell in _AE1_LEGAL_FORM_CHECKBOX_CELLS.items()
        if token in norm
    ]


# DGS-30-004 12/2025 AE-1A row anchors.
#   Sec 10 (Virginia state agency contracts) — rows 25..44 (up to 20 entries)
#   Sec 11 (representative projects 5-row summary) — rows 50..54
_AE1A_AGENCY_CONTRACTS_FIRST_ROW = 25
_AE1A_AGENCY_CONTRACTS_MAX = 20
_AE1A_REPRESENTATIVE_FIRST_ROW = 50
_AE1A_REPRESENTATIVE_MAX = 5


def _populate_ae1a(ctx: PopulationContext, spec: AEFormSpec) -> None:
    """Populate AE-1A (Firm Data continued) for the prime firm.

    Inputs:
        ctx.firm_profile.insurance.narrative          — Sec 8 (C7), required
        ctx.firm_profile.swam.default_percentage      — Sec 9 (V13), required
        ctx.firm_profile.swam.narrative               — Sec 9 (C14), required
        ctx.firm_profile.agency_contracts             — Sec 10 (rows 25-44), optional
        ctx.proposal_config.representative_projects   — Sec 11 (rows 50-54), optional
        ctx.projects (content_library/projects.csv)   — looked up by id from above
        ctx.firm_profile.contacts.primary             — signature lines (I59/I61)
        ctx.proposal_config.opportunity.submission_date — signature date (AD61)

    Output:
        <output_dir>/ae1a_swam_certifications/filled/AE-1A_<short_name>.xlsx

    Behavior notes:
        - The AE-1A header writes ONLY AN3 (RFP) + M5 (firm name). Cells
          M6 / AL6 are part of the Section 8 template header text and
          must NOT be overwritten — fill_dgs_header is intentionally
          not used here.
        - Sec 10 entries beyond row 44 (the 20th entry) are dropped with
          a stderr warning. Age old contracts off the firm-profile list
          rather than relying on this truncation.
        - Sec 11 entries beyond row 54 (the 5th entry) are dropped with
          a stderr warning — AE-1A's table is exactly 5 rows. AE-5 (PR 4)
          consumes the same `representative_projects` list with no cap.
        - Missing project ID in `representative_projects` (no matching
          row in `content_library/projects.csv`) leaves that row blank
          with a stderr warning.
        - Submission date is rendered as "Month DD, YYYY" when
          `proposal_config.opportunity.submission_date` is YYYY-MM-DD;
          any other format is passed through verbatim.

    Raises:
        ValueError: If `firm_profile.insurance.narrative`,
            `firm_profile.swam.default_percentage`, or
            `firm_profile.swam.narrative` is missing or empty. AE-1A
            cannot be rendered without these three fields.
    """
    template = template_path(ctx, spec.code)
    wb = load_template(template)
    ws = wb["AE-1A"]

    fp = ctx.firm_profile
    firm = fp["firm"]
    contacts = fp["contacts"]
    opportunity = ctx.proposal_config.get("opportunity") or {}

    # Header: AN3 + M5 only. M6 and AL6 hold Section 8 template text.
    write_cell(ws, "AN3", opportunity.get("rfp_number", ""))
    write_cell(ws, "M5",  firm["name"])

    # Section 8 — Professional liability insurance narrative
    insurance_block = fp.get("insurance") or {}
    insurance_narrative = (insurance_block.get("narrative") or "").strip()
    if not insurance_narrative:
        raise ValueError(
            "AE-1A: firm_profile.insurance.narrative is required. "
            "Add it to ~/.bfa/firm_profile.yml — see "
            "00_admin/firm_profile.yml.example."
        )
    write_cell(ws, "C7", insurance_narrative)

    # Section 9 — SWaM percentage + narrative
    swam_block = fp.get("swam") or {}
    swam_pct = swam_block.get("default_percentage")
    swam_narrative = (swam_block.get("narrative") or "").strip()
    if swam_pct is None or not swam_narrative:
        raise ValueError(
            "AE-1A: firm_profile.swam.default_percentage and "
            "firm_profile.swam.narrative are both required. "
            "Add them to ~/.bfa/firm_profile.yml."
        )
    write_cell(ws, "V13", swam_pct)
    write_cell(ws, "C14", swam_narrative)

    # Section 10 — Active state agency contracts (up to 20)
    agency_contracts = fp.get("agency_contracts") or []
    if len(agency_contracts) > _AE1A_AGENCY_CONTRACTS_MAX:
        print(
            f"[warn]  AE-1A: agency_contracts has {len(agency_contracts)} "
            f"entries; only the first {_AE1A_AGENCY_CONTRACTS_MAX} fit "
            f"in Section 10 — truncating. Age older contracts off in "
            f"firm_profile.yml.",
            file=sys.stderr,
        )
    for i, contract in enumerate(
        agency_contracts[:_AE1A_AGENCY_CONTRACTS_MAX]
    ):
        row = _AE1A_AGENCY_CONTRACTS_FIRST_ROW + i
        write_cell(ws, f"C{row}", contract.get("agency", ""))
        write_cell(ws, f"V{row}", contract.get("description", ""))

    # Section 11 — 5 representative projects pulled from content_library
    rep_ids = ctx.proposal_config.get("representative_projects") or []
    if len(rep_ids) > _AE1A_REPRESENTATIVE_MAX:
        print(
            f"[warn]  AE-1A: representative_projects has {len(rep_ids)} "
            f"entries; only the first {_AE1A_REPRESENTATIVE_MAX} fit in "
            f"Section 11 — truncating. The full list is consumed by AE-5.",
            file=sys.stderr,
        )
    by_id = {p["id"]: p for p in ctx.projects}
    for i, pid in enumerate(rep_ids[:_AE1A_REPRESENTATIVE_MAX]):
        row = _AE1A_REPRESENTATIVE_FIRST_ROW + i
        proj = by_id.get(pid)
        if proj is None:
            print(
                f"[warn]  AE-1A: representative_projects[{i}] = {pid!r} "
                f"not found in content_library/projects.csv; row {row} blank.",
                file=sys.stderr,
            )
            continue
        write_cell(ws, f"C{row}",  proj["name"])
        write_cell(ws, f"AB{row}", _project_year(proj))
        write_cell(ws, f"AJ{row}", proj["location"])

    # Signature lines
    primary = contacts["primary"]
    write_cell(ws, "I59", primary["name"])
    write_cell(ws, "I61", primary["title"])
    submission = opportunity.get("submission_date")
    if submission:
        write_cell(ws, "AD61", _format_submission_date(str(submission)))

    fit_merged_rows(ws)

    short_name = firm.get("short_name") or "firm"
    out_path = output_dir_for(ctx, spec.code) / f"AE-1A_{short_name}.xlsx"
    save_workbook(wb, out_path)
    print(f"        wrote {out_path.relative_to(ctx.output_dir)}")


def _project_year(row: dict[str, Any]) -> str:
    """Extract a year token for AE-1A Section 11 / AE-5 date columns.

    Prefers `complete_date`'s year (YYYY-MM-DD); falls back to
    `start_date`'s year, then to the literal `complete_date` token
    (e.g. "In Progress"), then to "n.d.". Mirrors csv_renderer's
    private `_project_year` — duplicated here to keep csv_renderer's
    public surface untouched in this PR.
    """
    complete = row.get("complete_date") or ""
    start = row.get("start_date") or ""

    def _yyyy(s: Any) -> str | None:
        if isinstance(s, str) and len(s) >= 4 and s[:4].isdigit():
            return s[:4]
        return None

    return (
        _yyyy(complete)
        or _yyyy(start)
        or (complete if isinstance(complete, str) and complete else None)
        or (start if isinstance(start, str) and start else None)
        or "n.d."
    )


def _format_submission_date(value: str) -> str:
    """Render proposal_config.opportunity.submission_date for AE-1A AD61.

    Converts `YYYY-MM-DD` to `Month DD, YYYY` (e.g. "April 23, 2026").
    Any other format passes through verbatim — the form accepts free
    text in the date cell and pursuits sometimes write "TBD" or a
    quarter ("Q2 2026").
    """
    from datetime import datetime
    try:
        dt = datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return value
    # Cross-platform "no leading zero on day":
    return f"{dt.strftime('%B')} {dt.day}, {dt.year}"


# DGS-30-004 12/2025 AE-2 (Consultant / Other Office Data) — assumed
# to mirror the AE-1 cell layout cell-for-cell. VT pursuit made AE-2 a
# no-op so there's no in-repo precedent. If a future pursuit confirms
# the AE-2 sheet uses different cell anchors, override these constants
# rather than the AE-1 ones.
#
# Section 7 (personnel by discipline, 14 rows) is intentionally NOT
# populated for AE-2 — sub firms typically leave it blank in DGS
# submissions. If a sub does provide counts, add them by hand.

# Map ownership_class → AE-2 Section 4 checkbox cell.
# Cells: micro (AL17), minority/women/veteran/svc-disabled (AL20).
# AL17 and AL20 are documented from AE-1; the form currently exposes
# only those two DBE checkboxes. Other classifications (women, veteran,
# service_disabled_veteran) get a stderr warning rather than silently
# checking the wrong cell.
_AE2_OWNERSHIP_MICRO_CELL = "AL17"
_AE2_OWNERSHIP_MINORITY_CELL = "AL20"
_AE2_DBE_OWNERSHIP_CLASSES = {
    "minority", "women", "veteran", "service_disabled_veteran",
}


def _populate_ae2(ctx: PopulationContext, spec: AEFormSpec) -> None:
    """Populate AE-2 (Consultant / Other Office Data) — one workbook per sub.

    Iterates `proposal_config.proposed_subconsultants` (firm IDs from
    `content_library/firms.csv`). For each ID, renders one AE-2 workbook
    using the AE-1 cell layout (Sections 1, 3, 4, 5; Section 7 skipped).

    Inputs:
        ctx.proposal_config.proposed_subconsultants  — list of firm_ids
        ctx.firms (matched by id)                    — sub firm data
        ctx.firm_profile.firm.name                   — header M5 (prime is
                                                       still the submitter)
        ctx.proposal_config.opportunity              — DGS header anchors

    Output (one per sub):
        <output_dir>/ae2_organizational_chart/filled/AE-2_<firm_id>.xlsx

    Cell-layout assumption:
        AE-2 mirrors AE-1's section/cell layout (DGS-30-004 12/2025).
        Verification needed against the actual DGS template — if AE-2
        is a separate sheet with different cell positions, update the
        cell constants in this function. The dispatch logic and field
        mappings are independent of those constants.

    Behavior:
        - Empty `proposed_subconsultants` → no forms, stderr warning,
          clean exit. Many term-contract pursuits do not submit AE-2
          (subs picked per project order).
        - firm_id not in firms.csv → ValueError (typo or stale id).
        - ownership_class outside {micro, minority} → stderr warning,
          checkbox left blank (form has only those two DBE cells
          documented).
        - Section 7 personnel-by-discipline left blank (subs don't
          typically populate this; firms.csv has no per-discipline
          counts).
        - Secondary POC (Section 5 row 28) left blank — firms.csv has
          one POC; pursuits with multi-POC subs can fill manually.
    """
    sub_ids = ctx.proposal_config.get("proposed_subconsultants") or []
    if not sub_ids:
        print(
            "[warn]  AE-2: proposal_config.proposed_subconsultants is "
            "empty; no AE-2 forms generated.",
            file=sys.stderr,
        )
        return

    firms_by_id = {f["id"]: f for f in ctx.firms}
    fp = ctx.firm_profile
    prime_firm_name = fp["firm"]["name"]
    opportunity = ctx.proposal_config.get("opportunity") or {}

    template = template_path(ctx, spec.code)

    for firm_id in sub_ids:
        sub = firms_by_id.get(firm_id)
        if sub is None:
            raise ValueError(
                f"AE-2: proposed_subconsultants entry {firm_id!r} not "
                f"found in content_library/firms.csv."
            )
        _write_ae2_for_sub(
            ctx,
            spec=spec,
            template=template,
            sub=sub,
            prime_firm_name=prime_firm_name,
            opportunity=opportunity,
        )


def _write_ae2_for_sub(
    ctx: PopulationContext,
    *,
    spec: AEFormSpec,
    template: Path,
    sub: dict[str, Any],
    prime_firm_name: str,
    opportunity: dict[str, Any],
) -> None:
    """Render one AE-2 workbook for one subconsultant."""
    wb = load_template(template)
    ws = wb["AE-2"]

    fill_dgs_header(
        ws,
        rfp=opportunity.get("rfp_number", ""),
        submitted_by=prime_firm_name,
        project_title=opportunity.get("rfp_title", ""),
        pc=opportunity.get("project_code"),
    )

    # Section 1 — Firm name & address (mirror of AE-1 Section 1)
    write_cell(ws, "C8",   sub["name"])
    years = sub.get("years_in_practice")
    write_cell(ws, "AR8",  years if years else None)
    write_cell(ws, "C9",   sub.get("addr1"))
    write_cell(ws, "AC10", sub.get("other_names"))
    write_cell(ws, "C10",  sub.get("addr2"))
    write_cell(ws, "H12",  sub.get("phone"))
    write_cell(ws, "T12",  sub.get("fax"))
    write_cell(ws, "H13",  sub.get("fein"))
    write_cell(ws, "X14",  sub.get("scc_id"))

    # Section 3 — Parent firm (firms.csv has only `parent_firm` name; no
    # parent address/phone/fax columns yet — leave those cells blank).
    write_cell(ws, "C17",  sub.get("parent_firm"))

    # Section 4 — Ownership classifications + registrations
    legal_form = sub.get("legal_form") or ""
    matched_cells = _legal_form_checkbox_cells(legal_form)
    for cell in matched_cells:
        write_cell(ws, cell, "X")
    if not matched_cells and legal_form:
        print(
            f"[warn]  AE-2 ({sub['id']}): legal_form {legal_form!r} has "
            f"no documented checkbox cell — fill the Section 4 legal-form "
            f"box manually.",
            file=sys.stderr,
        )

    ownership_class = (sub.get("ownership_class") or "").strip()
    if ownership_class == "micro":
        write_cell(ws, _AE2_OWNERSHIP_MICRO_CELL, "X")
    elif ownership_class == "minority":
        write_cell(ws, _AE2_OWNERSHIP_MINORITY_CELL, "X")
    elif ownership_class in _AE2_DBE_OWNERSHIP_CLASSES:
        # women / veteran / service_disabled_veteran — no documented
        # cell on the AE-1-mirror layout.
        print(
            f"[warn]  AE-2 ({sub['id']}): ownership_class "
            f"{ownership_class!r} has no documented checkbox cell — "
            f"fill manually.",
            file=sys.stderr,
        )
    # large / small → no checkbox check; the form's Section 4 is
    # intended for DBE classifications.

    write_cell(ws, "AL22", sub.get("apelscidla"))
    write_cell(ws, "AL23", sub.get("dsbsd_cert"))

    # Section 5 — Principal POC (firms.csv has one POC row; secondary
    # left blank for pursuits that need to add a second by hand).
    write_cell(ws, "C27",  sub.get("poc_name"))
    write_cell(ws, "N27",  sub.get("poc_title"))
    write_cell(ws, "Y27",  sub.get("poc_email"))
    write_cell(ws, "AL27", sub.get("poc_phone"))

    fit_merged_rows(ws)

    out_path = output_dir_for(ctx, spec.code) / f"AE-2_{sub['id']}.xlsx"
    save_workbook(wb, out_path)
    print(f"        wrote {out_path.relative_to(ctx.output_dir)}")


# DGS-30-004 12/2025 AE-3 Section 1 — fixed-discipline rows.
# Each ordered tuple is (slot_key_in_proposal_config, row_number).
# The form pre-labels these rows in column C; the populator only writes
# columns L/W/AI (Name / Title / Firm). The optional "Other" slot lives
# at row 17 and includes a discipline label in column C.
_AE3_FIXED_SLOTS: tuple[tuple[str, int], ...] = (
    ("pm",         11),
    ("architect",  12),
    ("structural", 13),
    ("mechanical", 14),
    ("electrical", 15),
    ("civil",      16),
)
_AE3_OTHER_ROW = 17

# AE-3 narrative cell anchors
_AE3_STAFF_AVAILABILITY_CELL = "C20"
_AE3_PROJECT_METHODOLOGY_CELL = "C28"
_AE3_QUALITY_ASSURANCE_CELL = "C44"

# AE-3 signature cells
_AE3_SIGNATURE_NAME_CELL = "I58"
_AE3_SIGNATURE_TITLE_CELL = "I60"
_AE3_SIGNATURE_DATE_CELL = "AE60"


def _populate_ae3(ctx: PopulationContext, spec: AEFormSpec) -> None:
    """Populate AE-3 (Project Staffing Organization).

    Inputs:
        ctx.proposal_config.key_personnel  — pursuit-level slot mapping; each
            slot is one of:
              - {personnel_id: <id>}    (id from content_library/personnel.csv)
              - {name, title, firm}     (inline; for sub-firm or guest staff)
              - null / missing          (slot left blank)
        ctx.personnel                     — content_library/personnel.csv rows;
                                            looked up when slots use personnel_id
        ctx.firm_profile.narratives.{staff_availability,
                                     project_methodology,
                                     quality_assurance}  — Sec 2/3/4 free text
        ctx.firm_profile.contacts.primary  — signature lines (I58/I60)
        ctx.firm_profile.firm.name         — used as `firm` value when a slot
                                              resolves via personnel_id (since
                                              personnel.csv is firm-internal)
        ctx.proposal_config.opportunity.{rfp_number,
                                         rfp_title,
                                         project_code,
                                         submission_date}  — DGS header + date

    Output:
        <output_dir>/ae3_firm_experience/filled/AE-3_<short_name>.xlsx

    DISC-09 close:
        Section 1 is pinned to typed inputs. Each slot resolves to a real
        row in content_library/personnel.csv OR an explicit inline entry —
        no AI-fill, no inference. The "no plausible-but-wrong values"
        guarantee is structural: if a slot is absent or partially filled,
        the row is left blank (visible to reviewers) rather than
        hallucinated.

    Behavior:
        - Slot with both `personnel_id` and inline fields → ValueError
          (mutually exclusive; ambiguous data = refuse rather than guess).
        - Slot with `personnel_id` not in personnel.csv → ValueError
          (typo or stale id; reviewer must fix before output).
        - Slot with partial inline (some of name/title/firm missing) →
          ValueError (incomplete; better to fail than ship a half-row).
        - Slot null / missing → row left blank, no error.
        - More than one `other` entry → only first is written to row 17
          with a stderr warning (AE-3 has a single Other row).

    Raises:
        ValueError: Any of the above slot misconfigurations, OR
            firm_profile.narratives missing/empty for any of the three
            required AE-3 fields.
    """
    template = template_path(ctx, spec.code)
    wb = load_template(template)
    ws = wb["AE-3"]

    fp = ctx.firm_profile
    firm = fp["firm"]
    contacts = fp["contacts"]
    opportunity = ctx.proposal_config.get("opportunity") or {}
    key_personnel = ctx.proposal_config.get("key_personnel") or {}
    personnel_by_id = {p["id"]: p for p in ctx.personnel}
    prime_firm_name = firm["name"]

    fill_dgs_header(
        ws,
        rfp=opportunity.get("rfp_number", ""),
        submitted_by=prime_firm_name,
        project_title=opportunity.get("rfp_title", ""),
        pc=opportunity.get("project_code"),
    )

    # Section 1 — Key personnel table
    for slot_key, row in _AE3_FIXED_SLOTS:
        slot = key_personnel.get(slot_key)
        resolved = _resolve_key_personnel_slot(
            slot, slot_key,
            personnel_by_id=personnel_by_id,
            prime_firm_name=prime_firm_name,
        )
        if resolved is None:
            continue
        write_cell(ws, f"L{row}",  resolved["name"])
        write_cell(ws, f"W{row}",  resolved["title"])
        write_cell(ws, f"AI{row}", resolved["firm"])

    # Row 17 — single "Other" slot
    other_entries = key_personnel.get("other") or []
    if len(other_entries) > 1:
        print(
            f"[warn]  AE-3: key_personnel.other has {len(other_entries)} "
            f"entries; AE-3 has one Other row — writing the first only. "
            f"Add additional roles via AE-6 narrative or a future "
            f"multi-row schema.",
            file=sys.stderr,
        )
    if other_entries:
        first_other = other_entries[0]
        if not isinstance(first_other, dict):
            raise ValueError(
                f"AE-3: key_personnel.other[0] must be a mapping, "
                f"got {type(first_other).__name__}."
            )
        # Other entries must include their own discipline label.
        discipline_label = (first_other.get("title") or "").strip()
        if not discipline_label:
            raise ValueError(
                "AE-3: key_personnel.other[0].title is required "
                "(used as the discipline label in column C)."
            )
        resolved = _resolve_key_personnel_slot(
            first_other, "other[0]",
            personnel_by_id=personnel_by_id,
            prime_firm_name=prime_firm_name,
        )
        if resolved is not None:
            write_cell(ws, f"C{_AE3_OTHER_ROW}", discipline_label)
            write_cell(ws, f"L{_AE3_OTHER_ROW}",  resolved["name"])
            write_cell(ws, f"W{_AE3_OTHER_ROW}",  resolved["title"])
            write_cell(ws, f"AI{_AE3_OTHER_ROW}", resolved["firm"])

    # Sections 2/3/4 — narratives
    narratives = fp.get("narratives") or {}
    for field, cell in (
        ("staff_availability",  _AE3_STAFF_AVAILABILITY_CELL),
        ("project_methodology", _AE3_PROJECT_METHODOLOGY_CELL),
        ("quality_assurance",   _AE3_QUALITY_ASSURANCE_CELL),
    ):
        text = (narratives.get(field) or "").strip()
        if not text:
            raise ValueError(
                f"AE-3: firm_profile.narratives.{field} is required. "
                f"Add it to ~/.bfa/firm_profile.yml — see "
                f"00_admin/firm_profile.yml.example."
            )
        write_cell(ws, cell, text)

    # Signature
    primary = contacts["primary"]
    write_cell(ws, _AE3_SIGNATURE_NAME_CELL,  primary["name"])
    write_cell(ws, _AE3_SIGNATURE_TITLE_CELL, primary["title"])
    submission = opportunity.get("submission_date")
    if submission:
        write_cell(
            ws, _AE3_SIGNATURE_DATE_CELL,
            _format_submission_date(str(submission)),
        )

    fit_merged_rows(ws)

    short_name = firm.get("short_name") or "firm"
    out_path = output_dir_for(ctx, spec.code) / f"AE-3_{short_name}.xlsx"
    save_workbook(wb, out_path)
    print(f"        wrote {out_path.relative_to(ctx.output_dir)}")


def _resolve_key_personnel_slot(
    slot: Any,
    slot_label: str,
    *,
    personnel_by_id: dict[str, dict[str, Any]],
    prime_firm_name: str,
) -> dict[str, str] | None:
    """Resolve an AE-3 / future AE-N key-personnel slot to {name, title, firm}.

    Returns None when the slot is null / missing (caller leaves the row
    blank). Raises ValueError on partial fills, ambiguous slots (both
    `personnel_id` and inline fields), or unresolvable `personnel_id`.

    Args:
        slot: Slot value from proposal_config. Accepted shapes:
            - None / missing  → returns None
            - {personnel_id: <id>}                       → looked up
            - {name, title, firm[, title?]}              → used inline
            - Mapping with both id and inline fields     → ValueError
        slot_label: Human-readable slot identifier for error messages
            (e.g. "pm", "other[0]").
        personnel_by_id: `id`-keyed view of `content_library/personnel.csv`.
        prime_firm_name: Firm name to use as `firm` when resolving via
            personnel_id (personnel.csv is firm-internal by convention).
    """
    if slot is None:
        return None
    if not isinstance(slot, dict):
        raise ValueError(
            f"AE-3: key_personnel.{slot_label} must be a mapping or null, "
            f"got {type(slot).__name__}."
        )

    has_id = bool(slot.get("personnel_id"))
    # `name` and `firm` are inline-only (would conflict with personnel_id
    # lookup). `title` is dual-purpose: required for the inline path,
    # optional override for the personnel_id path.
    inline_only_present = {
        f: bool((slot.get(f) or "").strip()) for f in ("name", "firm")
    }
    has_inline_only = any(inline_only_present.values())

    if has_id and has_inline_only:
        bad = [f for f, present in inline_only_present.items() if present]
        raise ValueError(
            f"AE-3: key_personnel.{slot_label} sets both 'personnel_id' "
            f"and inline field(s) {bad} — when using personnel_id, only "
            f"'title' may be supplied (as a per-pursuit role override)."
        )

    if has_id:
        pid = slot["personnel_id"]
        person = personnel_by_id.get(pid)
        if person is None:
            raise ValueError(
                f"AE-3: key_personnel.{slot_label}.personnel_id={pid!r} "
                f"not found in content_library/personnel.csv."
            )
        # Slot may override the title for this pursuit (e.g., "PM on this
        # contract" vs. their stable title). Default to personnel.csv title.
        title_override = (slot.get("title") or "").strip()
        return {
            "name":  person["name"],
            "title": title_override or person["title"],
            "firm":  prime_firm_name,
        }

    # Inline path. Require name, title, and firm.
    inline_full = {
        f: bool((slot.get(f) or "").strip())
        for f in ("name", "title", "firm")
    }
    missing = [f for f, present in inline_full.items() if not present]
    if missing:
        raise ValueError(
            f"AE-3: key_personnel.{slot_label} inline entry missing "
            f"required field(s): {missing}. Either fill in name/title/firm "
            f"or use personnel_id."
        )
    return {
        "name":  slot["name"].strip(),
        "title": slot["title"].strip(),
        "firm":  slot["firm"].strip(),
    }


# DGS-30-004 12/2025 AE-4 cell anchors.
# Sec 1 personal data (G9..AB24); Sec 2 employer (J20); Sec 3 education
# + registration (C28, C33, I38, AA38); Sec 4 CPSM (Y43, AP43); Sec 6
# specific experience (rows 49,51,53,55,57,59 × cols C/Y/AL); signature
# (I65, I67, AF67).
_AE4_PROJECT_ROWS = (49, 51, 53, 55, 57, 59)
_AE4_PROJECTS_MAX = 6


def _populate_ae4(ctx: PopulationContext, spec: AEFormSpec) -> None:
    """Populate AE-4 (Personnel Qualifications) — one workbook per key person.

    Iterates `proposal_config.key_personnel` slots that resolve to a
    `personnel_id` (the prime-firm path). Each yields one AE-4 workbook.
    Inline / sub-firm slots and `null` slots are skipped (they don't
    submit an AE-4 in the prime's package).

    Inputs per person:
        ctx.personnel (matched by id)        — name, title, office, years_*,
                                                education, license_*, cpsm_*,
                                                registration_line override
        ctx.proposal_config.key_personnel    — duty, assignment, pct (per slot)
        ctx.personnel_projects (filtered)    — Section 6 experience table
        ctx.projects (joined)                — project name + completion date
        ctx.firm_profile.firm.name           — employer cell (J20)
        ctx.firm_profile.contacts.primary    — signature lines (I65/I67)
        ctx.proposal_config.opportunity      — DGS header + signature date

    Output (one per key person):
        <output_dir>/ae4_key_personnel/filled/AE-4_<id>.xlsx

    Behavior:
        - Slot's `personnel_id` not in personnel.csv → ValueError
          (already enforced by _resolve_key_personnel_slot at AE-3 time;
          enforced again here for AE-4-only invocations).
        - Slot missing `duty`, `assignment`, or `pct` → AE-4 cells stay
          blank with a stderr warning (the form accepts blank). Reasoning:
          a pursuit might submit AE-4 forms with hand-filled assignments
          while iterating; halting on absent fields would block.
        - `registration_line` from personnel.csv (if non-empty) is used
          verbatim. Otherwise the populator derives a default from the
          license_* fields. If license_type='none' and no override is set,
          the cell is left blank with a stderr warning.
        - Section 6 takes the first up-to-six rows from
          personnel_projects.csv filtered by personnel_id, sorted by
          (listing_order asc, complete_date desc). Project name comes from
          projects.csv `name`; date from projects.csv `complete_date`
          (formatted M/D/YYYY when YYYY-MM-DD; else passed through).
        - Person with zero personnel_projects rows → Section 6 left blank
          with a stderr warning naming the person.
        - More than 6 rows for a person → first 6 used; stderr warning.
    """
    # Iterate slots that resolve to a personnel_id.
    key_personnel = ctx.proposal_config.get("key_personnel") or {}
    personnel_by_id = {p["id"]: p for p in ctx.personnel}
    fp = ctx.firm_profile
    employer = fp["firm"]["name"]
    contacts = fp["contacts"]
    opportunity = ctx.proposal_config.get("opportunity") or {}

    slots_to_render = list(_iter_ae4_slots(key_personnel))
    if not slots_to_render:
        print(
            "[warn]  AE-4: no key_personnel slot resolved to a personnel_id; "
            "no AE-4 forms generated.",
            file=sys.stderr,
        )
        return

    template = template_path(ctx, spec.code)

    for slot_label, slot in slots_to_render:
        pid = slot["personnel_id"]
        person = personnel_by_id.get(pid)
        if person is None:
            raise ValueError(
                f"AE-4: key_personnel.{slot_label}.personnel_id={pid!r} "
                f"not found in content_library/personnel.csv."
            )
        _write_ae4_for_person(
            ctx,
            spec=spec,
            template=template,
            slot_label=slot_label,
            slot=slot,
            person=person,
            employer=employer,
            contacts=contacts,
            opportunity=opportunity,
        )


def _iter_ae4_slots(
    key_personnel: dict[str, Any],
) -> list[tuple[str, dict[str, Any]]]:
    """Yield (label, slot) pairs for every personnel_id-bearing slot.

    Walks the six fixed slots in order then any `other` entries with a
    `personnel_id`. Entries without `personnel_id` (inline subs, nulls)
    are skipped — those don't get an AE-4 in the prime's package.
    """
    out: list[tuple[str, dict[str, Any]]] = []
    for slot_key, _ in _AE3_FIXED_SLOTS:
        slot = key_personnel.get(slot_key)
        if isinstance(slot, dict) and slot.get("personnel_id"):
            out.append((slot_key, slot))
    for i, slot in enumerate(key_personnel.get("other") or []):
        if isinstance(slot, dict) and slot.get("personnel_id"):
            out.append((f"other[{i}]", slot))
    return out


def _write_ae4_for_person(
    ctx: PopulationContext,
    *,
    spec: AEFormSpec,
    template: Path,
    slot_label: str,
    slot: dict[str, Any],
    person: dict[str, Any],
    employer: str,
    contacts: dict[str, Any],
    opportunity: dict[str, Any],
) -> None:
    """Render one AE-4 workbook for one person."""
    wb = load_template(template)
    ws = wb["AE-4"]

    fill_dgs_header(
        ws,
        rfp=opportunity.get("rfp_number", ""),
        submitted_by=employer,
        project_title=opportunity.get("rfp_title", ""),
        pc=opportunity.get("project_code"),
    )

    # Sec 1 — personal data
    title_for_form = (slot.get("title") or "").strip() or person["title"]
    write_cell(ws, "G9",   person["name"])
    write_cell(ws, "G10",  title_for_form)
    write_cell(ws, "AH10", person.get("office"))

    # Pursuit-level fields. Warn rather than raise — partial AE-4 forms
    # are common during proposal-prep iteration.
    duty = (slot.get("duty") or "").strip()
    assignment = (slot.get("assignment") or "").strip()
    pct = slot.get("pct")
    if not duty:
        print(
            f"[warn]  AE-4: key_personnel.{slot_label}.duty is blank; "
            f"P11 left empty.",
            file=sys.stderr,
        )
    if not assignment:
        print(
            f"[warn]  AE-4: key_personnel.{slot_label}.assignment is blank; "
            f"P14 left empty.",
            file=sys.stderr,
        )
    write_cell(ws, "P11",  duty)
    write_cell(ws, "P14",  assignment)
    write_cell(ws, "AH17", pct)

    # Sec 2 — employer + experience years
    write_cell(ws, "J20",  employer)
    write_cell(ws, "J24",  person.get("years_total"))
    write_cell(ws, "AB24", person.get("years_firm"))

    # Sec 3 — education + registration
    write_cell(ws, "C28",  person.get("education"))

    reg_line = (person.get("registration_line") or "").strip()
    if not reg_line:
        reg_line = _derive_registration_line(person, slot_label=slot_label)
    write_cell(ws, "C33", reg_line or None)

    # arch_num cell (I38) is left blank — schema doesn't currently model
    # registered architects, and the populator can't infer one from the
    # M&E discipline enum. eng_num cell (AA38) takes the license number.
    write_cell(ws, "AA38", person.get("license_number"))

    # Sec 4 — CPSM
    write_cell(ws, "Y43",  person.get("cpsm_status"))
    write_cell(ws, "AP43", person.get("cpsm_date"))

    # Sec 6 — specific experience (up to 6 projects)
    rows = _select_personnel_projects(
        ctx, personnel_id=person["id"], slot_label=slot_label,
    )
    project_by_id = {p["id"]: p for p in ctx.projects}
    for i, link in enumerate(rows[:_AE4_PROJECTS_MAX]):
        cell_row = _AE4_PROJECT_ROWS[i]
        proj = project_by_id.get(link["project_id"])
        if proj is None:
            print(
                f"[warn]  AE-4 ({slot_label}): personnel_projects row "
                f"references project_id={link['project_id']!r} not in "
                f"projects.csv; skipping.",
                file=sys.stderr,
            )
            continue
        write_cell(ws, f"C{cell_row}",  proj["name"])
        write_cell(ws, f"Y{cell_row}",  link["role"])
        write_cell(
            ws, f"AL{cell_row}",
            _format_project_date(proj.get("complete_date")),
        )

    # Signature
    primary = contacts["primary"]
    write_cell(ws, "I65",  primary["name"])
    write_cell(ws, "I67",  primary["title"])
    submission = opportunity.get("submission_date")
    if submission:
        write_cell(ws, "AF67", _format_submission_date(str(submission)))

    fit_merged_rows(ws)

    out_path = output_dir_for(ctx, spec.code) / f"AE-4_{person['id']}.xlsx"
    save_workbook(wb, out_path)
    print(f"        wrote {out_path.relative_to(ctx.output_dir)}")


def _select_personnel_projects(
    ctx: PopulationContext,
    *,
    personnel_id: str,
    slot_label: str,
) -> list[dict[str, Any]]:
    """Filter + sort personnel_projects rows for one person.

    Sort key: (listing_order asc, project complete_date desc, project_id
    asc as a stable tiebreak). `listing_order` defaults to 0 when missing.
    Warns to stderr if zero rows or more than _AE4_PROJECTS_MAX.
    """
    by_pid = [
        r for r in ctx.personnel_projects
        if r.get("personnel_id") == personnel_id
    ]
    if not by_pid:
        print(
            f"[warn]  AE-4 ({slot_label}): personnel_projects.csv has no "
            f"rows for personnel_id={personnel_id!r}; Section 6 left blank.",
            file=sys.stderr,
        )
        return []

    project_by_id = {p["id"]: p for p in ctx.projects}

    def sort_key(row: dict[str, Any]) -> tuple[int, str, str]:
        proj = project_by_id.get(row.get("project_id"))
        complete = (proj or {}).get("complete_date") or ""
        # Sort newest first → reverse the date string, fall back to far past.
        # Python sorts strings lexicographically; YYYY-MM-DD is sort-friendly.
        # Use a leading minus by inverting via a fixed-length subtraction.
        date_key = complete if complete and complete[:4].isdigit() else "0000"
        # Reverse-sort dates by negating: lower is "newer"
        # Fixed-length transform: invert each digit in the year.
        inverted_year = "".join(str(9 - int(c)) for c in date_key[:4])
        return (
            row.get("listing_order") or 0,
            inverted_year,
            str(row.get("project_id", "")),
        )

    sorted_rows = sorted(by_pid, key=sort_key)
    if len(sorted_rows) > _AE4_PROJECTS_MAX:
        print(
            f"[warn]  AE-4 ({slot_label}): personnel_projects has "
            f"{len(sorted_rows)} rows for {personnel_id!r}; AE-4 has 6 "
            f"slots — using the first 6 by (listing_order, complete_date desc).",
            file=sys.stderr,
        )
    return sorted_rows


def _derive_registration_line(
    person: dict[str, Any],
    *,
    slot_label: str,
) -> str:
    """Build a default AE-4 C33 registration line from personnel.csv fields.

    Patterns (mirror common BFA submissions):
        PE  → "<year> / <state> / Professional <discipline> Engineer"
        EIT → "<state> EIT — <discipline> (Engineer-in-Training)"
        CPD → "ASPE Certified Plumbing Designer (CPD) — License #<num>"
        none / missing → "" (caller writes None; warns to stderr)

    Returns "" when the personnel row lacks the data needed to build any
    of the patterns. Callers should treat empty as "leave the cell blank
    and let the user fill in by hand."
    """
    license_type = (person.get("license_type") or "").strip()
    license_state = (person.get("license_state") or "").strip()
    license_year = person.get("license_year")
    license_number = (person.get("license_number") or "").strip()
    discipline = (person.get("discipline") or "").strip()
    discipline_label = _format_discipline_for_reg_line(discipline)

    if license_type == "PE":
        if not (license_year and license_state and discipline_label):
            print(
                f"[warn]  AE-4 ({slot_label}): PE registration line "
                f"could not be derived (missing license_year, license_state, "
                f"or discipline); set registration_line override on personnel.csv.",
                file=sys.stderr,
            )
            return ""
        return (
            f"{license_year} / {license_state} / "
            f"Professional {discipline_label} Engineer"
        )
    if license_type == "EIT":
        if not (license_state and discipline_label):
            print(
                f"[warn]  AE-4 ({slot_label}): EIT registration line "
                f"could not be derived; set registration_line override on "
                f"personnel.csv.",
                file=sys.stderr,
            )
            return ""
        return (
            f"{license_state} EIT — {discipline_label} "
            f"(Engineer-in-Training)"
        )
    if license_type == "CPD":
        if license_number:
            return (
                f"ASPE Certified Plumbing Designer (CPD) "
                f"— License #{license_number}"
            )
        return "ASPE Certified Plumbing Designer (CPD)"

    # license_type in {"none", "", missing}
    print(
        f"[warn]  AE-4 ({slot_label}): unlicensed personnel and no "
        f"registration_line override on personnel.csv; C33 left blank. "
        f"Set personnel.registration_line to describe the situation "
        f"(foreign credential, ASPE designation, etc.).",
        file=sys.stderr,
    )
    return ""


def _format_discipline_for_reg_line(discipline: str) -> str:
    """Turn personnel.csv `discipline` into an AE-4-line capitalized noun.

    `electrical` → `Electrical`; `mechanical` → `Mechanical`. Returns
    empty string for non-engineer disciplines (`pm`, `cadd`, `other`)
    where the "Professional X Engineer" pattern doesn't apply.
    """
    if discipline in {"electrical", "mechanical", "plumbing", "controls"}:
        return discipline.capitalize()
    return ""


def _format_project_date(value: Any) -> str | None:
    """Render projects.csv `complete_date` for AE-4 cell AL{row}.

    YYYY-MM-DD → M/D/YYYY (e.g. "2024-08-30" → "8/30/2024"); other
    string values pass through (e.g. "In Progress", "Ongoing"). None /
    empty → None (cell stays blank).
    """
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    from datetime import datetime
    try:
        dt = datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        return s
    return f"{dt.month}/{dt.day}/{dt.year}"


# DGS-30-004 12/2025 AE-5 anchors.
# Section 4 — Key designers: 7 fixed-discipline rows. Discipline → row
# mapping is the contract for project_designers.csv; row 27 is "Other"
# and uses col C for the discipline label (the populator writes the
# `role` text there since that's what column C asks for).
_AE5_DESIGNER_ROWS: dict[str, int] = {
    "prime_ae":      21,
    "architectural": 22,
    "structural":    23,
    "mechanical":    24,
    "electrical":    25,
    "civil":         26,
    "other":         27,
}

# Section 5 — Codes table: VUSBC / IBC / NFPA 101 (life safety) / ASAD
# (accessibility — Architectural Standards for Aged or Disabled) / ADAAG.
# `codes_used` semicolon-list tokens map to these cells; unrecognized
# tokens warn (they may be in `codes_other` instead).
_AE5_CODE_CELLS: dict[str, str] = {
    "VUSBC":       "C30",
    "IBC":         "H30",
    "life_safety": "L30",
    "ASAD":        "S30",
    "ADAAG":       "X30",
}


def _populate_ae5(ctx: PopulationContext, spec: AEFormSpec) -> None:
    """Populate AE-5 (Representative Project Data) — one workbook per project.

    Iterates `proposal_config.representative_projects` (the pursuit-selected
    project IDs). For each ID:
      1. Looks up the project row in `content_library/projects.csv`
      2. Joins `project_contacts.csv` (admin + construction prime + supt)
      3. Joins `project_designers.csv` (up to 7 design-team rows)
      4. Renders cells across Sections 2/4/5/6/7/8 + signature

    Inputs (per project):
        ctx.projects (matched by id)             — Sec 2 + 6 + 7 (most cells)
        ctx.project_contacts (filtered by id)    — Sec 2 contact rows
        ctx.project_designers (filtered by id)   — Sec 4 designer table
        ctx.firm_profile.contacts.primary        — signature lines
        ctx.proposal_config.opportunity          — header + signature date

    Output (one per representative project):
        <output_dir>/ae5_example_projects/filled/AE-5_<project_id>.xlsx

    Behavior:
        - `representative_projects` empty → no forms, stderr warning, exit clean.
        - project_id not in projects.csv → ValueError (typo or stale id).
        - Missing optional fields → cells stay blank (DGS form aesthetic).
        - `codes_used` token not in the standard 5 → stderr warning;
          unmapped tokens are ignored (use `codes_other` for free text).
        - Multiple project_designers rows with the same discipline →
          the LAST one wins (the form has one slot per discipline);
          stderr warning.
    """
    rep_ids = ctx.proposal_config.get("representative_projects") or []
    if not rep_ids:
        print(
            "[warn]  AE-5: proposal_config.representative_projects is empty; "
            "no AE-5 forms generated.",
            file=sys.stderr,
        )
        return

    project_by_id = {p["id"]: p for p in ctx.projects}
    contacts_by_project: dict[str, list[dict[str, Any]]] = {}
    for c in ctx.project_contacts:
        contacts_by_project.setdefault(c["project_id"], []).append(c)
    designers_by_project: dict[str, list[dict[str, Any]]] = {}
    for d in ctx.project_designers:
        designers_by_project.setdefault(d["project_id"], []).append(d)

    template = template_path(ctx, spec.code)
    fp = ctx.firm_profile
    contacts = fp["contacts"]
    opportunity = ctx.proposal_config.get("opportunity") or {}
    employer = fp["firm"]["name"]

    for pid in rep_ids:
        project = project_by_id.get(pid)
        if project is None:
            raise ValueError(
                f"AE-5: representative_projects entry {pid!r} not found in "
                f"content_library/projects.csv."
            )
        _write_ae5_for_project(
            ctx,
            spec=spec,
            template=template,
            project=project,
            project_contacts=contacts_by_project.get(pid, []),
            project_designers=designers_by_project.get(pid, []),
            employer=employer,
            primary_contact=contacts["primary"],
            opportunity=opportunity,
        )


def _write_ae5_for_project(
    ctx: PopulationContext,
    *,
    spec: AEFormSpec,
    template: Path,
    project: dict[str, Any],
    project_contacts: list[dict[str, Any]],
    project_designers: list[dict[str, Any]],
    employer: str,
    primary_contact: dict[str, Any],
    opportunity: dict[str, Any],
) -> None:
    """Render one AE-5 workbook for one project."""
    wb = load_template(template)
    ws = wb["AE-5"]

    fill_dgs_header(
        ws,
        rfp=opportunity.get("rfp_number", ""),
        submitted_by=employer,
        project_title=opportunity.get("rfp_title", ""),
        pc=opportunity.get("project_code"),
    )

    # Sec 2 — Project identification
    write_cell(ws, "J7",   project["name"])
    write_cell(ws, "J9",   project.get("project_type"))
    write_cell(ws, "AD9",  project["location"])
    write_cell(ws, "G10",  project["client"])
    _write_ae5_admin_contact(ws, project_contacts, slot_label=project["id"])
    _write_ae5_construction_contacts(
        ws, project_contacts, slot_label=project["id"],
    )

    # Sec 4 — Designers (up to 7 rows by discipline)
    _write_ae5_designers(ws, project_designers, slot_label=project["id"])

    # Sec 5 — Codes
    _write_ae5_codes(ws, project, slot_label=project["id"])

    # Sec 6 — Description
    write_cell(ws, "C33", project.get("scope_summary"))

    # Sec 7 — Construction data
    write_cell(ws, "I41",  project.get("building_type"))
    write_cell(ws, "I42",  project.get("gross_sf"))
    write_cell(ws, "AF42", _format_project_date(project.get("design_start_date")))
    write_cell(ws, "AK42", _format_project_date(project.get("design_complete_date")))
    write_cell(ws, "AF43", _format_project_date(project.get("start_date")))
    write_cell(ws, "AK43", _format_project_date(project.get("complete_date")))
    write_cell(ws, "N44",  project.get("num_floors"))
    write_cell(ws, "K45",  project.get("owner_budget"))
    write_cell(ws, "AH45", project.get("num_change_orders"))
    write_cell(ws, "K46",  project.get("ae_estimate"))
    write_cell(ws, "AH46", project.get("cost_change_orders"))
    write_cell(ws, "K47",  project.get("low_bid"))
    write_cell(ws, "AH47", _format_project_date(project.get("substantial_completion")))

    # Sec 8 — SWaM
    write_cell(ws, "L50", project.get("swam_proposed_pct"))
    write_cell(ws, "Z50", project.get("swam_final_pct"))
    write_cell(ws, "C51", project.get("swam_description"))

    # Signature
    write_cell(ws, "I58",  primary_contact["name"])
    write_cell(ws, "I60",  primary_contact["title"])
    submission = opportunity.get("submission_date")
    if submission:
        write_cell(ws, "AD60", _format_submission_date(str(submission)))

    fit_merged_rows(ws)

    out_path = output_dir_for(ctx, spec.code) / f"AE-5_{project['id']}.xlsx"
    save_workbook(wb, out_path)
    print(f"        wrote {out_path.relative_to(ctx.output_dir)}")


def _write_ae5_admin_contact(
    ws: Any,
    project_contacts: list[dict[str, Any]],
    *,
    slot_label: str,
) -> None:
    """Section 2 admin POC rows (cells L11 / AE11 / G12 / AI12-AI14).

    `admin` role from project_contacts.csv. Missing → cells stay blank.
    """
    admin = next(
        (c for c in project_contacts if c.get("role") == "admin"),
        None,
    )
    if admin is None:
        return
    write_cell(ws, "L11",  admin.get("name"))
    write_cell(ws, "AE11", admin.get("title"))
    write_cell(ws, "G12",  admin.get("addr"))
    write_cell(ws, "AI12", admin.get("email"))
    write_cell(ws, "AI13", admin.get("phone"))
    write_cell(ws, "AI14", admin.get("fax"))


def _write_ae5_construction_contacts(
    ws: Any,
    project_contacts: list[dict[str, Any]],
    *,
    slot_label: str,
) -> None:
    """Section 2 construction-prime PM + Supt rows (L15, J16, AI16, J17, AI17).

    Two distinct project_contacts roles:
        - construction_prime_pm  → firm (L15), name (J16), phone (AI16)
        - construction_supt      → name (J17), fax (AI17 — supt's fax)

    Either or both may be missing; missing cells stay blank.
    """
    pm = next(
        (c for c in project_contacts
         if c.get("role") == "construction_prime_pm"),
        None,
    )
    if pm is not None:
        write_cell(ws, "L15",  pm.get("firm"))
        write_cell(ws, "J16",  pm.get("name"))
        write_cell(ws, "AI16", pm.get("phone"))

    supt = next(
        (c for c in project_contacts
         if c.get("role") == "construction_supt"),
        None,
    )
    if supt is not None:
        write_cell(ws, "J17",  supt.get("name"))
        write_cell(ws, "AI17", supt.get("fax"))


def _write_ae5_designers(
    ws: Any,
    project_designers: list[dict[str, Any]],
    *,
    slot_label: str,
) -> None:
    """Section 4 — designer rows by discipline.

    The form has 7 fixed-discipline rows. Multiple CSV rows for the same
    discipline on a project → last one wins (form has one slot per
    discipline) with a stderr warning. The `other` discipline writes
    `role` to col C as the discipline label per the form's layout.
    """
    by_discipline: dict[str, dict[str, Any]] = {}
    for d in project_designers:
        disc = d.get("discipline")
        if disc in by_discipline:
            print(
                f"[warn]  AE-5 ({slot_label}): multiple project_designers "
                f"rows for discipline={disc!r}; the last one wins. "
                f"Form has one slot per discipline.",
                file=sys.stderr,
            )
        by_discipline[disc] = d

    for discipline, row in _AE5_DESIGNER_ROWS.items():
        designer = by_discipline.get(discipline)
        if designer is None:
            continue
        if discipline == "other":
            write_cell(ws, f"C{row}", designer["role"])
        write_cell(ws, f"K{row}",  designer["firm"])
        write_cell(ws, f"X{row}",  designer["individual"])
        write_cell(ws, f"AI{row}", designer["role"])


def _write_ae5_codes(
    ws: Any,
    project: dict[str, Any],
    *,
    slot_label: str,
) -> None:
    """Section 5 — checkbox cells for codes_used + free-text codes_other.

    `codes_used` is a semicolon-list. Tokens matching `_AE5_CODE_CELLS`
    write `"X"` to their checkbox cell; unrecognized tokens warn (the
    user may have meant to put them in `codes_other`).
    `codes_other` is free text written verbatim to AI30.
    """
    tokens = project.get("codes_used") or []
    if isinstance(tokens, str):
        # Defensive: a non-list value can sneak past schema if a custom
        # schema doesn't include `codes_used` in its `lists` set.
        tokens = [t.strip() for t in tokens.split(";") if t.strip()]
    for token in tokens:
        cell = _AE5_CODE_CELLS.get(token)
        if cell is None:
            print(
                f"[warn]  AE-5 ({slot_label}): codes_used token {token!r} "
                f"is not a standard code (expected one of "
                f"{sorted(_AE5_CODE_CELLS)}). Use codes_other for "
                f"non-standard codes.",
                file=sys.stderr,
            )
            continue
        write_cell(ws, cell, "X")

    write_cell(ws, "AI30", project.get("codes_other"))


# DGS-30-004 12/2025 AE-6 cell anchors.
# C8 is the merged content area (~45 rows × 12.75pt); pagination caps a
# tab at _AE6_TAB_MAX_CHARS so wrapped text fits.
_AE6_CONTENT_CELL = "C8"
_AE6_SIGNATURE_NAME_CELL = "I57"
_AE6_SIGNATURE_TITLE_CELL = "I59"
_AE6_SIGNATURE_DATE_CELL = "AE59"
_AE6_TAB_MAX_CHARS = 4500
_AE6_TAB_NAME_MAX = 31  # Excel sheet-name length limit
_AE6_DEFAULT_NARRATIVE_PATH = "ae6_technical_narrative/ae6_narrative_draft.md"


def _populate_ae6(ctx: PopulationContext, spec: AEFormSpec) -> None:
    """Populate AE-6 (Supplemental Information) — multi-tab narrative workbook.

    Reads a per-pursuit markdown draft, splits on `## Section N — Title`
    headings, and creates one Excel tab per section. Long sections are
    paginated across continuation tabs to fit AE-6's content cell.

    Inputs:
        proposal_config.ae6_narrative_path  — relative path under repo root;
                                               default: ae6_technical_narrative/
                                               ae6_narrative_draft.md
        firm_profile.contacts.primary       — signature lines (last tab only)
        proposal_config.opportunity         — DGS header + signature date

    Output (single workbook with multiple sheets):
        <output_dir>/ae6_technical_narrative/filled/AE-6_<short_name>.xlsx

    Markdown processing:
        1. Split on `## Section ` headings; each chunk → one tab.
        2. Build short tab name `S<N> <title>` (≤31 chars).
        3. Strip internal proposal-shred refs (EVAL-NNN / TECH-NNN / REQ-NNN).
        4. Strip markdown syntax (bold/italic/headings/blockquotes/HRs).
        5. Paginate any chunk >4500 chars at paragraph boundaries; later
           parts get `(2)`, `(3)` etc. suffixes.

    Behavior:
        - Narrative file missing → single tab with `[VERIFY: ...]`
          placeholder pointing at the missing path. The user can then
          create the file; sanity_check.py refuses publish on `[VERIFY]`.
        - Empty narrative file → single tab with the same placeholder.
        - Signature only on the LAST tab (matches DGS form conventions —
          one signed cover for the supplemental section).
        - First tab uses the original AE-6 sheet (renamed); subsequent
          tabs are `wb.copy_worksheet(ws)` clones to preserve formatting.
    """
    fp = ctx.firm_profile
    contacts = fp["contacts"]
    employer = fp["firm"]["name"]
    opportunity = ctx.proposal_config.get("opportunity") or {}

    narrative_rel = (
        ctx.proposal_config.get("ae6_narrative_path")
        or _AE6_DEFAULT_NARRATIVE_PATH
    )
    narrative_path = ctx.repo_root / narrative_rel

    sections = _paginate_ae6_sections(
        _parse_ae6_sections(narrative_path),
        max_chars=_AE6_TAB_MAX_CHARS,
    )

    template = template_path(ctx, spec.code)
    wb = load_template(template)
    ws = wb["AE-6"]

    primary = contacts["primary"]
    submission = opportunity.get("submission_date")
    signature_date = (
        _format_submission_date(str(submission)) if submission else None
    )
    header_args = dict(
        rfp=opportunity.get("rfp_number", ""),
        submitted_by=employer,
        project_title=opportunity.get("rfp_title", ""),
        pc=opportunity.get("project_code"),
    )

    # First tab uses the original sheet (renamed).
    first_tab, first_content = sections[0]
    ws.title = first_tab[:_AE6_TAB_NAME_MAX]
    _fill_ae6_tab(
        ws, header_args=header_args, content=first_content,
        sign=(len(sections) == 1),
        signer_name=primary["name"],
        signer_title=primary["title"],
        signer_date=signature_date,
    )

    # Shorten source title before copying — copy_worksheet appends " Copy",
    # which would push us past Excel's 31-char limit on long names.
    ws.title = ws.title[:25]

    for i, (tab_name, content) in enumerate(sections[1:], start=1):
        new_ws = wb.copy_worksheet(ws)  # preserves formatting
        new_ws.title = tab_name[:_AE6_TAB_NAME_MAX]
        _fill_ae6_tab(
            new_ws, header_args=header_args, content=content,
            sign=(i == len(sections) - 1),
            signer_name=primary["name"],
            signer_title=primary["title"],
            signer_date=signature_date,
        )

    # Restore the original tab title to its full pretty form (we shortened
    # it above only to keep the copy-worksheet name within Excel's limit).
    ws.title = first_tab[:_AE6_TAB_NAME_MAX]

    fit_merged_rows(ws)

    short_name = fp["firm"].get("short_name") or "firm"
    out_path = output_dir_for(ctx, spec.code) / f"AE-6_{short_name}.xlsx"
    save_workbook(wb, out_path)
    print(
        f"        wrote {out_path.relative_to(ctx.output_dir)} "
        f"({len(sections)} tabs)"
    )


def _fill_ae6_tab(
    ws: Any,
    *,
    header_args: dict[str, Any],
    content: str,
    sign: bool,
    signer_name: str | None,
    signer_title: str | None,
    signer_date: str | None,
) -> None:
    """Fill one AE-6 tab: header anchors + content cell + optional signature."""
    fill_dgs_header(ws, **header_args)
    write_cell(ws, _AE6_CONTENT_CELL, content)
    if sign:
        write_cell(ws, _AE6_SIGNATURE_NAME_CELL, signer_name)
        write_cell(ws, _AE6_SIGNATURE_TITLE_CELL, signer_title)
        write_cell(ws, _AE6_SIGNATURE_DATE_CELL, signer_date)


def _parse_ae6_sections(path: Path) -> list[tuple[str, str]]:
    """Parse the AE-6 narrative markdown into per-tab chunks.

    Returns a list of `(short_tab_name, full_section_text)` tuples where:
        - `short_tab_name` is `S<N> <title>` (≤ 31 chars), built from
          headings of the form `## Section <N> — <title>`. Headings that
          don't match the pattern fall back to the raw heading text.
        - `full_section_text` is the section body with internal refs
          stripped (EVAL/TECH/REQ codes) and markdown decorations cleaned
          for plain-text Excel rendering.

    Missing or empty file → single placeholder tuple
    `("AE-6", "[VERIFY: paste narrative — see <path>]")`. The `[VERIFY]`
    marker triggers sanity_check.py to refuse publish.
    """
    if not path.is_file():
        return [
            ("AE-6", f"[VERIFY: paste narrative — see {path}]"),
        ]
    txt = path.read_text(encoding="utf-8").strip()
    if not txt:
        return [
            ("AE-6", f"[VERIFY: narrative file empty — see {path}]"),
        ]

    import re

    raw_chunks = re.split(r"(?=^## )", txt, flags=re.MULTILINE)
    sections: list[tuple[str, str]] = []
    for chunk in raw_chunks:
        chunk = chunk.strip()
        if not chunk or not chunk.startswith("## "):
            continue
        first_line = chunk.splitlines()[0]
        match = re.match(
            r"## Section (\d+)\s*[—\-]+\s*(.*)", first_line,
        )
        if match:
            num, title = match.group(1), match.group(2).strip()
            title = re.sub(r"[*_`]", "", title)  # strip markdown noise from title
            short = f"S{num} {title}"[:_AE6_TAB_NAME_MAX]
        else:
            short = re.sub(r"^## ", "", first_line)[:_AE6_TAB_NAME_MAX]
        body = _strip_internal_refs(chunk)
        body = _strip_markdown(body)
        sections.append((short, body))

    if not sections:
        # File has content but no `## Section N` headings — render as one
        # tab using the cleaned body verbatim.
        return [("AE-6", _strip_markdown(_strip_internal_refs(txt)))]
    return sections


def _strip_markdown(text: str) -> str:
    """Strip markdown decorations for plain-text Excel cell rendering.

    Handles:
      - `## Heading` lines → removed entirely (already captured as tab name)
      - `### …` and deeper → marker stripped, title text kept
      - `---` / `***` horizontal rules → removed
      - `> blockquote` prefix → stripped
      - `**bold**` → plain text
      - `*italic*` → plain text (avoids matching `**`)
      - 3+ blank lines collapsed to 2
    """
    import re
    text = re.sub(r"^## .*\n?", "", text, flags=re.MULTILINE)
    text = re.sub(r"^#{3,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^>\s?", "", text, flags=re.MULTILINE)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"(?<!\*)\*([^*\n]+?)\*(?!\*)", r"\1", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _strip_internal_refs(text: str) -> str:
    """Remove proposal-shred internal codes (EVAL-NNN / TECH-NNN / REQ-NNN).

    These codes are useful for traceability during drafting but must not
    leak into the delivered AE-6. Strips, in order:
      1. Standalone `*(Addresses ...)*` lines (section-level tag lines)
      2. Inline `under EVAL-007` / `under TECH-013` phrases
      3. `factor (CODE)` / `factor (CODE, CODE)` parentheticals
      4. Bare `(CODE)` / `(CODE, CODE)` parentheticals anywhere
      5. Any remaining bare `EVAL-NNN` / `TECH-NNN` / `REQ-NNN` tokens
      6. Double-space cleanup left behind by previous substitutions
    """
    import re
    text = re.sub(
        r"^\*\(Addresses [^\n]+\)\*\s*\n?", "", text, flags=re.MULTILINE,
    )
    text = re.sub(r"\s+under (?:EVAL|TECH|REQ)-\d+", "", text)
    text = re.sub(
        r"\s+factor\s+\((?:EVAL|TECH|REQ)-\d+\)", " factor", text,
    )
    text = re.sub(
        r"\s*\((?:(?:EVAL|TECH|REQ)-\d+(?:,\s*)?)+\)", "", text,
    )
    text = re.sub(r"\b(?:EVAL|TECH|REQ)-\d+\b", "", text)
    text = re.sub(r"  +", " ", text)
    return text.strip()


def _paginate_ae6_sections(
    sections: list[tuple[str, str]],
    *,
    max_chars: int,
) -> list[tuple[str, str]]:
    """Split any section whose body exceeds `max_chars` across continuation tabs.

    Splits at paragraph boundaries (double-newline). Continuation tabs
    get `(2)`, `(3)` … suffixes; the original tab name is truncated to
    fit the suffix within the 31-char Excel limit. Sections at or below
    the limit are returned unchanged.
    """
    result: list[tuple[str, str]] = []
    for tab_name, content in sections:
        if len(content) <= max_chars:
            result.append((tab_name, content))
            continue
        paragraphs = content.split("\n\n")
        chunk = ""
        part = 1
        for para in paragraphs:
            candidate = (chunk + "\n\n" + para).strip() if chunk else para
            if len(candidate) <= max_chars:
                chunk = candidate
            else:
                if chunk:
                    label = (
                        tab_name if part == 1
                        else f"{tab_name[:26]} ({part})"
                    )
                    result.append((label[:_AE6_TAB_NAME_MAX], chunk))
                    part += 1
                chunk = para
        if chunk:
            label = (
                tab_name if part == 1
                else f"{tab_name[:26]} ({part})"
            )
            result.append((label[:_AE6_TAB_NAME_MAX], chunk))
    return result


_POPULATORS: dict[str, Callable[[PopulationContext, AEFormSpec], None]] = {
    "AE-1": _populate_ae1,
    "AE-1A": _populate_ae1a,
    "AE-2": _populate_ae2,
    "AE-3": _populate_ae3,
    "AE-4": _populate_ae4,
    "AE-5": _populate_ae5,
    "AE-6": _populate_ae6,
}


if __name__ == "__main__":
    sys.exit(main())
