"""scripts/publish/sanity_check.py

Pre-submission readiness verification. Runs a registry of generalized checks
against the proposal repo and reports structured results. Exit 0 if all
critical checks pass; exit 1 otherwise.

Designed to be the engine-side promote of VT pursuit's `sanity_check.py`
(311 lines, 86 hardcoded checks). The check inventory is generalized; the
file manifest is derived dynamically from `proposal_config.yml`,
`content_library/`, and the on-disk scaffold output. No hardcoded pursuit
paths. Pursuit-specific knobs live in `00_admin/sanity_config.yml`
(optional — script skips per-knob cleanly when absent).

Public CLI:
    python scripts/publish/sanity_check.py
    python scripts/publish/sanity_check.py --strict        # treat major as critical
    python scripts/publish/sanity_check.py --json          # machine-readable output
    python scripts/publish/sanity_check.py --repo-root DIR # override autodetect

Public Python API:
    from scripts.publish.sanity_check import (
        Severity, CheckResult, run_all_checks, format_text_report,
    )
    results = run_all_checks(repo_root)
    failed = [r for r in results if not r.passed and r.severity is Severity.CRITICAL]

Exit codes (CLI):
    0 — no critical failures (safe to submit)
    1 — one or more critical failures (do not submit)
    2 — script error (config malformed, repo not found, etc.)

Check inventory (each returns list[CheckResult]):
    verify_residue          — [VERIFY*] markers in volume markdown or _output/.docx
    placeholder_residue     — PLACEHOLDER / [TBD] / [INSERT*] / [FIXME] / etc.
    markdown_as_text        — raw markdown syntax in rendered .docx body
    prohibited_content      — patterns from sanity_config.yml prohibited list
    proof_points_present    — required-substring proof points from sanity_config.yml
    addendum_acknowledged   — every RFP addendum filename referenced in output
    personnel_forms_present — one filled AE-4 per content_library/personnel.csv row
    firm_forms_present      — one filled AE-3 per content_library/firms.csv row
"""
from __future__ import annotations

import argparse
import enum
import json
import re
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable

_REPO_ROOT_GUESS = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT_GUESS) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT_GUESS))

# csv_renderer is the shared content_library reader (see scripts/lib/csv_renderer.py)
from scripts.lib.csv_renderer import read_csv  # noqa: E402

# yaml is optional; if PyYAML is not installed, config-driven checks degrade
# to no-ops with a single WARN result (rather than failing the whole script).
try:
    import yaml as _yaml  # type: ignore[import-not-found]
except ImportError:
    _yaml = None


# ── Result types ──────────────────────────────────────────────────────────────


class Severity(enum.Enum):
    CRITICAL = "critical"
    MAJOR = "major"
    WARN = "warn"


@dataclass
class CheckResult:
    """One outcome from one check.

    Attributes:
        id: Stable identifier (`<check_name>.<sub_id>`). Stable across runs;
            CI / triage tools can key off this.
        severity: One of Severity.CRITICAL / MAJOR / WARN. Only CRITICAL
            failures cause non-zero exit (unless `--strict`, which promotes
            MAJOR to CRITICAL).
        passed: True if the check succeeded; False if it failed.
        message: Human-readable summary (one sentence).
        locator: File path / line / cell / docx-tab the result points at;
            empty string when not applicable.
    """

    id: str
    severity: Severity
    passed: bool
    message: str
    locator: str = ""

    def to_json(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "severity": self.severity.value,
            "passed": self.passed,
            "message": self.message,
            "locator": self.locator,
        }


# ── Repo discovery & config loading ───────────────────────────────────────────


@dataclass
class RepoContext:
    """Resolved per-run context. Computed once, passed to each check."""

    root: Path
    proposal_config: dict[str, Any]
    sanity_config: dict[str, Any]
    volume_dirs: list[Path] = field(default_factory=list)
    output_docx: list[Path] = field(default_factory=list)
    content_library: Path | None = None
    addendums_dir: Path | None = None


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file as a dict. Returns {} on missing file or null root.
    Raises ValueError on parse error, non-mapping root, or missing PyYAML
    when the file does exist (we can't honor config-driven contracts blindly)."""
    if not path.is_file():
        return {}
    if _yaml is None:
        raise ValueError(
            f"PyYAML not installed; cannot read {path}. "
            f"Install with: pip install pyyaml (see requirements.txt)"
        )
    with path.open("r", encoding="utf-8") as f:
        data = _yaml.safe_load(f)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"{path}: top level must be a mapping, got {type(data).__name__}")
    return data


