#!/usr/bin/env python3
"""scripts/pursuit/fill_b592_letter.py

Populate the BFA fee letter template for the B592 mechanical calculation
peer review (review only: no design, no seal, no site visits).

Input : _scratch/letter/un/            (unzipped + run-merged template)
Output: _scratch/letter/B592_Fee_Proposal_Letter.docx
Publish with scripts/publish/publish_output.py afterwards.
"""
from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from scripts.lib.guard_cwd import require_proposal_or_engine_root  # noqa: E402

UN = REPO_ROOT / "_scratch" / "letter" / "un"
OUT = REPO_ROOT / "_scratch" / "letter" / "B592_Fee_Proposal_Letter.docx"

FEE = "$7,611.56"
DATE = "November 16, 2026"
SIGNER = "Jonathan Tapscott"
SIGNER_TITLE = "Director of Technology & Business Development"

FIELDS = [  # (placeholder text, value) - filled in document order, first match each
    ("Click to add Date", DATE),
    ("Click to add Addressed to", "Ennio Bruno, Director, Federal Operations"),
    ("Click to add To Company", "G Force, an FBSG Inc. Company"),
    ("Click to add To Street Address", "3019 W. Germantown Pike"),
    ("Click to add To City, State Zip", "Norristown, PA 19403"),
    ("Click to add to Email", "ebruno@fbsginc.com"),
    ("Click to add RE Services", "Mechanical Calculation Peer Review Services"),
    ("Click to add RE Project", "FY26 Special Project, Building 592 Renovations (RM16-1405), Work Order 1808017"),
    ("Click to add RE Location", "Philadelphia Navy Yard Annex, Philadelphia, PA"),
    ("Click to add Addressed to First Name", "Ennio"),
    ("Click here to add Client Name", "G Force"),
    ("Click here to add Phone Number", "757-226-8245"),
    ("Click here to add email address", "jtapscott@bfa-eng.com"),
    ("Click here to add Signatory Name", SIGNER),
    ("Click here to add Signatory Title", SIGNER_TITLE),
    ("Click here to add Printed Name", SIGNER),
    ("Click here to add Title", SIGNER_TITLE),
    ("Click here to add Date", DATE),
]

INTRO = ("Bowman, Foster & Associates, Inc. is pleased to provide this proposal for mechanical engineering "
         "consulting services to G Force (The Client) to assist with the renovation of Building 592 at the Naval "
         "Foundry and Propeller Center for the above referenced project. The project involves an independent peer "
         "review of the delegated design mechanical calculations for the new wood dust collection, ductwork, and "
         "explosion protection system serving the Mezzanine Pattern Shop.")
BASIS = ("This proposal is based on the contract documents set forth by NAVFAC Mid-Atlantic (The Owner) under "
         "Contract N40085-24-D-0009, Work Order 1808017 (drawings dated September 24, 2026; specifications approved "
         "October 23, 2026). The scope of work calls for a review of the delegated design calculations for "
         "compliance with, and as required by, the Owner's contract documents, UFGS 23 51 43.00 20, 23 35 19.00 20, "
         "and 23 30 00. This is a review-only service. Bowman, Foster & Associates, Inc. will not prepare, sign, or "
         "seal design calculations or shop drawings, and will not perform the post-installation inspection or "
         "Certification of Compliance. Those remain the responsibility of the Contractor's Delegated Design "
         "Professional Engineer.")
CODES = [
    "NFPA 664, Prevention of Fires and Explosions in Wood Processing and Woodworking Facilities (2020)",
    "NFPA 68, Explosion Protection by Deflagration Venting",
    "NFPA 69, Explosion Prevention Systems",
    "NFPA 91, Exhaust Systems for Air Conveying of Vapors, Gases, Mists, and Particulate Solids",
    "NFPA 654, Prevention of Fire and Dust Explosions from Combustible Particulate Solids",
    "ACGIH Industrial Ventilation: A Manual of Recommended Practice for Design",
    "SMACNA Round Industrial Duct Construction Standards",
    "UFC 3-410-01, Heating, Ventilating, and Air Conditioning Systems",
    "UFGS 23 51 43.00 20, 23 35 19.00 20, and 23 30 00",
]
SCOPE_SUMMARY = ("Bowman, Foster & Associates, Inc. will review the delegated design mechanical calculation package "
                 "furnished by the Client (prepared by the dust collector manufacturer and/or the Contractor's "
                 "Delegated Design Professional Engineer) for conformance with the contract documents and the codes "
                 "and standards listed above, and will issue one round of written review comments.")
