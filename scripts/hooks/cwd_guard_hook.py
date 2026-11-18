#!/usr/bin/env python3
"""scripts/hooks/cwd_guard_hook.py

Claude Code PreToolUse hook for Write / Edit / NotebookEdit.

Reads tool input JSON on stdin, extracts file_path, and rejects (exit 2)
if the file_path resolves outside the current git repo's toplevel.

This is the programmatic enforcement layer of ARCH-16. It complements:
- The prose rule in CLAUDE.md §1 ("Working directory discipline")
- The script-level guard helpers in scripts/lib/guard_cwd.{sh,py}

Wired up via .claude/settings.json. Runs whenever the agent attempts to
Write / Edit / NotebookEdit in this project. Out-of-repo writes are blocked
with a diagnostic message; exit code 2 is Claude Code's documented "deny"
signal.

Behavior matrix:
- tool_input.file_path missing             -> allow (some tool variants don't
                                              carry one)
- cwd not in a git repo                    -> warn on stderr, allow (defensive
                                              — hook only loads when this
                                              project's .claude/settings.json
                                              is loaded; in practice we're
                                              always in git)
- file_path inside repo root               -> allow (exit 0)
- file_path inside ~/.claude/projects/     -> allow (auto-memory storage —
                                              outside repo by design)
- file_path outside repo root + allowlist  -> reject (exit 2) with diagnostic
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

# Force UTF-8 stderr so the failure marker renders on Windows cp1252.
try:
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

# Import path_inside from the canonical Python guard helper. Resolve relative
# to this file so the hook works from any cwd.
_HERE = Path(__file__).resolve().parent
_REPO_ROOT_FROM_HOOK = _HERE.parent.parent  # scripts/hooks/.. = scripts; .. = repo
sys.path.insert(0, str(_REPO_ROOT_FROM_HOOK))

from scripts.lib.guard_cwd import path_inside  # noqa: E402


# Paths that are legitimately outside the repo and should be allowed.
# These are auto-managed by Claude Code or the OS and not project artifacts.
ALLOWLISTED_OUTSIDE_REPO = [
    # Auto-memory storage (Claude Code default: ~/.claude/projects/<sanitized-cwd>/)
    # Allow the entire ~/.claude/projects/ tree so any project's memory works.
    Path.home() / ".claude" / "projects",
]


def _stderr(msg: str) -> None:
    print(msg, file=sys.stderr)


def _is_allowlisted(file_path: str) -> bool:
    for allowlisted in ALLOWLISTED_OUTSIDE_REPO:
        if path_inside(file_path, allowlisted):
            return True
    return False


def main() -> int:
    # ── Read tool input JSON from stdin ──────────────────────────────────────
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        _stderr(f"[guard_cwd hook] could not parse stdin as JSON: {exc} — allowing")
        return 0

    tool_name = payload.get("tool_name", "unknown")
    file_path = payload.get("tool_input", {}).get("file_path", "")

    # No file_path → not in our enforcement scope
    if not file_path:
        return 0

    # ── Determine the active repo root ───────────────────────────────────────
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            check=True,
            capture_output=True,
            text=True,
        )
        repo_root = Path(result.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Defensive: hook ran but we're not in a git repo (or git missing).
        # Allow with a stderr warning — the hook can't know the boundary.
        _stderr(
            "[guard_cwd hook] cwd is not inside a git repo "
            "(or git unavailable) — allowing tool call (best-effort)"
        )
        return 0

    # ── Path-inside check (single source of truth: scripts/lib/guard_cwd.py) ─
    if path_inside(file_path, repo_root):
        return 0

    # ── Outside repo, but might be in a legitimate allowlisted location ──────
    if _is_allowlisted(file_path):
        return 0

    # ── Reject ───────────────────────────────────────────────────────────────
    _stderr(f"[guard_cwd hook] ✖ Refusing {tool_name} — file_path is outside repo root")
    _stderr(f"  target:    {file_path}")
    _stderr(f"  repo root: {repo_root}")
    _stderr(
        "  Per CLAUDE.md §1 (Working directory discipline): all writes must"
    )
    _stderr(
        "  occur inside the repo. If you genuinely need to write outside the"
    )
    _stderr(
        "  repo, do it explicitly in the user-facing terminal, not via the agent."
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
