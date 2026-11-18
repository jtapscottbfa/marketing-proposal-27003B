#!/usr/bin/env python3
"""scripts/pursuit/build_b592_package.py

Builds the B592 pursuit package into _scratch/build/ (gitignored). Publish
the results with scripts/publish/publish_output.py (never-overwrite
versioning), then save state with scripts/git/publish_commit.sh.

Outputs (in _scratch/build/):
    B592_RFP_Shred.md / .xlsx
    B592_Proposal_Schedule.md / .xlsx
    B592_Fee_Estimate.xlsx           (formula-driven; recalc in Excel)
    B592_Fee_Summary.md              (values computed here; must match xlsx)
    calendar/*.ics                   (combined + one per event)
"""
from __future__ import annotations

import datetime as dt
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
from scripts.lib.guard_cwd import require_proposal_or_engine_root  # noqa: E402
from scripts.pursuit import b592_data as D  # noqa: E402

from openpyxl import Workbook  # noqa: E402
from openpyxl.comments import Comment  # noqa: E402
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side  # noqa: E402
from openpyxl.utils import get_column_letter as L  # noqa: E402

BUILD = REPO_ROOT / "_scratch" / "build"
TODAY = "2026-11-09"

# ------------------------------------------------------------------ styles
F = "Arial"
F_BASE = Font(name=F, size=10)
F_BOLD = Font(name=F, size=10, bold=True)
F_TITLE = Font(name=F, size=14, bold=True, color="1F3864")
F_SUB = Font(name=F, size=9, italic=True, color="595959")
F_HDR = Font(name=F, size=10, bold=True, color="FFFFFF")
F_INPUT = Font(name=F, size=10, color="0000FF")
F_LINK = Font(name=F, size=10, color="008000")
FILL_HDR = PatternFill("solid", fgColor="1F3864")
FILL_INPUT = PatternFill("solid", fgColor="FFFF00")
FILL_TOT = PatternFill("solid", fgColor="D9E1F2")
FILL_BAND = PatternFill("solid", fgColor="F2F2F2")
THIN = Side(style="thin", color="BFBFBF")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(wrap_text=True, vertical="top")
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
USD = '$#,##0;($#,##0);"-"'
USD2 = '$#,##0.00;($#,##0.00);"-"'
HRS = '#,##0.0;(#,##0.0);"-"'


def style_range(ws, rng, font=None, fill=None, fmt=None, align=None, border=BOX):
    for row in ws[rng]:
        for c in row:
            if font:
                c.font = font
            if fill:
                c.fill = fill
            if fmt:
                c.number_format = fmt
            if align:
                c.alignment = align
            if border:
                c.border = border


def header(ws, row, labels, col=1):
    for i, lab in enumerate(labels):
        c = ws.cell(row=row, column=col + i, value=lab)
        c.font, c.fill, c.alignment, c.border = F_HDR, FILL_HDR, CENTER, BOX


def title(ws, text, sub=None):
    ws["A1"] = text
    ws["A1"].font = F_TITLE
    if sub:
        ws["A2"] = sub
        ws["A2"].font = F_SUB


def widths(ws, ws_widths):
    for i, w in enumerate(ws_widths, start=1):
        ws.column_dimensions[L(i)].width = w


def table(ws, start_row, labels, rows, col_widths=None, wrap_cols=()):
    header(ws, start_row, labels)
    for r, row in enumerate(rows, start=start_row + 1):
        for c, val in enumerate(row, start=1):
            cell = ws.cell(row=r, column=c, value=val)
            cell.font, cell.border = F_BASE, BOX
            cell.alignment = WRAP
        if (r - start_row) % 2 == 0:
            for c in range(1, len(labels) + 1):
                ws.cell(row=r, column=c).fill = FILL_BAND
    if col_widths:
        widths(ws, col_widths)
    ws.freeze_panes = ws.cell(row=start_row + 1, column=1)
    ws.auto_filter.ref = f"A{start_row}:{L(len(labels))}{start_row + len(rows)}"


# ------------------------------------------------------------------ fee math (python mirror)
RATE = {code: rate for code, _, _, rate in D.ROLES}
TRADE_OF = {code: trade for code, _, trade, _ in D.ROLES}
TRIP_COST = sum(q * u for _, q, _, u, _ in D.TRIP_ITEMS)


def fee_numbers():
    rows = []
    for did, ph, name, ref, sub, hrs, trips, pkgs in D.DELIVERABLES:
        h = sum(hrs.values())
        lab = sum(v * RATE[k] for k, v in hrs.items())
        exp = trips * TRIP_COST + pkgs * D.PRINT_SHIP_UNIT
        by_trade = {t: sum(v * RATE[k] for k, v in hrs.items() if TRADE_OF[k] == t) for t in D.TRADES}
        hrs_trade = {t: sum(v for k, v in hrs.items() if TRADE_OF[k] == t) for t in D.TRADES}
        rows.append(dict(id=did, phase=ph, name=name, ref=ref, sub=sub, hours=h, labor=lab,
                         exp=exp, total=lab + exp, by_trade=by_trade, hrs_trade=hrs_trade,
                         trips=trips, pkgs=pkgs))
    opts = []
    for oid, name, hrs, trips in D.OPTIONS:
        h = sum(hrs.values())
        lab = sum(v * RATE[k] for k, v in hrs.items())
        opts.append(dict(id=oid, name=name, hours=h, labor=lab, exp=trips * TRIP_COST,
                         total=lab + trips * TRIP_COST))
    return rows, opts


