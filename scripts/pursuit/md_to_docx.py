#!/usr/bin/env python3
"""scripts/pursuit/md_to_docx.py

Convert Markdown to a transcription-friendly .docx: pandoc conversion, then
python-docx post-processing (Arial, bordered tables with shaded header row,
0.75 in. margins, optional landscape, page-number footer).

Usage:
    python scripts/pursuit/md_to_docx.py IN.md OUT.docx [--landscape]
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from scripts.lib.guard_cwd import path_inside, require_proposal_or_engine_root  # noqa: E402

from docx import Document  # noqa: E402
from docx.enum.section import WD_ORIENT  # noqa: E402
from docx.oxml import OxmlElement  # noqa: E402
from docx.oxml.ns import qn  # noqa: E402
from docx.shared import Inches, Pt, RGBColor  # noqa: E402

FONT = "Arial"


def _borders(tbl):
    tblPr = tbl._tbl.tblPr
    b = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement(f"w:{edge}")
        e.set(qn("w:val"), "single")
        e.set(qn("w:sz"), "4")
        e.set(qn("w:color"), "808080")
        b.append(e)
    tblPr.append(b)


def _shade(cell, hex_fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_fill)
    tcPr.append(shd)


def _page_field(par):
    run = par.add_run()
    for tag, text in (("begin", None), (None, "PAGE"), ("end", None)):
        if tag:
            fc = OxmlElement("w:fldChar")
            fc.set(qn("w:fldCharType"), tag)
            run._r.append(fc)
        else:
            it = OxmlElement("w:instrText")
            it.set(qn("xml:space"), "preserve")
            it.text = text
            run._r.append(it)


def post_process(path: Path, landscape: bool, footer_text: str):
    doc = Document(str(path))
    for st in doc.styles:
        try:
            if st.font is not None:
                st.font.name = FONT
                rpr = st.element.get_or_add_rPr()
                rfonts = rpr.find(qn("w:rFonts"))
                if rfonts is None:
                    rfonts = OxmlElement("w:rFonts")
                    rpr.append(rfonts)
                for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
                    rfonts.set(qn(a), FONT)
        except (AttributeError, ValueError):
            pass
    sizes = {"Normal": 10, "Body Text": 10, "First Paragraph": 10, "Compact": 10, "Title": 18,
             "Subtitle": 12, "Heading 1": 14, "Heading 2": 12, "Heading 3": 11}
    for name, sz in sizes.items():
        try:
            doc.styles[name].font.size = Pt(sz)
            if name.startswith("Heading") or name == "Title":
                doc.styles[name].font.color.rgb = RGBColor(0x1F, 0x38, 0x64)
        except KeyError:
            pass
    for sec in doc.sections:
        if landscape:
            sec.orientation = WD_ORIENT.LANDSCAPE
            sec.page_width, sec.page_height = Inches(11), Inches(8.5)
        else:
            sec.page_width, sec.page_height = Inches(8.5), Inches(11)
        for m in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
            setattr(sec, m, Inches(0.75))
        fp = sec.footer.paragraphs[0] if sec.footer.paragraphs else sec.footer.add_paragraph()
        fp.text = f"{footer_text} | Page "
        _page_field(fp)
        for r in fp.runs:
            r.font.size = Pt(8)
            r.font.name = FONT
    for tbl in doc.tables:
        _borders(tbl)
        for i, row in enumerate(tbl.rows):
            for cell in row.cells:
                if i == 0:
                    _shade(cell, "1F3864")
                for p in cell.paragraphs:
                    p.paragraph_format.space_after = Pt(0)
                    p.paragraph_format.space_before = Pt(0)
                    for run in p.runs:
                        run.font.size = Pt(8.5)
                        run.font.name = FONT
                        if i == 0:
                            run.font.bold = True
                            run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    doc.save(str(path))


def main():
    require_proposal_or_engine_root(REPO_ROOT)
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    landscape = "--landscape" in sys.argv
    if len(args) != 2:
        print(__doc__)
        sys.exit(1)
    src, out = Path(args[0]).resolve(), Path(args[1]).resolve()
    for p in (src, out.parent):
        if not path_inside(p, REPO_ROOT):
            print(f"✖ md_to_docx: path outside repo: {p}", file=sys.stderr)
            sys.exit(1)
    if out.exists():
        print(f"✖ md_to_docx: refusing to overwrite {out}", file=sys.stderr)
        sys.exit(1)
    subprocess.run(["pandoc", str(src), "-f", "markdown+pipe_tables+yaml_metadata_block", "-t", "docx",
                    "-o", str(out)], check=True)
    post_process(out, landscape, f"BFA | {src.stem.replace('_', ' ')} | DRAFT")
    zip_fix(out)
    print(f"✔ {out.name}")


def zip_fix(path: Path):
    """Drop ZIP directory entries (Word can refuse them via cloud co-editing)."""
    import zipfile
    tmp = path.with_suffix(".tmp.zip")
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if not item.filename.endswith("/"):
                zout.writestr(item, zin.read(item.filename))
    import time
    for attempt in range(10):  # network shares / AV scanners can briefly lock the file
        try:
            tmp.replace(path)
            return
        except PermissionError:
            time.sleep(1 + attempt)
    raise PermissionError(f"could not replace {path} after retries")


if __name__ == "__main__":
    main()
