"""scripts/lib/guard_cwd.py

Python equivalent of guard_cwd.sh. Used by every Python entry-point script
to verify it's running inside a valid engine repo or scaffolded proposal repo
before doing anything destructive.

Mirrors the bash helper API:
    require_proposal_or_engine_root(root)  ->  None (sys.exit on failure)
    path_inside(candidate, container)      ->  bool

USAGE (from any script):
    from pathlib import Path
    from scripts.lib.guard_cwd import require_proposal_or_engine_root

    REPO_ROOT = Path(__file__).resolve().parent.parent
    require_proposal_or_engine_root(REPO_ROOT)

This is the safety net for ARCH-16 (agent/script cwd guardrail). Python
scripts already self-locate via __file__, but a copied-out script or a path
resolution bug could still run in the wrong directory; this guard rejects
those cases before any destructive operation.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Force UTF-8 stderr so the failure marker renders on Windows cp1252.
try:
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

_FAIL = "✖"  # ✖ — matches the bash helper's failure marker


def require_proposal_or_engine_root(root: Path | str) -> None:
    """Verify root is either the engine repo or a scaffolded proposal repo.

    Exits the process with status 1 (and a descriptive stderr message) if
    the root is missing, not a directory, or doesn't carry a recognized
    marker file.
    """
    if root is None or root == "":
        print(
            f"{_FAIL} guard_cwd: no root path provided to "
            f"require_proposal_or_engine_root",
            file=sys.stderr,
        )
        sys.exit(1)

    root_path = Path(root)

    if not root_path.exists():
        print(
            f"{_FAIL} guard_cwd: resolved REPO_ROOT does not exist: {root_path}",
            file=sys.stderr,
        )
        sys.exit(1)

    if not root_path.is_dir():
        print(
            f"{_FAIL} guard_cwd: REPO_ROOT is not a directory: {root_path}",
            file=sys.stderr,
        )
        sys.exit(1)

    # Engine repo marker
    if (root_path / "scripts" / "scaffold" / "new_proposal.sh").is_file():
        return

    # Scaffolded proposal repo marker (live config or example fallback)
    if (root_path / "00_admin" / "proposal_config.yml").is_file():
        return
    if (root_path / "00_admin" / "proposal_config.yml.example").is_file():
        return

    print(
        f"{_FAIL} Refusing to run: {root_path} does not look like a "
        f"proposal or engine repo.",
        file=sys.stderr,
    )
    print("  Expected one of:", file=sys.stderr)
    print(f"    {root_path}/scripts/scaffold/new_proposal.sh   (engine repo)", file=sys.stderr)
    print(f"    {root_path}/00_admin/proposal_config.yml       (scaffolded proposal)", file=sys.stderr)
    print(f"    {root_path}/00_admin/proposal_config.yml.example", file=sys.stderr)
    print("", file=sys.stderr)
    print(
        "  If you copied this script out of the repo, run it from inside "
        "the repo instead.",
        file=sys.stderr,
    )
    sys.exit(1)


def path_inside(candidate: Path | str, container: Path | str) -> bool:
    """Return True if candidate is inside container (including equality).

    Resolves both to absolute paths. Does NOT abort the caller — the caller
    decides what to do on a False result.

    If candidate doesn't exist yet, resolves its parent and joins the
    basename (mirrors the bash helper's behavior so callers can pre-validate
    a write target before creating it).
    """
    if not candidate or not container:
        return False

    cand = Path(candidate)
    cont = Path(container)

    try:
        if cand.exists():
            cand_abs = cand.resolve()
        else:
            # Resolve parent + rejoin basename. Parent must exist for this
            # to be meaningful; if it doesn't, fall through to False.
            parent = cand.parent
            if not parent.exists():
                return False
            cand_abs = parent.resolve() / cand.name

        if not cont.exists():
            return False
        cont_abs = cont.resolve()
    except (OSError, RuntimeError, ValueError):
        return False

    try:
        cand_abs.relative_to(cont_abs)
        return True
    except ValueError:
        return False