# ------------------------------------------------------------------ fee workbook
def build_fee_xlsx(path: Path):
    roles = [r[0] for r in D.ROLES]
    nR = len(roles)
    nD = len(D.DELIVERABLES)
    wb = Workbook()

    # README
    ws = wb.active
    ws.title = "README"
    title(ws, "B592 Dust Collection Delegated Design Peer Review: Fee Estimate (DRAFT)",
          f"Prepared {TODAY} | Bowman, Foster & Associates for G Force Construction (FBSG) | NAVFAC N40085-24-D-0009, WO 1808017")
    lines = [
        ("Purpose", "MEP fee for Contractor's Delegated Design PE peer review / verification / seal of the B592 dust collection and explosion-protection delegated design (UFGS 23 51 43.00 20)."),
        ("How to edit", "Change hours ONLY in Hours_Matrix (blue cells) and rates ONLY in Rates (yellow cells). Trips / sealed packages are blue cells in Fee_by_Deliverable. Everything else is formula-driven."),
        ("Color code", "Blue text = input. Black = formula. Green = link to another sheet. Yellow fill = assumption the user must confirm (labor rates)."),
        ("Summary", "Base fee by trade and phase, expenses, options, and integrity checks (must read 0)."),
        ("Rates", "Labor categories, trade mapping, hourly billing rates (ASSUMED placeholders)."),
        ("Hours_Matrix", "Deliverable x role hours. Row 3 = trade per role; row 4 = rate per role."),
        ("Fee_by_Trade", "Labor $ and hours by trade (Mechanical, Structural, Electrical, Fire Protection, Plumbing, PM/QA-QC) for each deliverable."),
        ("Fee_by_Deliverable", "Hours, labor, expenses, and total for each deliverable D01-D16."),
        ("Expenses", "Per-trip travel build-up and sealed package print/ship."),
        ("Options", "Optional services priced separately (not in base)."),
        ("Transcribe", "Flat one-row-per-(deliverable, role) list for keying into the internal fee template. Rows exist only for non-zero hours at build time; rebuild if you add a role to a deliverable."),
        ("Assumptions", "Assumptions and exclusions that bound the fee."),
        ("Example", "Hours_Matrix row D02, column MPE = 10 means 10 Mechanical PE hours on duct calc verification at the Rates!MPE rate."),
    ]
    for i, (k, v) in enumerate(lines, start=4):
        ws.cell(row=i, column=1, value=k).font = F_BOLD
        c = ws.cell(row=i, column=2, value=v)
        c.font, c.alignment = F_BASE, WRAP
    widths(ws, [20, 110])

    # Rates
    wr = wb.create_sheet("Rates")
    title(wr, "Labor Categories and Billing Rates",
          "ASSUMED placeholder rates: replace with BFA's current rate sheet (yellow cells).")
    header(wr, 4, ["Code", "Labor Category", "Trade", "Rate ($/hr)", "Basis"])
    for i, (code, role, trade, rate) in enumerate(D.ROLES, start=5):
        wr.cell(row=i, column=1, value=code)
        wr.cell(row=i, column=2, value=role)
        wr.cell(row=i, column=3, value=trade)
        c = wr.cell(row=i, column=4, value=rate)
        c.font, c.fill, c.number_format = F_INPUT, FILL_INPUT, USD2
        wr.cell(row=i, column=5, value="ASSUMED: 2026 Mid-Atlantic fully burdened billing rate; confirm")
    style_range(wr, f"A5:C{4 + nR}", font=F_BASE)
    style_range(wr, f"E5:E{4 + nR}", font=F_SUB)
    for i in range(5, 5 + nR):
        wr.cell(row=i, column=4).border = BOX
    wr.cell(row=5, column=4).comment = Comment("Placeholder rate. No BFA rate sheet in repo. Replace with current billing rates.", "Claude")
    widths(wr, [8, 46, 18, 13, 62])
    RATE_RANGE = f"Rates!$A$5:$A${4 + nR}"

    # Hours_Matrix
    wh = wb.create_sheet("Hours_Matrix")
    title(wh, "Labor Hours by Deliverable and Role (inputs in blue)",
          "Row 3 = trade, row 4 = rate (both linked from Rates). Labor Fee = SUMPRODUCT(rates, hours).")
    first, last = 4, 3 + nR  # columns D..M
    fc, lc = L(first), L(last)
    wh.cell(row=3, column=3, value="Trade").font = F_BOLD
    wh.cell(row=4, column=3, value="Rate ($/hr)").font = F_BOLD
    for j, code in enumerate(roles):
        col = first + j
        cl = L(col)
        c3 = wh.cell(row=3, column=col, value=f"=INDEX(Rates!$C$5:$C${4 + nR},MATCH({cl}$5,{RATE_RANGE},0))")
        c4 = wh.cell(row=4, column=col, value=f"=INDEX(Rates!$D$5:$D${4 + nR},MATCH({cl}$5,{RATE_RANGE},0))")
        c3.font, c4.font = F_LINK, F_LINK
        c3.alignment = CENTER
        c4.number_format = USD
        c3.border = c4.border = BOX
    hdr = ["ID", "Phase", "Deliverable"] + roles + ["Total Hours", "Labor Fee ($)", "Spec / Drawing Ref", "Submittal Type"]
    header(wh, 5, hdr)
    r0 = 6
    for i, (did, ph, name, ref, sub, hrs, trips, pkgs) in enumerate(D.DELIVERABLES):
        r = r0 + i
        wh.cell(row=r, column=1, value=did)
        wh.cell(row=r, column=2, value=ph)
        wh.cell(row=r, column=3, value=name)
        for j, code in enumerate(roles):
            c = wh.cell(row=r, column=first + j, value=hrs.get(code, 0))
            c.font, c.number_format, c.border = F_INPUT, HRS, BOX
        wh.cell(row=r, column=last + 1, value=f"=SUM({fc}{r}:{lc}{r})").number_format = HRS
        wh.cell(row=r, column=last + 2, value=f"=SUMPRODUCT(${fc}$4:${lc}$4,{fc}{r}:{lc}{r})").number_format = USD
        wh.cell(row=r, column=last + 3, value=ref)
        wh.cell(row=r, column=last + 4, value=sub)
        for col in (1, 2, 3, last + 1, last + 2, last + 3, last + 4):
            cc = wh.cell(row=r, column=col)
            cc.border = BOX
            if cc.font != F_INPUT:
                cc.font = F_BASE
        wh.cell(row=r, column=3).alignment = WRAP
    rt = r0 + nD  # totals row
    wh.cell(row=rt, column=3, value="TOTAL")
    for col in range(first, last + 3):
        cl = L(col)
        wh.cell(row=rt, column=col, value=f"=SUM({cl}{r0}:{cl}{rt - 1})").number_format = USD if col == last + 2 else HRS
    style_range(wh, f"A{rt}:{L(last + 4)}{rt}", font=F_BOLD, fill=FILL_TOT)
    wh.cell(row=rt + 1, column=3, value="Labor $ by role").font = F_BOLD
    for col in range(first, last + 1):
        cl = L(col)
        c = wh.cell(row=rt + 1, column=col, value=f"={cl}{rt}*{cl}$4")
        c.number_format, c.font, c.border = USD, F_BASE, BOX
    widths(wh, [6, 7, 58] + [8] * nR + [11, 13, 34, 20])
    wh.freeze_panes = "D6"
    HM_HOURS_COL = L(last + 1)
    HM_FEE_COL = L(last + 2)

    # Fee_by_Trade
    wt = wb.create_sheet("Fee_by_Trade")
    title(wt, "Labor Fee by Trade and Deliverable",
          "Each cell = SUMPRODUCT over Hours_Matrix roles whose trade matches the column header.")
    header(wt, 4, ["ID", "Deliverable"] + D.TRADES + ["Total ($)"])
    nT = len(D.TRADES)
    for i in range(nD):
        r = 5 + i
        hr = r0 + i
        wt.cell(row=r, column=1, value=f"=Hours_Matrix!A{hr}").font = F_LINK
        wt.cell(row=r, column=2, value=f"=Hours_Matrix!C{hr}").font = F_LINK
        for t in range(nT):
            col = 3 + t
            c = wt.cell(row=r, column=col,
                        value=f"=SUMPRODUCT((Hours_Matrix!${fc}$3:${lc}$3={L(col)}$4)*Hours_Matrix!${fc}$4:${lc}$4*Hours_Matrix!${fc}{hr}:${lc}{hr})")
            c.number_format, c.font = USD, F_BASE
        wt.cell(row=r, column=3 + nT, value=f"=SUM(C{r}:{L(2 + nT)}{r})").number_format = USD
        style_range(wt, f"A{r}:{L(3 + nT)}{r}")
        wt.cell(row=r, column=2).alignment = WRAP
    tr = 5 + nD
    wt.cell(row=tr, column=2, value="TOTAL LABOR")
    for col in range(3, 4 + nT):
        wt.cell(row=tr, column=col, value=f"=SUM({L(col)}5:{L(col)}{tr - 1})").number_format = USD
    style_range(wt, f"A{tr}:{L(3 + nT)}{tr}", font=F_BOLD, fill=FILL_TOT)
    # hours by trade block
    hb = tr + 3
    wt.cell(row=hb - 1, column=1, value="Hours by Trade").font = F_BOLD
    header(wt, hb, ["ID", "Deliverable"] + D.TRADES + ["Total (hrs)"])
    for i in range(nD):
        r = hb + 1 + i
        hr = r0 + i
        wt.cell(row=r, column=1, value=f"=Hours_Matrix!A{hr}").font = F_LINK
        wt.cell(row=r, column=2, value=f"=Hours_Matrix!C{hr}").font = F_LINK
        for t in range(nT):
            col = 3 + t
            c = wt.cell(row=r, column=col,
                        value=f"=SUMPRODUCT((Hours_Matrix!${fc}$3:${lc}$3={L(col)}${hb})*Hours_Matrix!${fc}{hr}:${lc}{hr})")
            c.number_format, c.font = HRS, F_BASE
        wt.cell(row=r, column=3 + nT, value=f"=SUM(C{r}:{L(2 + nT)}{r})").number_format = HRS
        style_range(wt, f"A{r}:{L(3 + nT)}{r}")
        wt.cell(row=r, column=2).alignment = WRAP
    htr = hb + 1 + nD
    wt.cell(row=htr, column=2, value="TOTAL HOURS")
    for col in range(3, 4 + nT):
        wt.cell(row=htr, column=col, value=f"=SUM({L(col)}{hb + 1}:{L(col)}{htr - 1})").number_format = HRS
    style_range(wt, f"A{htr}:{L(3 + nT)}{htr}", font=F_BOLD, fill=FILL_TOT)
    widths(wt, [6, 60] + [14] * nT + [13])
    wt.freeze_panes = "C5"
    TRADE_TOTAL_ROW, TRADE_HRS_ROW = tr, htr

    # Expenses
    we = wb.create_sheet("Expenses")
    title(we, "Reimbursable Expenses (at cost, no markup)", "Per-trip build-up; trip and package counts link from Fee_by_Deliverable.")
    header(we, 4, ["Item", "Qty", "Unit", "Unit Cost ($)", "Extended ($)", "Basis"])
    for i, (item, q, u, uc, basis) in enumerate(D.TRIP_ITEMS, start=5):
        we.cell(row=i, column=1, value=item)
        cq = we.cell(row=i, column=2, value=q)
        we.cell(row=i, column=3, value=u)
        cu = we.cell(row=i, column=4, value=uc)
        we.cell(row=i, column=5, value=f"=B{i}*D{i}").number_format = USD2
        we.cell(row=i, column=6, value=basis)
        cq.font = cu.font = F_INPUT
        cu.number_format = USD2
    nE = len(D.TRIP_ITEMS)
    style_range(we, f"A5:F{4 + nE}")
    for i in range(5, 5 + nE):
        we.cell(row=i, column=2).font = F_INPUT
        we.cell(row=i, column=4).font = F_INPUT
    pt = 5 + nE  # per trip subtotal
    we.cell(row=pt, column=1, value="Per-trip subtotal")
    we.cell(row=pt, column=5, value=f"=SUM(E5:E{pt - 1})").number_format = USD2
    style_range(we, f"A{pt}:F{pt}", font=F_BOLD, fill=FILL_TOT)
    TRIP_CELL = f"Expenses!$E${pt}"
    ps = pt + 2
    we.cell(row=ps, column=1, value="Sealed package print / seal / overnight (per package)")
    c = we.cell(row=ps, column=4, value=D.PRINT_SHIP_UNIT)
    c.font, c.number_format = F_INPUT, USD2
    we.cell(row=ps, column=6, value="ASSUMED")
    style_range(we, f"A{ps}:F{ps}")
    we.cell(row=ps, column=4).font = F_INPUT
    PKG_CELL = f"Expenses!$D${ps}"
    widths(we, [56, 8, 8, 14, 14, 40])

    # Fee_by_Deliverable
    wd = wb.create_sheet("Fee_by_Deliverable")
    title(wd, "Fee by Deliverable (Base Scope)", "Trips and sealed packages are inputs (blue).")
    header(wd, 4, ["ID", "Phase", "Deliverable", "Spec / Drawing Ref", "Submittal Type", "Hours",
                   "Site Trips", "Sealed Pkgs", "Labor ($)", "Expenses ($)", "Total ($)"])
    for i, dl in enumerate(D.DELIVERABLES):
        r = 5 + i
        hr = r0 + i
        wd.cell(row=r, column=1, value=f"=Hours_Matrix!A{hr}").font = F_LINK
        wd.cell(row=r, column=2, value=D.PHASES[dl[1]])
        wd.cell(row=r, column=3, value=f"=Hours_Matrix!C{hr}").font = F_LINK
        wd.cell(row=r, column=4, value=dl[3])
        wd.cell(row=r, column=5, value=dl[4])
        wd.cell(row=r, column=6, value=f"=Hours_Matrix!{HM_HOURS_COL}{hr}").number_format = HRS
        wd.cell(row=r, column=7, value=dl[6])
        wd.cell(row=r, column=8, value=dl[7])
        wd.cell(row=r, column=9, value=f"=Hours_Matrix!{HM_FEE_COL}{hr}").number_format = USD
        wd.cell(row=r, column=10, value=f"=G{r}*{TRIP_CELL}+H{r}*{PKG_CELL}").number_format = USD
        wd.cell(row=r, column=11, value=f"=I{r}+J{r}").number_format = USD
        style_range(wd, f"A{r}:K{r}")
        for col in (1, 3, 6, 9):
            wd.cell(row=r, column=col).font = F_LINK
        for col in (2, 4, 5, 10, 11):
            wd.cell(row=r, column=col).font = F_BASE
        for col in (7, 8):
            wd.cell(row=r, column=col).font = F_INPUT
        for col in (2, 3, 4):
            wd.cell(row=r, column=col).alignment = WRAP
    dt_ = 5 + nD
    wd.cell(row=dt_, column=3, value="BASE TOTAL")
    for col in (6, 7, 8, 9, 10, 11):
        cl = L(col)
        wd.cell(row=dt_, column=col, value=f"=SUM({cl}5:{cl}{dt_ - 1})").number_format = USD if col >= 9 else HRS
    style_range(wd, f"A{dt_}:K{dt_}", font=F_BOLD, fill=FILL_TOT)
    widths(wd, [6, 22, 52, 28, 18, 9, 8, 9, 12, 12, 12])
    wd.freeze_panes = "D5"
    # expenses totals on Expenses sheet
    et = ps + 2
    we.cell(row=et, column=1, value="Base site trips (from Fee_by_Deliverable)")
    we.cell(row=et, column=2, value=f"=Fee_by_Deliverable!G{dt_}").font = F_LINK
    we.cell(row=et, column=5, value=f"=B{et}*{TRIP_CELL}").number_format = USD2
    we.cell(row=et + 1, column=1, value="Base sealed packages (from Fee_by_Deliverable)")
    we.cell(row=et + 1, column=2, value=f"=Fee_by_Deliverable!H{dt_}").font = F_LINK
    we.cell(row=et + 1, column=5, value=f"=B{et + 1}*{PKG_CELL}").number_format = USD2
    we.cell(row=et + 2, column=1, value="TOTAL BASE EXPENSES")
    we.cell(row=et + 2, column=5, value=f"=E{et}+E{et + 1}").number_format = USD2
    style_range(we, f"A{et}:F{et + 1}")
    we.cell(row=et, column=2).font = we.cell(row=et + 1, column=2).font = F_LINK
    style_range(we, f"A{et + 2}:F{et + 2}", font=F_BOLD, fill=FILL_TOT)
    EXP_TOTAL = f"Expenses!$E${et + 2}"

    # Options
    wo = wb.create_sheet("Options")
    title(wo, "Optional Services (not in base fee)", "Hours are inputs (blue). Rates link from Rates.")
    o_first = 3
    o_last = o_first + nR - 1
    ofc, olc = L(o_first), L(o_last)
    wo.cell(row=3, column=2, value="Rate ($/hr)").font = F_BOLD
    for j, code in enumerate(roles):
        col = o_first + j
        c = wo.cell(row=3, column=col, value=f"=INDEX(Rates!$D$5:$D${4 + nR},MATCH({L(col)}$4,{RATE_RANGE},0))")
        c.font, c.number_format, c.border = F_LINK, USD, BOX
    header(wo, 4, ["ID", "Option"] + roles + ["Hours", "Trips", "Labor ($)", "Expenses ($)", "Total ($)"])
    for i, (oid, name, hrs, trips) in enumerate(D.OPTIONS):
        r = 5 + i
        wo.cell(row=r, column=1, value=oid)
        wo.cell(row=r, column=2, value=name)
        for j, code in enumerate(roles):
            c = wo.cell(row=r, column=o_first + j, value=hrs.get(code, 0))
            c.number_format = HRS
        wo.cell(row=r, column=o_last + 1, value=f"=SUM({ofc}{r}:{olc}{r})").number_format = HRS
        wo.cell(row=r, column=o_last + 2, value=trips)
        wo.cell(row=r, column=o_last + 3, value=f"=SUMPRODUCT(${ofc}$3:${olc}$3,{ofc}{r}:{olc}{r})").number_format = USD
        wo.cell(row=r, column=o_last + 4, value=f"={L(o_last + 2)}{r}*{TRIP_CELL}").number_format = USD
        wo.cell(row=r, column=o_last + 5, value=f"={L(o_last + 3)}{r}+{L(o_last + 4)}{r}").number_format = USD
        style_range(wo, f"A{r}:{L(o_last + 5)}{r}", font=F_BASE)
        for j in range(nR):
            wo.cell(row=r, column=o_first + j).font = F_INPUT
        wo.cell(row=r, column=o_last + 2).font = F_INPUT
        wo.cell(row=r, column=2).alignment = WRAP
    widths(wo, [8, 60] + [7] * nR + [8, 7, 12, 12, 12])
    wo.freeze_panes = "C5"
    OPT_TOTAL_COL = L(o_last + 5)
    OPT_HRS_COL = L(o_last + 1)

    # Transcribe
    wx = wb.create_sheet("Transcribe")
    title(wx, "Flat Fee Lines for Internal Template", "One row per deliverable x role with hours > 0 at build time. All values link to Hours_Matrix.")
    header(wx, 4, ["Line", "Deliverable ID", "Phase", "Deliverable", "Trade", "Role Code", "Labor Category", "Rate ($/hr)", "Hours", "Extended ($)"])
    r = 5
    line = 1
    for i, dl in enumerate(D.DELIVERABLES):
        hr = r0 + i
        for j, code in enumerate(roles):
            if dl[5].get(code, 0) <= 0:
                continue
            cl = L(first + j)
            vals = [line, f"=Hours_Matrix!A{hr}", D.PHASES[dl[1]], f"=Hours_Matrix!C{hr}", f"=Hours_Matrix!{cl}$3",
                    f"=Hours_Matrix!{cl}$5", f"=INDEX(Rates!$B$5:$B${4 + nR},MATCH(F{r},{RATE_RANGE},0))",
                    f"=Hours_Matrix!{cl}$4", f"=Hours_Matrix!{cl}{hr}", f"=H{r}*I{r}"]
            for c, v in enumerate(vals, start=1):
                cell = wx.cell(row=r, column=c, value=v)
                cell.font, cell.border = (F_LINK if isinstance(v, str) and v.startswith("=Hours") else F_BASE), BOX
            wx.cell(row=r, column=8).number_format = USD
            wx.cell(row=r, column=9).number_format = HRS
            wx.cell(row=r, column=10).number_format = USD
            r += 1
            line += 1
    xr = r
    wx.cell(row=xr, column=4, value="TOTAL")
    wx.cell(row=xr, column=9, value=f"=SUM(I5:I{xr - 1})").number_format = HRS
    wx.cell(row=xr, column=10, value=f"=SUM(J5:J{xr - 1})").number_format = USD
    style_range(wx, f"A{xr}:J{xr}", font=F_BOLD, fill=FILL_TOT)
    widths(wx, [6, 10, 26, 56, 16, 8, 40, 11, 8, 12])
    wx.freeze_panes = "A5"
    wx.auto_filter.ref = f"A4:J{xr - 1}"

    # Assumptions
    wa = wb.create_sheet("Assumptions")
    title(wa, "Assumptions and Exclusions (bound the fee)")
    header(wa, 4, ["#", "Assumption"])
    for i, a in enumerate(D.ASSUMPTIONS, start=5):
        wa.cell(row=i, column=1, value=f"A{i - 4:02d}")
        wa.cell(row=i, column=2, value=a).alignment = WRAP
    style_range(wa, f"A5:B{4 + len(D.ASSUMPTIONS)}", font=F_BASE)
    xs = 6 + len(D.ASSUMPTIONS)
    header(wa, xs, ["#", "Exclusion"])
    for i, a in enumerate(D.EXCLUSIONS, start=xs + 1):
        wa.cell(row=i, column=1, value=f"X{i - xs:02d}")
        wa.cell(row=i, column=2, value=a).alignment = WRAP
    style_range(wa, f"A{xs + 1}:B{xs + len(D.EXCLUSIONS)}", font=F_BASE)
    for row in wa.iter_rows(min_row=5, max_row=xs + len(D.EXCLUSIONS)):
        row[1].alignment = WRAP
    widths(wa, [6, 120])

    # Summary (first visible after README)
    wsu = wb.create_sheet("Summary", 1)
    title(wsu, "B592 Delegated Design Peer Review: Fee Summary (DRAFT)",
          "All values are formulas. Labor rates are ASSUMED; see Rates.")
    info = [("Project", D.PROJECT["title"]), ("Location", D.PROJECT["location"]),
            ("Client (Prime)", D.PROJECT["prime"]), ("BFA Role", D.PROJECT["bfa_role"]),
            ("Fee Basis", "Lump sum by phase; expenses at cost; quote valid 90 days")]
    for i, (k, v) in enumerate(info, start=4):
        wsu.cell(row=i, column=1, value=k).font = F_BOLD
        c = wsu.cell(row=i, column=2, value=v)
        c.font, c.alignment = F_BASE, WRAP
        wsu.merge_cells(start_row=i, start_column=2, end_row=i, end_column=4)
    s = 10
    header(wsu, s, ["Fee by Trade", "Hours", "Labor ($)", "% of Labor"])
    for k, t in enumerate(D.TRADES):
        r = s + 1 + k
        col = L(3 + k)
        wsu.cell(row=r, column=1, value=t)
        wsu.cell(row=r, column=2, value=f"=Fee_by_Trade!{col}{TRADE_HRS_ROW}").number_format = HRS
        wsu.cell(row=r, column=3, value=f"=Fee_by_Trade!{col}{TRADE_TOTAL_ROW}").number_format = USD
        wsu.cell(row=r, column=4, value=f"=IF($C${s + 1 + len(D.TRADES)}=0,0,C{r}/$C${s + 1 + len(D.TRADES)})").number_format = "0.0%"
        style_range(wsu, f"A{r}:D{r}", font=F_BASE)
        wsu.cell(row=r, column=2).font = wsu.cell(row=r, column=3).font = F_LINK
    st = s + 1 + len(D.TRADES)
    wsu.cell(row=st, column=1, value="Total Labor")
    wsu.cell(row=st, column=2, value=f"=SUM(B{s + 1}:B{st - 1})").number_format = HRS
    wsu.cell(row=st, column=3, value=f"=SUM(C{s + 1}:C{st - 1})").number_format = USD
    wsu.cell(row=st, column=4, value=f"=SUM(D{s + 1}:D{st - 1})").number_format = "0.0%"
    style_range(wsu, f"A{st}:D{st}", font=F_BOLD, fill=FILL_TOT)

    p = st + 2
    header(wsu, p, ["Fee by Phase", "Hours", "Labor ($)", "Total incl. Expenses ($)"])
    hm_rng = f"Hours_Matrix!$B${r0}:$B${rt - 1}"
    for k, (code, name) in enumerate(D.PHASES.items()):
        r = p + 1 + k
        wsu.cell(row=r, column=1, value=name)
        wsu.cell(row=r, column=2, value=f'=SUMIF({hm_rng},"{code}",Hours_Matrix!${HM_HOURS_COL}${r0}:${HM_HOURS_COL}${rt - 1})').number_format = HRS
        wsu.cell(row=r, column=3, value=f'=SUMIF({hm_rng},"{code}",Hours_Matrix!${HM_FEE_COL}${r0}:${HM_FEE_COL}${rt - 1})').number_format = USD
        wsu.cell(row=r, column=4, value=f'=SUMIF(Fee_by_Deliverable!$B$5:$B${dt_ - 1},"{name}",Fee_by_Deliverable!$K$5:$K${dt_ - 1})').number_format = USD
        style_range(wsu, f"A{r}:D{r}", font=F_BASE)
    pt_ = p + 1 + len(D.PHASES)
    wsu.cell(row=pt_, column=1, value="Total")
    for col in (2, 3, 4):
        cl = L(col)
        wsu.cell(row=pt_, column=col, value=f"=SUM({cl}{p + 1}:{cl}{pt_ - 1})").number_format = USD if col > 2 else HRS
    style_range(wsu, f"A{pt_}:D{pt_}", font=F_BOLD, fill=FILL_TOT)

    b = pt_ + 2
    header(wsu, b, ["Base Fee", "", "Amount ($)", ""])
    base_rows = [("Labor (lump sum)", f"=C{st}"), ("Reimbursable expenses (at cost)", f"={EXP_TOTAL}"),
                 ("BASE FEE TOTAL", f"=C{b + 1}+C{b + 2}"), ("Total hours", f"=B{st}"),
                 ("Blended labor rate ($/hr)", f"=IF(C{b + 4}=0,0,C{b + 1}/C{b + 4})")]
    for k, (lab, f) in enumerate(base_rows):
        r = b + 1 + k
        wsu.cell(row=r, column=1, value=lab)
        c = wsu.cell(row=r, column=3, value=f)
        c.number_format = HRS if "hours" in lab else (USD2 if "rate" in lab else USD)
        style_range(wsu, f"A{r}:D{r}", font=F_BASE)
    style_range(wsu, f"A{b + 3}:D{b + 3}", font=F_BOLD, fill=FILL_TOT)
    wsu.cell(row=b + 3, column=3).number_format = USD
    BASE_TOTAL_CELL = f"C{b + 3}"

    o = b + 7
    header(wsu, o, ["Optional Services (not in base)", "Hours", "Total ($)", ""])
    for k, (oid, name, _, _) in enumerate(D.OPTIONS):
        r = o + 1 + k
        wsu.cell(row=r, column=1, value=f"{oid}: {name}").alignment = WRAP
        wsu.cell(row=r, column=2, value=f"=Options!{OPT_HRS_COL}{5 + k}").number_format = HRS
        wsu.cell(row=r, column=3, value=f"=Options!{OPT_TOTAL_COL}{5 + k}").number_format = USD
        style_range(wsu, f"A{r}:D{r}", font=F_BASE)
        wsu.cell(row=r, column=1).alignment = WRAP
        wsu.cell(row=r, column=2).font = wsu.cell(row=r, column=3).font = F_LINK

    ck = o + 2 + len(D.OPTIONS)
    header(wsu, ck, ["Integrity Checks (must be 0)", "", "Difference", ""])
    checks = [("Trade total vs Hours_Matrix labor", f"=ROUND(C{st}-Hours_Matrix!{HM_FEE_COL}{rt},2)"),
              ("Phase total vs Hours_Matrix labor", f"=ROUND(C{pt_}-Hours_Matrix!{HM_FEE_COL}{rt},2)"),
              ("Deliverable total vs base fee", f"=ROUND(Fee_by_Deliverable!K{dt_}-{BASE_TOTAL_CELL},2)"),
              ("Transcribe total vs Hours_Matrix labor", f"=ROUND(Transcribe!J{xr}-Hours_Matrix!{HM_FEE_COL}{rt},2)")]
    for k, (lab, f) in enumerate(checks):
        r = ck + 1 + k
        wsu.cell(row=r, column=1, value=lab)
        wsu.cell(row=r, column=3, value=f).number_format = USD2
        style_range(wsu, f"A{r}:D{r}", font=F_BASE)
    widths(wsu, [62, 12, 16, 20])

    for wsx in wb.worksheets:
        wsx.sheet_view.showGridLines = False
        wsx.page_setup.orientation = "landscape"
        wsx.page_setup.fitToWidth = 1
        wsx.page_setup.fitToHeight = 0
        wsx.sheet_properties.pageSetUpPr.fitToPage = True
    wb.calculation.fullCalcOnLoad = True
    wb.save(path)