_NON_VOLUME_DIRS = {"00_admin"}


def _discover_volume_dirs(root: Path, proposal_config: dict[str, Any]) -> list[Path]:
    """Return absolute paths for active volume directories.

    Order of resolution:
      1. `volumes:` list in proposal_config.yml — entries with `active: true`,
         sorted by `order` (or list position if no `order` key).
      2. Fallback: glob `[0-9][0-9]_*` directories at repo root, excluding
         `00_admin/` (admin/intake content, not deliverable volumes).

    Why exclude 00_admin: it contains the RFP shred, win-themes worksheet,
    template_backlog, and reference_proposals/ — files that legitimately
    contain `[VERIFY]` and `PLACEHOLDER` markers as drafting scaffold.
    They aren't part of what gets shipped to the client.
    """
    volumes = proposal_config.get("volumes")
    if isinstance(volumes, list) and volumes:
        active = [v for v in volumes if isinstance(v, dict) and v.get("active", True)]
        active.sort(key=lambda v: (v.get("order", 9999), v.get("folder", "")))
        out: list[Path] = []
        for v in active:
            folder = v.get("folder")
            if isinstance(folder, str) and folder:
                p = root / folder
                if p.is_dir():
                    out.append(p)
        if out:
            return out

    # Fallback: scaffold-numbered directories, minus admin/intake roots
    return sorted(
        p for p in root.glob("[0-9][0-9]_*")
        if p.is_dir() and p.name not in _NON_VOLUME_DIRS
    )


def build_context(repo_root: Path) -> RepoContext:
    """Resolve repo-relative paths and load configs. Cheap; called once."""
    root = repo_root.resolve()

    proposal_config = _load_yaml(root / "00_admin" / "proposal_config.yml")
    sanity_config = _load_yaml(root / "00_admin" / "sanity_config.yml")

    output_dir = root / "_output"
    output_docx = sorted(output_dir.glob("*.docx")) if output_dir.is_dir() else []

    content_library = root / "content_library"
    if not content_library.is_dir():
        content_library = None

    addendums_dir = root / "00_admin" / "rfp_intake" / "addendums"
    if not addendums_dir.is_dir():
        addendums_dir = None

    return RepoContext(
        root=root,
        proposal_config=proposal_config,
        sanity_config=sanity_config,
        volume_dirs=_discover_volume_dirs(root, proposal_config),
        output_docx=output_docx,
        content_library=content_library,
        addendums_dir=addendums_dir,
    )


# ── docx text extraction ──────────────────────────────────────────────────────


_TAG_RE = re.compile(r"<[^>]*>")
_WS_RE = re.compile(r"\s+")
_PARA_BREAK_RE = re.compile(r"</w:p>", re.IGNORECASE)


def _docx_text(path: Path) -> str:
    """Extract plain text from a .docx file's word/document.xml.

    Inserts a newline at every `</w:p>` so paragraph-anchored regex (e.g.
    `^## ` for raw markdown headings) work after extraction. Tags are
    stripped; whitespace is collapsed within each line.
    """
    with zipfile.ZipFile(path) as z:
        try:
            xml = z.read("word/document.xml").decode("utf-8", errors="replace")
        except KeyError as exc:
            raise ValueError(f"{path}: no word/document.xml — not a valid .docx") from exc

    paragraphs = _PARA_BREAK_RE.split(xml)
    lines = []
    for p in paragraphs:
        text = _TAG_RE.sub("", p)
        text = _WS_RE.sub(" ", text).strip()
        if text:
            lines.append(text)
    return "\n".join(lines)


# ── Check implementations ─────────────────────────────────────────────────────


# Marker patterns shared with check_output_pdf.sh — keep in sync.
_VERIFY_PATTERN = re.compile(r"\[VERIFY[^\]]*\]")