# (level, kind, text): kind = head (italic heading style) or detail
PHASING = [
    (0, "head", "Kickoff and Document Review"),
    (1, "detail", "Receive the delegated design calculation package and manufacturer data from the Client."),
    (1, "detail", "Review the mechanical drawings, schedules (M-601, M-602), and specifications to establish the review basis."),
    (0, "head", "Mechanical Calculation Peer Review"),
    (1, "head", "Duct Aerodynamic Calculations"),
    (2, "detail", "Verify node-by-node static pressure losses, duct and runout sizing, system balance, and minimum transport velocities (mains 3,500 FPM minimum; runouts 4,000 FPM minimum) per ACGIH and NFPA 664."),
    (1, "head", "Deflagration Venting (NFPA 68)"),
    (2, "detail", "Verify vent area based on collector volume, reduced pressure (Pred), and the specified dust characteristics (Kst 200 bar-m/s minimum, Pmax 8.5 bar minimum), and vent reaction forces."),
    (1, "head", "Explosion Isolation (NFPA 69)"),
    (2, "detail", "Verify flap valve placement (Lmin/Lmax) against the manufacturer's test certification, and the rotary airlock isolation criteria."),
    (1, "head", "Recirculation (NFPA 664)"),
    (2, "detail", "Confirm whether exhaust air is recirculated and whether an abort gate is required."),
    (1, "head", "Collector and Fan Performance"),
    (2, "detail", "Verify fan selection against the system curve, air-to-cloth ratio, filter pressure drop, and duct pressure class."),
    (1, "head", "Review Comments"),
    (2, "detail", "Issue one consolidated written comment log to the Client."),
    (0, "head", "Construction Period Services"),
    (1, "detail", "Not included. Available as an Additional Service."),
]
EXTRA_ADDITIONAL = [
    "Review of revised or resubmitted calculations after the first round of comments.",
    "Preparation, signing, or sealing of delegated design calculations or shop drawings; site visits; witnessing of tests; or Certification of Compliance.",
]
CLIENT_RESP = {
    "Provide access to all areas of the building": "Provide the complete delegated design calculation package, including manufacturer data, equipment selections, and test certificates, in electronic format.",
    "Architectural Drawings": "Contract drawings and specifications, including all amendments",
    "Structural Drawings": "Dust collector manufacturer shop drawings and product data",
    "Site Plans": "Explosion protection vendor data and test certificates",
}
FEE_CELLS = {
    "Design Documentation": "Mechanical Calculation Peer Review",
    "$[Design Fee]": FEE,
    "$[CPS Fee]": "Not Included",
    "$[Meet/SI Fee]": "Not Included",
    "$[Record Drawing Fee]": "Not Included",
    "$[Travel Fee]": "Not Required",
    "$[Repro Fee]": "Not Included",
    "$Total": FEE,
}

# Self-closing empty paragraphs (<w:p .../>) must match first, or the lazy
# pattern would swallow them together with the following paragraph.
P_RE = re.compile(r"<w:p(?:\s[^>]*?)?/>|<w:p(?:\s[^>]*)?>.*?</w:p>", re.S)


def text_of(p):
    return "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", p)).replace("&amp;", "&")


def clean_rpr(rpr):
    rpr = re.sub(r'<w:rStyle w:val="PlaceholderText"/>', "", rpr)
    return re.sub(r'<w:highlight w:val="[^"]+"/>', "", rpr)


def fill(x, ph, val):
    i = x.find(f">{ph}</w:t>")
    if i < 0:
        raise SystemExit(f"placeholder not found: {ph}")
    rs = max(x.rfind("<w:r>", 0, i), x.rfind("<w:r ", 0, i))
    re_ = x.find("</w:r>", i) + 6
    run = x[rs:re_]
    m = re.search(r"<w:rPr>.*?</w:rPr>", run, re.S)
    rpr = clean_rpr(m.group(0)) if m else ""
    new_run = f'<w:r>{rpr}<w:t xml:space="preserve">{escape(val)}</w:t></w:r>'
    x = x[:rs] + new_run + x[re_:]
    ss = x.rfind("<w:sdt>", 0, rs)
    se = x.find("</w:sdtPr>", ss)
    if ss >= 0 and se > 0:
        x = x[:ss] + x[ss:se].replace("<w:showingPlcHdr/>", "") + x[se:]
    return x