# ------------------------------------------------------------------ shred
def md_table(headers, rows, w=None):
    """Pipe table. w = relative column widths (pandoc reads them from dash counts)."""
    seps = ["-" * max(3, n) for n in w] if w else ["---"] * len(headers)
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join(seps) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(c).replace("|", "/").replace("\n", " ") for c in r) + " |")
    return "\n".join(out)


def build_shred(md_path: Path, xlsx_path: Path):
    P = D.PROJECT
    facts = [("Project", P["title"]), ("Location", P["location"]), ("Owner", P["owner"]),
             ("Contract vehicle", P["contract"]), ("Work order", P["work_order"]),
             ("Designer of Record", P["eor"]), ("Prime / client", P["prime"]),
             ("Client POC", P["client_poc"]), ("Client cc", P["client_cc"]), ("BFA POC", P["bfa_poc"]),
             ("BFA role requested", "Peer review on the mechanical calculations needed (E. Bruno, 2026-11-04)"),
             ("BFA role as priced", P["bfa_role"]), ("Documents", P["docs_dates"]),
             ("BFA quote due", P["proposal_due"]), ("Page limit / format", "None stated (GC quote; no Section L/M)"),
             ("Evaluation", "None stated; G Force selects sub on price and qualifications (assumed)"),
             ("Small business", "Prime is 8(a)/HUBZone/EDWOSB/WOSB/SDB; no sub goal stated")]
    md = [f"# B592 RFP Shred: Dust Collection Delegated Design Peer Review",
          "",
          f"- **RFP:** {P['title']}, Philadelphia Navy Yard Annex",
          f"- **Source:** G Force RFQ email thread (2026-11-02 / 2026-11-04); Att. A drawings (179 sheets); Att. B specs (1,550 pp)",
          f"- **Shred date:** {TODAY}",
          "- **Shredded by:** Claude (AI draft) for J. Tapscott review",
          "",
          "## 1. Key Facts", "", md_table(["Item", "Value"], facts, [22, 78]), "",
          "## 2. Client Correspondence Log", "",
          md_table(["Date", "From / To", "Content", "Significance"], D.CORRESPONDENCE, [10, 22, 45, 23]), "",
          "## 3. Project Scope (Spec 01 11 00 §1.1.1)", "",
          "- Item a: Replace building substation and electrical distribution, including panels.",
          "- Item b: **HVAC and dust exhaust system upgrades, mezzanine pattern shop** (BFA scope driver).",
          "- Item c: Crane access ladders and platforms.",
          "- Item d: Replace lighting system and controls.",
          "- Item e: Renovate mezzanine lunch/break room, including new HVAC (AHU-M01 / CU-M01).",
          "- Item f: Renovate mezzanine pattern shop office, including new HVAC.",
          "- Item g: Build out 2nd floor printing lab / offices / restrooms (AHU-201, RF-201, humidifier).",
          "- Item h: Mezzanine floor infill framing and deck.",
          "- Building stays occupied; NFPC remains operational throughout construction (01 14 00).",
          "",
          "## 4. Technical Requirements Driving BFA Scope", "",
          md_table(["ID", "Source", "Requirement", "BFA Role", "Trade", "Deliverable"], D.REQUIREMENTS, [7, 16, 45, 14, 10, 8]), "",
          "## 5. Red Flags / Compliance Risks", "",
          md_table(["ID", "Severity", "Topic", "Finding / Action"], D.RED_FLAGS, [6, 6, 14, 74]), "",
          "## 6. Clarification Questions for G Force", "",
          md_table(["#", "Question", "Sent?", "Answer"], [(q, t, "☐", "") for q, t in D.QUESTIONS], [4, 66, 6, 24]), "",
          "## 7. Relevant Drawings", "", md_table(["Sheet(s)", "Content"], D.MECH_SHEETS), "",
          "## 8. Relevant Specification Sections", "", md_table(["Section", "Title", "Relevance"], D.SPEC_SECTIONS), "",
          "## 9. Format & Submission Requirements", "",
          md_table(["Requirement", "Value"], [
              ("Format", "Not specified. Recommend a 2-4 page fee proposal letter with scope, fee table, assumptions, and exclusions."),
              ("Submission", f"Email to {P['client_poc'].split(',')[0]} (ebruno@fbsginc.com)"),
              ("Due", P["proposal_due"]),
              ("Validity", "90 days (recommended)")]), "",
          "## 10. Addendum Change Log", "", md_table(["Addendum", "Date", "Change", "Impact"], [("None received", "-", "-", "Ask Q10")]), ""]
    md_path.write_text("\n".join(md), encoding="utf-8")

    wb = Workbook()
    ws = wb.active
    ws.title = "Key_Facts"
    title(ws, "B592 RFP Shred: Key Facts", f"Shred date {TODAY} | AI draft for J. Tapscott review")
    table(ws, 4, ["Item", "Value"], facts, [26, 110])
    ws2 = wb.create_sheet("Correspondence")
    title(ws2, "Client Correspondence Log")
    table(ws2, 4, ["Date", "From / To", "Content", "Significance"], D.CORRESPONDENCE, [12, 34, 70, 40])
    ws3 = wb.create_sheet("Requirements")
    title(ws3, "Technical Requirements Driving BFA Scope", "Status column is for your tracking.")
    table(ws3, 4, ["ID", "Source", "Requirement", "BFA Role", "Trade", "Deliverable", "Status"],
          [r + ("Open",) for r in D.REQUIREMENTS], [9, 30, 80, 26, 18, 14, 10])
    ws4 = wb.create_sheet("Red_Flags")
    title(ws4, "Red Flags / Compliance Risks")
    table(ws4, 4, ["ID", "Severity", "Topic", "Finding / Action", "Owner", "Resolved?"],
          [r + ("J. Tapscott", "No") for r in D.RED_FLAGS], [7, 9, 20, 100, 14, 10])
    ws5 = wb.create_sheet("Questions")
    title(ws5, "Clarification Questions for G Force")
    table(ws5, 4, ["#", "Question", "Sent (date)", "Answer"], [(q, t, "", "") for q, t in D.QUESTIONS], [6, 100, 12, 50])
    ws6 = wb.create_sheet("Drawings")
    title(ws6, "Relevant Drawings")
    table(ws6, 4, ["Sheet(s)", "Content"], D.MECH_SHEETS, [26, 90])
    ws7 = wb.create_sheet("Spec_Sections")
    title(ws7, "Relevant Specification Sections")
    table(ws7, 4, ["Section", "Title", "Relevance"], D.SPEC_SECTIONS, [18, 40, 70])
    for wsx in wb.worksheets:
        wsx.sheet_view.showGridLines = False
        wsx.page_setup.orientation = "landscape"
    wb.save(xlsx_path)