_PLACEHOLDER_PATTERNS = [
    ("placeholder", re.compile(r"PLACEHOLDER", re.IGNORECASE)),
    ("number_token", re.compile(r"\[NUMBER\]")),
    ("tbd", re.compile(r"\[TBD\]")),
    ("insert", re.compile(r"\[INSERT[^\]]*\]")),
    ("confirm", re.compile(r"\[CONFIRM[^\]]*\]")),
    ("pending", re.compile(r"\[PENDING[^\]]*\]")),
    ("needs_verification", re.compile(r"\[NEEDS_VERIFICATION[^\]]*\]")),
    ("fixme", re.compile(r"\[FIXME[^\]]*\]")),
    ("todo", re.compile(r"\[TODO[^\]]*\]")),
    ("xx", re.compile(r"\[XX\]")),
    ("xxx", re.compile(r"\[XXX\]")),
    ("internal", re.compile(r"\[INTERNAL[^\]]*\]")),
    ("draft", re.compile(r"\[DRAFT\]")),
    ("end_of_draft", re.compile(r"\*?End of draft\*?", re.IGNORECASE)),
]

# Paragraph-anchored (post-paragraph-split) raw-markdown patterns.
_MARKDOWN_PATTERNS = [
    ("h2_or_deeper", re.compile(r"^#{2,6} ")),
    ("bold", re.compile(r"\*\*[^*\n]+\*\*")),
    ("italic", re.compile(r"(?<!\*)\*[^*\n]+\*(?!\*)")),
    ("hr", re.compile(r"^---\s*$")),
    ("blockquote", re.compile(r"^> ")),
]


def _iter_volume_md(ctx: RepoContext) -> Iterable[Path]:
    """All .md files inside any active volume directory (depth ≤ 2)."""
    for vol in ctx.volume_dirs:
        # match combine_volumes.sh: -maxdepth 2
        for p in vol.glob("*.md"):
            yield p
        for p in vol.glob("*/*.md"):
            yield p


def check_verify_residue(ctx: RepoContext) -> list[CheckResult]:
    """`[VERIFY*]` markers in volume markdown or rendered output."""
    results: list[CheckResult] = []

    for md in sorted(_iter_volume_md(ctx)):
        text = md.read_text(encoding="utf-8", errors="replace")
        hits = _VERIFY_PATTERN.findall(text)
        rel = md.relative_to(ctx.root)
        results.append(CheckResult(
            id=f"verify_residue.md:{rel.as_posix()}",
            severity=Severity.CRITICAL,
            passed=not hits,
            message=(
                "no [VERIFY] markers" if not hits
                else f"{len(hits)} [VERIFY] marker(s); first: {hits[0]!r}"
            ),
            locator=str(rel),
        ))

    for docx in ctx.output_docx:
        try:
            text = _docx_text(docx)
        except (ValueError, zipfile.BadZipFile) as exc:
            results.append(CheckResult(
                id=f"verify_residue.docx:{docx.name}",
                severity=Severity.CRITICAL,
                passed=False,
                message=f"could not read docx: {exc}",
                locator=str(docx.relative_to(ctx.root)),
            ))
            continue
        hits = _VERIFY_PATTERN.findall(text)
        results.append(CheckResult(
            id=f"verify_residue.docx:{docx.name}",
            severity=Severity.CRITICAL,
            passed=not hits,
            message=(
                "no [VERIFY] markers" if not hits
                else f"{len(hits)} [VERIFY] marker(s); first: {hits[0]!r}"
            ),
            locator=str(docx.relative_to(ctx.root)),
        ))

    return results


def check_placeholder_residue(ctx: RepoContext) -> list[CheckResult]:
    """PLACEHOLDER / [TBD] / [INSERT…] etc. in rendered output.

    Markdown sources are *not* scanned — drafting-time placeholders are
    legitimate there. Only the rendered .docx must be clean (matches the
    contract enforced by check_output_pdf.sh).
    """
    results: list[CheckResult] = []

    for docx in ctx.output_docx:
        try:
            text = _docx_text(docx)
        except (ValueError, zipfile.BadZipFile) as exc:
            results.append(CheckResult(
                id=f"placeholder_residue.docx:{docx.name}",
                severity=Severity.CRITICAL,
                passed=False,
                message=f"could not read docx: {exc}",
                locator=str(docx.relative_to(ctx.root)),
            ))
            continue
        for sub_id, pattern in _PLACEHOLDER_PATTERNS:
            hits = pattern.findall(text)
            results.append(CheckResult(
                id=f"placeholder_residue.{sub_id}:{docx.name}",
                severity=Severity.CRITICAL,
                passed=not hits,
                message=(
                    f"no {sub_id} hits" if not hits
                    else f"{len(hits)} {sub_id} hit(s); first: {hits[0]!r}"
                ),
                locator=str(docx.relative_to(ctx.root)),
            ))

    return results


