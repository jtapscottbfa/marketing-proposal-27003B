#!/usr/bin/env python3
"""scripts/publish/publish_output.py

Publish a deliverable into output/ with automatic versioning. Existing files
are never overwritten: older versions are moved into a version folder.

Routing (by file extension):
    .md                      -> output/artifacts/
    .docx .xlsx .pdf .pptx   -> output/published/
    .ics                     -> output/published/calendar/

Naming:
    The current version lives at   <dest>/<DOC_ID>_vNN.<ext>
    When a new version is published, every current <DOC_ID>_v*.<ext> in
    <dest> moves to                <dest>/_superseded/vNN/<DOC_ID>_vNN.<ext>
    and the new file is written as <DOC_ID>_v(NN+1).<ext>.

Safety:
    - Fails (exit 1) if any target path already exists. Nothing is overwritten.
    - Refuses sources or targets outside the repo root.
    - Appends one line per publish to output/PUBLISH_LOG.md.

Usage:
    python scripts/publish/publish_output.py SRC --doc-id DOC_ID [--note "..."]
    python scripts/publish/publish_output.py SRC1 SRC2 ... --doc-id-from-stem

After publishing, run scripts/git/publish_commit.sh to save state and merge
to main (required by CLAUDE.md section 6).
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from scripts.lib.guard_cwd import path_inside, require_proposal_or_engine_root  # noqa: E402

OUTPUT = REPO_ROOT / "output"
ROUTES = {
    ".md": OUTPUT / "artifacts",
    ".docx": OUTPUT / "published",
    ".xlsx": OUTPUT / "published",
    ".pdf": OUTPUT / "published",
    ".pptx": OUTPUT / "published",
    ".ics": OUTPUT / "published" / "calendar",
}
VERSION_RE = re.compile(r"_v(\d{2,})$")


def _fail(msg: str) -> None:
    print(f"✖ publish_output: {msg}", file=sys.stderr)
    sys.exit(1)


def _versions(dest: Path, doc_id: str, ext: str) -> tuple[list[Path], int]:
    """Return (current files for doc_id in dest, highest version seen anywhere)."""
    pat = re.compile(rf"^{re.escape(doc_id)}_v(\d{{2,}}){re.escape(ext)}$")
    current = [p for p in dest.glob(f"{doc_id}_v*{ext}") if pat.match(p.name)]
    highest = 0
    for p in list(current) + list((dest / "_superseded").glob(f"*/{doc_id}_v*{ext}")):
        m = pat.match(p.name)
        if m:
            highest = max(highest, int(m.group(1)))
    return current, highest


def publish(src: Path, doc_id: str, note: str) -> Path:
    src = src.resolve()
    if not src.is_file():
        _fail(f"source not found: {src}")
    if not path_inside(src, REPO_ROOT):
        _fail(f"source is outside the repo root: {src}")
    ext = src.suffix.lower()
    if ext not in ROUTES:
        _fail(f"no output route for extension '{ext}' ({src.name})")
    if VERSION_RE.search(doc_id):
        _fail(f"doc id must not carry a version suffix: {doc_id}")

    dest = ROUTES[ext]
    dest.mkdir(parents=True, exist_ok=True)
    current, highest = _versions(dest, doc_id, ext)
    new_ver = highest + 1
    target = dest / f"{doc_id}_v{new_ver:02d}{ext}"
    if target.exists():
        _fail(f"target already exists, refusing to overwrite: {target}")

    moved = []
    for old in current:
        m = re.search(r"_v(\d{2,})" + re.escape(ext) + "$", old.name)
        ver_dir = dest / "_superseded" / f"v{m.group(1)}"
        ver_dir.mkdir(parents=True, exist_ok=True)
        old_target = ver_dir / old.name
        if old_target.exists():
            _fail(f"superseded slot already occupied, refusing to overwrite: {old_target}")
        shutil.move(str(old), str(old_target))
        moved.append(old_target)

    shutil.copy2(src, target)

    log = OUTPUT / "PUBLISH_LOG.md"
    if not log.exists():
        log.write_text(
            "# Publish Log\n\n"
            "| Timestamp | Document | Version | File | Superseded | Note |\n"
            "|---|---|---|---|---|---|\n",
            encoding="utf-8",
        )
    stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    sup = "; ".join(p.relative_to(REPO_ROOT).as_posix() for p in moved) or "-"
    with log.open("a", encoding="utf-8") as fh:
        fh.write(
            f"| {stamp} | {doc_id} | v{new_ver:02d} | "
            f"{target.relative_to(REPO_ROOT).as_posix()} | {sup} | {note or '-'} |\n"
        )
    print(f"✔ {target.relative_to(REPO_ROOT).as_posix()}"
          + (f"  (superseded: {sup})" if moved else ""))
    return target


def main() -> None:
    require_proposal_or_engine_root(REPO_ROOT)
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sources", nargs="+", type=Path)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--doc-id", help="Document id (single source only)")
    g.add_argument("--doc-id-from-stem", action="store_true",
                   help="Use each source file's stem as its doc id")
    ap.add_argument("--note", default="", help="Short note for PUBLISH_LOG.md")
    args = ap.parse_args()
    if args.doc_id and len(args.sources) != 1:
        _fail("--doc-id takes exactly one source; use --doc-id-from-stem for several")
    for s in args.sources:
        publish(s, args.doc_id or s.stem, args.note)


if __name__ == "__main__":
    main()
