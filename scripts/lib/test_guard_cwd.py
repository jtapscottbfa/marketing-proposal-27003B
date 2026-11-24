"""Tests for scripts/lib/guard_cwd.py

Run from engine root:
    python -m unittest scripts.lib.test_guard_cwd -v
"""
from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

# Make `scripts.lib.guard_cwd` importable regardless of how the test is invoked.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.lib.guard_cwd import (  # noqa: E402
    path_inside,
    require_proposal_or_engine_root,
)


class _SilentStderr(contextlib.AbstractContextManager):
    """Suppress stderr inside a `with` block so failing tests don't dump
    the helper's diagnostic messages into the test output."""

    def __enter__(self):
        self._buf = io.StringIO()
        self._cm = contextlib.redirect_stderr(self._buf)
        self._cm.__enter__()
        return self._buf

    def __exit__(self, *exc):
        return self._cm.__exit__(*exc)


def _make_engine_root(base: Path) -> Path:
    """Create a directory layout that satisfies the engine-root marker."""
    (base / "scripts" / "scaffold").mkdir(parents=True)
    (base / "scripts" / "scaffold" / "new_proposal.sh").write_text(
        "#!/usr/bin/env bash\n", encoding="utf-8"
    )
    return base


def _make_proposal_root(base: Path, *, with_live_config: bool = True) -> Path:
    """Create a directory layout that satisfies the scaffolded-proposal marker.

    If with_live_config is True, writes proposal_config.yml. Otherwise writes
    only the .example fallback so we exercise the second marker branch.
    """
    (base / "00_admin").mkdir(parents=True)
    name = "proposal_config.yml" if with_live_config else "proposal_config.yml.example"
    (base / "00_admin" / name).write_text("# stub\n", encoding="utf-8")
    return base


class RequireProposalOrEngineRootTests(unittest.TestCase):
    # ── Accept paths ─────────────────────────────────────────────────────

    def test_accepts_engine_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _make_engine_root(Path(tmp))
            require_proposal_or_engine_root(root)  # should not raise

    def test_accepts_scaffolded_proposal_with_live_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _make_proposal_root(Path(tmp), with_live_config=True)
            require_proposal_or_engine_root(root)

    def test_accepts_scaffolded_proposal_with_example_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = _make_proposal_root(Path(tmp), with_live_config=False)
            require_proposal_or_engine_root(root)

    def test_accepts_string_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            _make_engine_root(Path(tmp))
            require_proposal_or_engine_root(tmp)  # str, not Path

    # ── Reject paths ─────────────────────────────────────────────────────

    def test_rejects_empty_root(self):
        with _SilentStderr(), self.assertRaises(SystemExit) as ctx:
            require_proposal_or_engine_root("")
        self.assertEqual(ctx.exception.code, 1)

    def test_rejects_none_root(self):
        with _SilentStderr(), self.assertRaises(SystemExit) as ctx:
            require_proposal_or_engine_root(None)  # type: ignore[arg-type]
        self.assertEqual(ctx.exception.code, 1)

    def test_rejects_nonexistent_path(self):
        with _SilentStderr(), self.assertRaises(SystemExit) as ctx:
            require_proposal_or_engine_root("/this/path/should/not/exist/xyz123")
        self.assertEqual(ctx.exception.code, 1)

    def test_rejects_file_instead_of_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            file_path = Path(tmp) / "not-a-dir.txt"
            file_path.write_text("hi", encoding="utf-8")
            with _SilentStderr(), self.assertRaises(SystemExit) as ctx:
                require_proposal_or_engine_root(file_path)
            self.assertEqual(ctx.exception.code, 1)

    def test_rejects_directory_with_no_markers(self):
        with tempfile.TemporaryDirectory() as tmp:
            # Empty dir — no engine marker, no proposal marker.
            with _SilentStderr() as buf, self.assertRaises(SystemExit) as ctx:
                require_proposal_or_engine_root(tmp)
            self.assertEqual(ctx.exception.code, 1)
            stderr_text = buf.getvalue()
            self.assertIn("does not look like a proposal or engine repo", stderr_text)


class PathInsideTests(unittest.TestCase):
    def test_child_is_inside(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            child = root / "subdir"
            child.mkdir()
            self.assertTrue(path_inside(child, root))

    def test_grandchild_is_inside(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            deep = root / "a" / "b" / "c"
            deep.mkdir(parents=True)
            self.assertTrue(path_inside(deep, root))

    def test_self_is_inside(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertTrue(path_inside(root, root))

    def test_parent_is_not_inside(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            child = root / "child"
            child.mkdir()
            self.assertFalse(path_inside(root, child))

    def test_sibling_is_not_inside(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            a = base / "a"
            b = base / "b"
            a.mkdir()
            b.mkdir()
            self.assertFalse(path_inside(a, b))

    def test_unrelated_paths(self):
        with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
            self.assertFalse(path_inside(tmp1, tmp2))

    def test_empty_inputs_return_false(self):
        self.assertFalse(path_inside("", "/tmp"))
        self.assertFalse(path_inside("/tmp", ""))
        self.assertFalse(path_inside(None, "/tmp"))  # type: ignore[arg-type]
        self.assertFalse(path_inside("/tmp", None))  # type: ignore[arg-type]

    def test_nonexistent_container_returns_false(self):
        with tempfile.TemporaryDirectory() as tmp:
            child = Path(tmp) / "child"
            child.mkdir()
            self.assertFalse(path_inside(child, "/this/container/does/not/exist"))

    def test_nonexistent_candidate_inside_existing_container(self):
        """A write target that doesn't exist yet should still be checkable."""
        with tempfile.TemporaryDirectory() as tmp:
            container = Path(tmp)
            future_path = container / "subdir" / "not_yet.txt"
            future_path.parent.mkdir(parents=True)
            # not_yet.txt itself doesn't exist
            self.assertTrue(path_inside(future_path, container))

    def test_nonexistent_candidate_with_nonexistent_parent_returns_false(self):
        with tempfile.TemporaryDirectory() as tmp:
            container = Path(tmp)
            phantom = container / "no" / "such" / "parent" / "file.txt"
            self.assertFalse(path_inside(phantom, container))


if __name__ == "__main__":
    unittest.main()