def check_markdown_as_text(ctx: RepoContext) -> list[CheckResult]:
    """Raw markdown syntax leaked into rendered .docx body text.

    A symptom of a broken render path (cells filled with markdown source
    rather than rendered prose). VT post-mortem SS-04.
    """
    results: list[CheckResult] = []

    for docx in ctx.output_docx:
        try:
            text = _docx_text(docx)
        except (ValueError, zipfile.BadZipFile):
            # Already reported by verify/placeholder checks; skip duplicate noise.
            continue
        for sub_id, pattern in _MARKDOWN_PATTERNS:
            # _docx_text() inserts \n between paragraphs, so re.MULTILINE
            # makes ^ / $ paragraph-anchored.
            hits = re.findall(pattern.pattern, text, re.MULTILINE)
            results.append(CheckResult(
                id=f"markdown_as_text.{sub_id}:{docx.name}",
                severity=Severity.MAJOR,
                passed=not hits,
                message=(
                    f"no raw {sub_id} markdown" if not hits
                    else f"{len(hits)} raw {sub_id} instance(s); first: {hits[0]!r}"
                ),
                locator=str(docx.relative_to(ctx.root)),
            ))

    return results


def check_prohibited_content(ctx: RepoContext) -> list[CheckResult]:
    """Patterns from `sanity_config.yml: prohibited_patterns`.

    Each entry: `pattern` (literal substring; case-sensitive), `label`,
    optional `severity` (default critical). Searches both volume markdown
    and rendered .docx. No-op (zero results) when the config block is
    absent or empty.
    """
    results: list[CheckResult] = []

    raw = ctx.sanity_config.get("prohibited_patterns")
    if not isinstance(raw, list):
        return results

    entries: list[tuple[str, str, Severity]] = []
    for i, entry in enumerate(raw):
        if not isinstance(entry, dict):
            continue
        pattern = entry.get("pattern")
        if not isinstance(pattern, str) or not pattern:
            continue
        label = entry.get("label") or pattern
        sev_str = (entry.get("severity") or "critical").lower()
        try:
            severity = Severity(sev_str)
        except ValueError:
            severity = Severity.CRITICAL
        entries.append((pattern, label, severity))

    if not entries:
        return results

    sources: list[tuple[str, Path, str]] = []  # (kind, path, text)
    for md in sorted(_iter_volume_md(ctx)):
        sources.append(("md", md, md.read_text(encoding="utf-8", errors="replace")))
    for docx in ctx.output_docx:
        try:
            sources.append(("docx", docx, _docx_text(docx)))
        except (ValueError, zipfile.BadZipFile):
            continue

    for pattern, label, severity in entries:
        for kind, path, text in sources:
            rel = path.relative_to(ctx.root)
            present = pattern in text
            results.append(CheckResult(
                id=f"prohibited_content.{label}:{kind}:{rel.as_posix()}",
                severity=severity,
                passed=not present,
                message=(
                    f"absent: {label!r}" if not present
                    else f"prohibited pattern {label!r} found"
                ),
                locator=str(rel),
            ))

    return results


def check_proof_points_present(ctx: RepoContext) -> list[CheckResult]:
    """Required substrings from `sanity_config.yml: proof_points`.

    Each entry: `pattern` (literal substring), `label`, optional
    `severity` (default critical). Searches the union of all rendered
    .docx body text. No-op when the config block is absent or empty,
    or when there are no rendered .docx files.
    """
    results: list[CheckResult] = []

    raw = ctx.sanity_config.get("proof_points")
    if not isinstance(raw, list) or not raw:
        return results
    if not ctx.output_docx:
        return results

    entries: list[tuple[str, str, Severity]] = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        pattern = entry.get("pattern")
        if not isinstance(pattern, str) or not pattern:
            continue
        label = entry.get("label") or pattern
        sev_str = (entry.get("severity") or "critical").lower()
        try:
            severity = Severity(sev_str)
        except ValueError:
            severity = Severity.CRITICAL
        entries.append((pattern, label, severity))

    haystack = "\n".join(
        text for text in (
            _try_docx_text(d) for d in ctx.output_docx
        ) if text is not None
    )

    for pattern, label, severity in entries:
        present = pattern in haystack
        results.append(CheckResult(
            id=f"proof_points_present.{label}",
            severity=severity,
            passed=present,
            message=(
                f"proof point present: {label!r}" if present
                else f"missing proof point: {label!r} (pattern: {pattern!r})"
            ),
            locator="_output/*.docx",
        ))

    return results


