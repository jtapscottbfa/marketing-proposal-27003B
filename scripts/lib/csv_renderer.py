"""scripts/lib/csv_renderer.py

CSV reader + narrative renderer for `content_library/*.csv`. Reads the
four standard tables (projects, personnel, firms, past_performance) into
typed dicts, then formats rows for AE form-population (e.g., AE-3 firm
table, AE-4 employment-history boxes, AE-5 project sheets).

Public API:
    read_csv(path, *, schema=None) -> list[dict]
    render_project_one_liner(row) -> str
    render_personnel_role_block(row, role) -> str

Schema is auto-detected from filename for the four standard tables; pass
`schema=` to read a non-standard CSV. See `content_library/README.md`
for column definitions.

USAGE:
    from scripts.lib.csv_renderer import (
        read_csv,
        render_project_one_liner,
        render_personnel_role_block,
    )

    for row in read_csv("content_library/projects.csv"):
        print(render_project_one_liner(row))
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

VERIFY_MARKER = "[VERIFY]"

_SCORE_ENUM = {
    "Exceptional", "Very Good", "Satisfactory", "Marginal", "Unsatisfactory",
}

_PROJECT_SCHEMA: dict[str, Any] = {
    "required": {
        "id", "name", "client", "agency_type", "location",
        "firm_role", "start_date", "complete_date", "scope_summary",
    },
    "enums": {
        "agency_type": {"federal", "state", "local", "higher_ed", "private"},
    },
    "ints": {
        "contract_value", "gross_sf",
        # AE-5 construction-data integers (all optional)
        "num_floors",
        "owner_budget", "ae_estimate", "low_bid",
        "num_change_orders", "cost_change_orders",
        "swam_proposed_pct", "swam_final_pct",
    },
    "lists": {"eor_disciplines", "relevance_tags", "codes_used"},
}

_PERSONNEL_SCHEMA: dict[str, Any] = {
    "required": {
        "id", "name", "title", "office", "years_total", "years_firm",
        "education", "discipline",
    },
    "enums": {
        "discipline": {
            "electrical", "mechanical", "plumbing", "controls",
            "pm", "cadd", "other",
        },
        "license_type": {"PE", "EIT", "CPD", "none"},
        "cpsm_status": {"Yes", "No"},
    },
    "ints": {"years_total", "years_firm", "license_year"},
    "lists": set(),
}

_FIRM_SCHEMA: dict[str, Any] = {
    "required": {
        "id", "name", "ownership_class", "primary_function",
        "poc_name", "poc_title", "poc_email",
    },
    "enums": {
        "ownership_class": {
            "large", "small", "micro", "minority", "women",
            "veteran", "service_disabled_veteran",
        },
    },
    "ints": {"years_in_practice", "prior_projects_with_prime"},
    "lists": set(),
}

_PAST_PERFORMANCE_SCHEMA: dict[str, Any] = {
    "required": {
        "project_id", "eval_type", "eval_period", "score_overall",
        "verification_status",
    },
    "enums": {
        "eval_type": {"CPARS", "PPQ", "client_letter", "internal"},
        "score_overall": _SCORE_ENUM,
        "score_quality": _SCORE_ENUM,
        "score_schedule": _SCORE_ENUM,
        "score_cost": _SCORE_ENUM,
        "score_management": _SCORE_ENUM,
        # [VERIFY] is a *valid* sentinel value here, not a placeholder.
        "verification_status": {"verified", "unverified", VERIFY_MARKER},
    },
    "ints": set(),
    "lists": set(),
}

_PERSONNEL_PROJECTS_SCHEMA: dict[str, Any] = {
    "required": {"personnel_id", "project_id", "role"},
    "enums": {},
    "ints": {"listing_order"},
    "lists": set(),
}

_PROJECT_CONTACTS_SCHEMA: dict[str, Any] = {
    "required": {"project_id", "role"},
    "enums": {
        "role": {"admin", "construction_prime_pm", "construction_supt"},
    },
    "ints": set(),
    "lists": set(),
}

_PROJECT_DESIGNERS_SCHEMA: dict[str, Any] = {
    "required": {"project_id", "discipline", "firm", "individual", "role"},
    "enums": {
        "discipline": {
            "prime_ae", "architectural", "structural", "mechanical",
            "electrical", "civil", "other",
        },
    },
    "ints": set(),
    "lists": set(),
}

_SCHEMA_BY_FILENAME: dict[str, dict[str, Any]] = {
    "projects.csv": _PROJECT_SCHEMA,
    "personnel.csv": _PERSONNEL_SCHEMA,
    "firms.csv": _FIRM_SCHEMA,
    "past_performance.csv": _PAST_PERFORMANCE_SCHEMA,
    "personnel_projects.csv": _PERSONNEL_PROJECTS_SCHEMA,
    "project_contacts.csv": _PROJECT_CONTACTS_SCHEMA,
    "project_designers.csv": _PROJECT_DESIGNERS_SCHEMA,
}


def read_csv(
    path: Path | str,
    *,
    schema: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Read a content_library CSV into a list of typed dicts.

    Coerces ints, splits semicolon-list columns, validates enums, and
    converts empty cells to None. Raises if any required column on any
    row is empty or contains the [VERIFY] marker (exception:
    `verification_status` in past_performance, where [VERIFY] is itself
    a valid enum value).

    Args:
        path: Path to the CSV. Must exist.
        schema: Optional schema override. Required keys: `required`
            (set of column names), `enums` (dict[col, set[value]]),
            `ints` (set), `lists` (set). When omitted, schema is
            looked up by filename.

    Returns:
        One dict per data row. Empty cells are None; ints are int;
        list columns are list[str]; everything else is str.

    Raises:
        FileNotFoundError: path doesn't exist.
        ValueError: unknown filename (and no schema passed), required
            cell empty or [VERIFY], invalid enum value, or non-int in
            an int column.
    """
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"CSV not found: {p}")

    if schema is None:
        schema = _SCHEMA_BY_FILENAME.get(p.name)
    if schema is None:
        raise ValueError(
            f"read_csv: no schema known for {p.name!r}. "
            f"Pass schema= to read a non-standard CSV."
        )

    required: set[str] = schema.get("required", set())
    enums: dict[str, set[str]] = schema.get("enums", {})
    ints: set[str] = schema.get("ints", set())
    lists: set[str] = schema.get("lists", set())

    rows: list[dict[str, Any]] = []
    with p.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        # csv.DictReader.fieldnames is None only on an empty file; a header-
        # only file gives fieldnames but iterates zero rows.
        for line_num, raw in enumerate(reader, start=2):
            typed = _coerce_row(
                raw,
                line_num=line_num,
                source=p,
                required=required,
                enums=enums,
                ints=ints,
                lists=lists,
            )
            rows.append(typed)

    return rows