# ------------------------------------------------------------------ schedule + ICS
def _dow(d):
    return dt.date.fromisoformat(d).strftime("%a")


def build_schedule(md_path: Path, xlsx_path: Path):
    rows = []
    for d, t, dur, ttl, own, note, ics in D.SCHEDULE:
        rows.append((d, _dow(d), t or "All day", f"{dur} min" if dur else "-", ttl, own, note, "Yes" if ics else "No"))
    md = ["# B592 Proposal Schedule", "",
          f"- **Opportunity:** {D.PROJECT['title']}: Delegated Design Peer Review (sub to G Force)",
          "- **RFQ received:** 2026-11-02",
          f"- **Quote due:** {D.PROJECT['proposal_due']}",
          "- **Proposal manager:** J. Tapscott",
          "- **Time zone:** America/New_York (ET)",
          "",
          "## Pre-Submission Milestones", "",
          md_table(["Date", "Day", "Time (ET)", "Duration", "Milestone", "Owner", "Notes", "In Outlook ICS"], rows, [10, 5, 7, 7, 28, 12, 25, 6]), "",
          "## Post-Award Delivery Milestones (relative; dates set at NTP)", "",
          md_table(["Timing", "Milestone", "Owner"], D.POST_AWARD), "",
          "## Working Assumptions", "",
          "- G Force did not state a due date. The quote target of 2026-11-13 12:00 ET is ASSUMED, based on a typical 1-week sub-quote lead before a GC's NAVFAC due date.",
          "- 2026-11-12 in the email thread is the B408 (N4008526R0275) due date, a project G Force declined. It does not apply here.",
          "- Government review durations come from 01 33 00 §1.11: 20 WD for CO approval, 30 WD for Government FP engineer review. HVAC controls get an extra 10 WD.",
          "- Site visits need 15 CD notice and SECNAV 5512/1 badging submitted at least 2 weeks ahead (01 14 00).",
          "", "## Contingency Notes", "",
          "- If G Force sets an earlier due date, compress: internal review plus PE validation on 11-10, approval on 11-11, submit on 11-12.",
          "- Veterans Day (11-11) is a federal holiday; Government offices are closed.",
          "- Outlook import: open `output/published/calendar/B592_Proposal_Schedule_All_vNN.ics` (all events) or the single-event files.", ""]
    md_path.write_text("\n".join(md), encoding="utf-8")

    wb = Workbook()
    ws = wb.active
    ws.title = "Pre_Submission"
    title(ws, "B592 Proposal Schedule: Pre-Submission", "Times ET. 'In Outlook ICS' = included in calendar files.")
    table(ws, 4, ["Date", "Day", "Time (ET)", "Duration", "Milestone", "Owner", "Notes", "In Outlook ICS"], rows,
          [12, 6, 10, 10, 50, 16, 60, 12])
    ws2 = wb.create_sheet("Post_Award")
    title(ws2, "Post-Award Delivery Milestones (relative)")
    table(ws2, 4, ["Timing", "Milestone", "Owner"], D.POST_AWARD, [22, 80, 16])
    for wsx in wb.worksheets:
        wsx.sheet_view.showGridLines = False
        wsx.page_setup.orientation = "landscape"
    wb.save(xlsx_path)