def para_with_text(p, text):
    """Same paragraph properties and first-run formatting; new single-run text."""
    open_tag = re.match(r"<w:p[^>]*>", p).group(0)
    ppr = re.search(r"<w:pPr>.*?</w:pPr>", p, re.S)
    first_run = re.search(r"<w:r[ >].*?</w:r>", p, re.S)
    rpr = ""
    if first_run:
        m = re.search(r"<w:rPr>.*?</w:rPr>", first_run.group(0), re.S)
        rpr = clean_rpr(m.group(0)) if m else ""
    open_tag = re.sub(r' w14:paraId="[^"]+"', "", open_tag)
    open_tag = re.sub(r' w14:textId="[^"]+"', "", open_tag)
    return (f'{open_tag}{ppr.group(0) if ppr else ""}<w:r>{rpr}'
            f'<w:t xml:space="preserve">{escape(text)}</w:t></w:r></w:p>')


def main():
    require_proposal_or_engine_root(REPO_ROOT)
    global UN, OUT
    if len(sys.argv) == 3:  # optional: UNZIPPED_DIR OUT_DOCX
        UN, OUT = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    docp = UN / "word" / "document.xml"
    x = docp.read_text(encoding="utf-8")

    for ph, val in FIELDS:
        x = fill(x, ph, val)

    paras = list(P_RE.finditer(x))
    T = [text_of(m.group(0)) for m in paras]

    def idx(prefix, start=0):
        for i in range(start, len(T)):
            if T[i].strip().startswith(prefix):
                return i
        raise SystemExit(f"paragraph not found: {prefix}")

    repl: dict[int, str] = {}
    raw = [m.group(0) for m in paras]

    repl[idx("Bowman, Foster & Associates, Inc. is pleased")] = para_with_text(raw[idx("Bowman, Foster & Associates, Inc. is pleased")], INTRO)
    repl[idx("This proposal is based on the set forth")] = para_with_text(raw[idx("This proposal is based on the set forth")], BASIS)
    ci = idx("Click to add codes/standards")
    repl[ci] = "".join(para_with_text(raw[ci], c) for c in CODES)
    si = idx("Click to add Scope of Services Summary")
    repl[si] = para_with_text(raw[si], SCOPE_SUMMARY)

    # Project phasing: replace from "Kickoff Meeting..." through last construction-period item
    k0 = idx("Kickoff Meeting and Site Investigation")
    tpl = {
        (0, "head"): raw[k0],
        (1, "detail"): raw[idx("Attend pre-construction conference.")],
        (1, "head"): raw[idx("35% Schematic Design Development")],
        (2, "detail"): raw[idx("Click here to add 35% Submittal Details")],
    }
    k1 = idx("Participate in construction progress meetings.")
    repl[k0] = "".join(para_with_text(tpl[(lvl, kind)], t) for lvl, kind, t in PHASING)
    for i in range(k0 + 1, k1 + 1):
        repl[i] = ""

    ai = idx("Additional consulting services beyond")
    repl[ai] = raw[ai] + "".join(para_with_text(raw[ai], t) for t in EXTRA_ADDITIONAL)

    for prefix, new in CLIENT_RESP.items():
        i = idx(prefix)
        repl[i] = para_with_text(raw[i], new)

    fs = idx("Professional Fees")
    for old, new in FEE_CELLS.items():
        i = idx(old, fs)
        repl[i] = para_with_text(raw[i], new)

    out = []
    pos = 0
    for i, m in enumerate(paras):
        out.append(x[pos:m.start()])
        out.append(repl.get(i, m.group(0)))
        pos = m.end()
    out.append(x[pos:])
    x = "".join(out)

    left = re.findall(r"Click (?:here )?to add[^<]*", x)
    if left:
        raise SystemExit(f"unfilled placeholders: {left}")
    docp.write_text(x, encoding="utf-8")

    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        ct = UN / "[Content_Types].xml"
        z.write(ct, "[Content_Types].xml")
        for f in sorted(UN.rglob("*")):
            if f.is_file() and f != ct:
                z.write(f, f.relative_to(UN).as_posix())
    print(f"✔ {OUT.relative_to(REPO_ROOT).as_posix()}")


if __name__ == "__main__":
    main()