def _try_docx_text(path: Path) -> str | None:
    try:
        return _docx_text(path)
    except (ValueError, zipfile.BadZipFile):
        return None


def check_addendum_acknowledged(ctx: RepoContext) -> list[CheckResult]:
    """Each file in 00_admin/rfp_intake/addendums/ must be referenced by
    name (basename without extension) somewhere in the rendered output.

    No-op when addendums directory is absent or empty, or when no .docx
    has been rendered yet.
    """
    results: list[CheckResult] = []

    if ctx.addendums_dir is None or not ctx.output_docx:
        return results

    addendums = sorted(
        p for p in ctx.addendums_dir.iterdir()
        if p.is_file() and not p.name.startswith(".")
    )
    if not addendums:
        return results

    haystack = "\n".join(
        text for text in (
            _try_docx_text(d) for d in ctx.output_docx
        ) if text is not None
    )

    for addendum in addendums:
        stem = addendum.stem
        present = stem in haystack
        results.append(CheckResult(
            id=f"addendum_acknowledged.{stem}",
            severity=Severity.CRITICAL,
            passed=present,
            message=(
                f"addendum {stem!r} acknowledged"
                if present else f"addendum {stem!r} not referenced in output"
            ),
            locator=str(addendum.relative_to(ctx.root)),
        ))

    return results


def check_personnel_forms_present(ctx: RepoContext) -> list[CheckResult]:
    """One filled `AE-4_<id>.xlsx` per row in content_library/personnel.csv.

    Looks anywhere under the repo for `**/filled/AE-4_<id>.xlsx`. Skips
    cleanly (zero results) when the personnel CSV is absent or has zero
    data rows — the engine ships header-only CSVs, so this check is a
    no-op until pursuit data is loaded.
    """
    return _check_form_per_row(
        ctx,
        csv_name="personnel.csv",
        form_prefix="AE-4",
        check_id_prefix="personnel_forms_present",
    )


def check_firm_forms_present(ctx: RepoContext) -> list[CheckResult]:
    """One filled `AE-3_<id>.xlsx` per row in content_library/firms.csv."""
    return _check_form_per_row(
        ctx,
        csv_name="firms.csv",
        form_prefix="AE-3",
        check_id_prefix="firm_forms_present",
    )


def _check_form_per_row(
    ctx: RepoContext,
    *,
    csv_name: str,
    form_prefix: str,
    check_id_prefix: str,
) -> list[CheckResult]:
    results: list[CheckResult] = []

    if ctx.content_library is None:
        return results
    csv_path = ctx.content_library / csv_name
    if not csv_path.is_file():
        return results

    try:
        rows = read_csv(csv_path)
    except (ValueError, FileNotFoundError) as exc:
        results.append(CheckResult(
            id=f"{check_id_prefix}.csv_read",
            severity=Severity.CRITICAL,
            passed=False,
            message=f"could not read {csv_name}: {exc}",
            locator=str(csv_path.relative_to(ctx.root)),
        ))
        return results

    if not rows:
        return results

    # Index existing filled forms by id-suffix → path. Match suffix
    # case-insensitively to be friendly across personnel.id case styles.
    found: dict[str, Path] = {}
    for xlsx in ctx.root.glob(f"**/filled/{form_prefix}_*.xlsx"):
        suffix = xlsx.stem[len(form_prefix) + 1:].lower()
        found.setdefault(suffix, xlsx)

    for row in rows:
        row_id = (row.get("id") or "").strip()
        if not row_id:
            continue
        match = found.get(row_id.lower())
        results.append(CheckResult(
            id=f"{check_id_prefix}.{row_id}",
            severity=Severity.CRITICAL,
            passed=match is not None,
            message=(
                f"{form_prefix}_{row_id}.xlsx present at {match.relative_to(ctx.root)}"
                if match is not None
                else f"{form_prefix}_{row_id}.xlsx missing — expected under **/filled/"
            ),
            locator=str(match.relative_to(ctx.root)) if match else "",
        ))

    return results