VTZ = """BEGIN:VTIMEZONE
TZID:America/New_York
BEGIN:DAYLIGHT
TZOFFSETFROM:-0500
TZOFFSETTO:-0400
TZNAME:EDT
DTSTART:19700308T020000
RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=2SU
END:DAYLIGHT
BEGIN:STANDARD
TZOFFSETFROM:-0400
TZOFFSETTO:-0500
TZNAME:EST
DTSTART:19701101T020000
RRULE:FREQ=YEARLY;BYMONTH=11;BYDAY=1SU
END:STANDARD
END:VTIMEZONE"""


def _esc(s):
    return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def _fold(line):
    b = line.encode("utf-8")
    if len(b) <= 75:
        return line
    out, cur = [], b""
    for ch in line:
        e = ch.encode("utf-8")
        if len(cur) + len(e) > (75 if not out else 74):
            out.append(cur.decode("utf-8"))
            cur = b""
        cur += e
    out.append(cur.decode("utf-8"))
    return "\r\n ".join(out)


def _vevent(d, t, dur, ttl, own, note):
    stamp = "20261109T120000Z"
    slug = re.sub(r"[^a-z0-9]+", "-", ttl.lower()).strip("-")[:40]
    uid = f"b592-{d.replace('-', '')}-{slug}@bfa-proposal-27003b"
    lines = ["BEGIN:VEVENT", f"UID:{uid}", f"DTSTAMP:{stamp}"]
    day = dt.date.fromisoformat(d)
    if t is None:
        lines += [f"DTSTART;VALUE=DATE:{day:%Y%m%d}", f"DTEND;VALUE=DATE:{day + dt.timedelta(days=1):%Y%m%d}",
                  "TRANSP:TRANSPARENT"]
        alarm = "-PT15H"  # 9:00 AM previous day for all-day items
    else:
        h, m = map(int, t.split(":"))
        start = dt.datetime.combine(day, dt.time(h, m))
        end = start + dt.timedelta(minutes=dur or 30)
        lines += [f"DTSTART;TZID=America/New_York:{start:%Y%m%dT%H%M%S}",
                  f"DTEND;TZID=America/New_York:{end:%Y%m%dT%H%M%S}", "TRANSP:OPAQUE"]
        alarm = "-PT1D" if "Submit" in ttl else "-PT15M"
    lines += [f"SUMMARY:{_esc('[B592] ' + ttl)}",
              f"DESCRIPTION:{_esc(f'Owner: {own}. {note} Project: B592 Dust Collection Delegated Design Peer Review (G Force / NAVFAC Philadelphia Navy Yard).')}",
              "LOCATION:Teams / BFA office", "CATEGORIES:Proposal,B592", "STATUS:CONFIRMED",
              "BEGIN:VALARM", "ACTION:DISPLAY", f"DESCRIPTION:{_esc(ttl)}", f"TRIGGER:{alarm}", "END:VALARM",
              "END:VEVENT"]
    return lines