def _coerce_row(
    raw: dict[str, str | None],
    *,
    line_num: int,
    source: Path,
    required: set[str],
    enums: dict[str, set[str]],
    ints: set[str],
    lists: set[str],
) -> dict[str, Any]:
    typed: dict[str, Any] = {}
    for col, val in raw.items():
        if val is None:
            typed[col] = None
            continue
        v = val.strip()
        if v == "":
            typed[col] = None
            continue

        if v == VERIFY_MARKER:
            verify_is_valid_enum = (
                col in enums and VERIFY_MARKER in enums[col]
            )
            if col in required and not verify_is_valid_enum:
                raise ValueError(
                    f"{source}:{line_num}: required column {col!r} contains "
                    f"{VERIFY_MARKER}; row needs human verification before use."
                )
            typed[col] = VERIFY_MARKER
            continue

        if col in lists:
            typed[col] = [item.strip() for item in v.split(";") if item.strip()]
            continue

        if col in ints:
            try:
                typed[col] = int(v)
            except ValueError as exc:
                raise ValueError(
                    f"{source}:{line_num}: column {col!r} expected int, "
                    f"got {v!r}"
                ) from exc
            continue

        if col in enums:
            allowed = enums[col]
            if v not in allowed:
                raise ValueError(
                    f"{source}:{line_num}: column {col!r} value {v!r} "
                    f"not in allowed values {sorted(allowed)}"
                )

        typed[col] = v

    for col in required:
        if typed.get(col) is None:
            raise ValueError(
                f"{source}:{line_num}: required column {col!r} is empty."
            )

    return typed


def render_project_one_liner(row: dict[str, Any]) -> str:
    """Compact one-line project label: ``<name> (<client>, <year>)``.

    Year is extracted from `complete_date` when it parses as YYYY-MM-DD;
    otherwise falls back to `start_date`'s year, then to the literal
    `complete_date` token (e.g., "In Progress"), then "n.d.".
    """
    name = row.get("name") or "[unnamed project]"
    client = row.get("client") or "[unknown client]"
    year = _project_year(row)
    return f"{name} ({client}, {year})"


def _project_year(row: dict[str, Any]) -> str:
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


def render_personnel_role_block(row: dict[str, Any], role: str) -> str:
    """Multi-line block for AE-4 employment-history boxes.

    Includes only populated optional fields. `role` is the proposed
    assignment on the current pursuit (not stored in the CSV).
    """
    lines: list[str] = []

    name = row.get("name") or "[unnamed]"
    title = row.get("title")
    lines.append(f"{name} — {title}" if title else str(name))

    if role:
        lines.append(f"Role on this contract: {role}")

    years_total = row.get("years_total")
    years_firm = row.get("years_firm")
    if years_total is not None and years_firm is not None:
        lines.append(
            f"Experience: {years_total} years total / "
            f"{years_firm} with current firm"
        )
    elif years_total is not None:
        lines.append(f"Experience: {years_total} years total")

    education = row.get("education")
    if education:
        lines.append(f"Education: {education}")

    license_type = row.get("license_type")
    if license_type and license_type != "none":
        license_str = str(license_type)
        license_state = row.get("license_state")
        license_number = row.get("license_number")
        license_year = row.get("license_year")
        if license_number:
            license_str += f" #{license_number}"
        details: list[str] = []
        if license_state:
            details.append(str(license_state))
        if license_year is not None:
            details.append(str(license_year))
        if details:
            license_str += f" ({', '.join(details)})"
        lines.append(f"Registration: {license_str}")

    notes = row.get("notes")
    if notes:
        lines.append(f"Notes: {notes}")

    return "\n".join(lines)