# ── Driver ────────────────────────────────────────────────────────────────────


CheckFunc = Callable[[RepoContext], list[CheckResult]]

CHECKS: list[CheckFunc] = [
    check_verify_residue,
    check_placeholder_residue,
    check_markdown_as_text,
    check_prohibited_content,
    check_proof_points_present,
    check_addendum_acknowledged,
    check_personnel_forms_present,
    check_firm_forms_present,
]


def run_all_checks(repo_root: Path, checks: Iterable[CheckFunc] | None = None) -> list[CheckResult]:
    """Run every registered check and return a flat result list.

    Args:
        repo_root: Path to the proposal repo root (the directory containing
            00_admin/proposal_config.yml).
        checks: Optional override of the check registry — useful for tests
            that want to exercise one check at a time. Defaults to CHECKS.

    Returns:
        Flat list of CheckResult, in the order checks were declared.
    """
    ctx = build_context(repo_root)
    out: list[CheckResult] = []
    for fn in (checks if checks is not None else CHECKS):
        out.extend(fn(ctx))
    return out


def has_blocking_failure(results: Iterable[CheckResult], strict: bool = False) -> bool:
    """True if any result should block submission.

    Default contract: only CRITICAL failures block. With `strict=True`,
    MAJOR failures also block.
    """
    blocking = {Severity.CRITICAL}
    if strict:
        blocking.add(Severity.MAJOR)
    return any(not r.passed and r.severity in blocking for r in results)


# ── CLI ───────────────────────────────────────────────────────────────────────


def format_text_report(results: list[CheckResult], strict: bool) -> str:
    """Plain-text grouped-by-status report for terminal output."""
    by_status: dict[str, list[CheckResult]] = {"FAIL": [], "WARN": [], "PASS": []}
    for r in results:
        if r.passed:
            by_status["PASS"].append(r)
        elif r.severity is Severity.CRITICAL or (strict and r.severity is Severity.MAJOR):
            by_status["FAIL"].append(r)
        else:
            by_status["WARN"].append(r)

    lines: list[str] = []
    lines.append("=" * 62)
    lines.append("  Pre-Submission Sanity Check")
    lines.append("=" * 62)

    for status in ("FAIL", "WARN", "PASS"):
        bucket = by_status[status]
        if not bucket:
            continue
        lines.append(f"\n--- {status} ({len(bucket)}) ---")
        for r in bucket:
            tag = f"[{status}]"
            sev = r.severity.value.upper()
            lines.append(f"  {tag:<7} ({sev}) {r.message}")
            if r.locator:
                lines.append(f"          at {r.locator}")
            lines.append(f"          id: {r.id}")

    total = len(results)
    failed = len(by_status["FAIL"])
    warned = len(by_status["WARN"])
    passed = len(by_status["PASS"])

    lines.append("\n" + "=" * 62)
    lines.append(
        f"  {passed}/{total} passed   {failed} blocking failure(s)   "
        f"{warned} warning(s)"
    )
    if failed == 0 and warned == 0:
        lines.append("  ALL CHECKS PASSED — package is sanity-clean")
    elif failed == 0:
        lines.append(f"  PASSED WITH {warned} WARNING(S) — review before upload")
    else:
        lines.append(f"  {failed} BLOCKING FAILURE(S) — do not submit until resolved")
    lines.append("=" * 62)
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Pre-submission sanity check")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Override repo root autodetect (default: parent of scripts/)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat MAJOR failures as blocking (default: only CRITICAL blocks)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON result array on stdout instead of text report",
    )
    args = parser.parse_args(argv)

    repo_root = args.repo_root or _REPO_ROOT_GUESS
    if not (repo_root / "00_admin").is_dir():
        print(
            f"sanity_check: not a proposal repo (no 00_admin/ at {repo_root})",
            file=sys.stderr,
        )
        return 2

    try:
        results = run_all_checks(repo_root)
    except ValueError as exc:
        print(f"sanity_check: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(
            [r.to_json() for r in results],
            indent=2,
        ))
    else:
        print(format_text_report(results, strict=args.strict))

    return 1 if has_blocking_failure(results, strict=args.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