def _vcal(events):
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//BFA//Proposal Engine B592//EN", "CALSCALE:GREGORIAN",
             "METHOD:PUBLISH", "X-WR-CALNAME:B592 Proposal Schedule", "X-WR-TIMEZONE:America/New_York"]
    lines += VTZ.split("\n")
    for e in events:
        lines += e
    lines.append("END:VCALENDAR")
    return "\r\n".join(_fold(x) for x in lines) + "\r\n"


def build_ics(folder: Path):
    folder.mkdir(parents=True, exist_ok=True)
    evs = [s for s in D.SCHEDULE if s[6]]
    allev = [_vevent(*s[:6]) for s in evs]
    (folder / "B592_Proposal_Schedule_All.ics").write_bytes(_vcal(allev).encode("utf-8"))
    names = []
    for s in evs:
        slug = re.sub(r"[^A-Za-z0-9]+", "_", s[3]).strip("_")[:40]
        name = f"B592_EVT_{s[0].replace('-', '')}_{slug}.ics"
        (folder / name).write_bytes(_vcal([_vevent(*s[:6])]).encode("utf-8"))
        names.append(name)
    return names


# ------------------------------------------------------------------ fee summary md
def build_fee_md(md_path: Path):
    rows, opts = fee_numbers()
    lab = sum(r["labor"] for r in rows)
    exp = sum(r["exp"] for r in rows)
    hrs = sum(r["hours"] for r in rows)
    trade_l = {t: sum(r["by_trade"][t] for r in rows) for t in D.TRADES}
    trade_h = {t: sum(r["hrs_trade"][t] for r in rows) for t in D.TRADES}
    md = ["# B592 Fee Summary: Delegated Design Peer Review (DRAFT)", "",
          "> Labor rates are ASSUMED placeholders. Source of truth: `B592_Fee_Estimate` workbook (formula-driven).", "",
          "## Base Fee", "",
          md_table(["Item", "Amount"], [("Labor (lump sum)", f"${lab:,.0f}"), ("Reimbursable expenses (at cost)", f"${exp:,.0f}"),
                                        ("**BASE FEE TOTAL**", f"**${lab + exp:,.0f}**"), ("Total hours", f"{hrs:,.0f}"),
                                        ("Blended rate", f"${lab / hrs:,.2f}/hr")]), "",
          "## Fee by Trade", "",
          md_table(["Trade", "Hours", "Labor ($)", "% of Labor"],
                   [(t, f"{trade_h[t]:,.0f}", f"${trade_l[t]:,.0f}", f"{trade_l[t] / lab:.1%}") for t in D.TRADES]
                   + [("**Total**", f"**{hrs:,.0f}**", f"**${lab:,.0f}**", "100.0%")]), "",
          "## Fee by Deliverable", "",
          md_table(["ID", "Phase", "Deliverable", "Submittal", "Hours", "Labor", "Expenses", "Total"],
                   [(r["id"], r["phase"], r["name"], r["sub"], f"{r['hours']:,.0f}", f"${r['labor']:,.0f}",
                     f"${r['exp']:,.0f}" if r["exp"] else "-", f"${r['total']:,.0f}") for r in rows]
                   + [("", "", "**TOTAL**", "", f"**{hrs:,.0f}**", f"**${lab:,.0f}**", f"**${exp:,.0f}**",
                       f"**${lab + exp:,.0f}**")], [5, 5, 45, 14, 7, 8, 8, 8]), "",
          "## Labor by Deliverable and Trade", "",
          md_table(["ID"] + D.TRADES + ["Labor"],
                   [(r["id"],) + tuple(f"${r['by_trade'][t]:,.0f}" if r["by_trade"][t] else "-" for t in D.TRADES)
                    + (f"${r['labor']:,.0f}",) for r in rows]
                   + [("**TOTAL**",) + tuple(f"**${trade_l[t]:,.0f}**" for t in D.TRADES) + (f"**${lab:,.0f}**",)]), "",
          "Phases: " + "; ".join(D.PHASES.values()), "",
          "## Labor Rates (ASSUMED)", "",
          md_table(["Code", "Labor Category", "Trade", "Rate"], [(c, r, t, f"${v}/hr") for c, r, t, v in D.ROLES]), "",
          "## Expenses", "",
          md_table(["Item", "Qty", "Unit", "Unit Cost", "Per Trip"], [(i, q, u, f"${c:,.2f}", f"${q * c:,.2f}") for i, q, u, c, _ in D.TRIP_ITEMS]
                   + [("**Per-trip subtotal**", "", "", "", f"**${TRIP_COST:,.2f}**")]),
          "",
          f"Base: {sum(r['trips'] for r in rows)} trips, {sum(r['pkgs'] for r in rows)} sealed packages at ${D.PRINT_SHIP_UNIT:,.0f} each.", "",
          "## Optional Services (not in base)", "",
          md_table(["ID", "Option", "Hours", "Total"], [(o["id"], o["name"], f"{o['hours']:,.0f}", f"${o['total']:,.0f}") for o in opts]), ""]
    md_path.write_text("\n".join(md), encoding="utf-8")
    return dict(labor=lab, exp=exp, total=lab + exp, hours=hrs, trade_l=trade_l, trade_h=trade_h, rows=rows, opts=opts)


def main():
    require_proposal_or_engine_root(REPO_ROOT)
    BUILD.mkdir(parents=True, exist_ok=True)
    build_shred(BUILD / "B592_RFP_Shred.md", BUILD / "B592_RFP_Shred.xlsx")
    build_schedule(BUILD / "B592_Proposal_Schedule.md", BUILD / "B592_Proposal_Schedule.xlsx")
    ics = build_ics(BUILD / "calendar")
    build_fee_xlsx(BUILD / "B592_Fee_Estimate.xlsx")
    n = build_fee_md(BUILD / "B592_Fee_Summary.md")
    print(f"built: shred, schedule, {len(ics) + 1} ics, fee xlsx/md")
    print(f"BASE labor ${n['labor']:,.0f} | expenses ${n['exp']:,.2f} | total ${n['total']:,.2f} | hours {n['hours']}")
    for t in D.TRADES:
        print(f"  {t:16s} {n['trade_h'][t]:5.0f} h  ${n['trade_l'][t]:,.0f}")
    for o in n["opts"]:
        print(f"  {o['id']} {o['hours']:4.0f} h  ${o['total']:,.2f}")


if __name__ == "__main__":
    main()
