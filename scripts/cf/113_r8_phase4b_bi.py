"""R-8 Phase 4b -- Business Income to one column per BI record.

`CALC - BI Rating` column k becomes row k of the Schedule BUSINESS INCOME block
(row 176+k). Its own inputs come from that row; building and location values come
through its parent building (ParentCol); the 20 CoreScratchpad rows that read
BI-level inputs (186-209) get per-record copies on the BI sheet. Same pattern as
Contents (Phase 2b-ii), through the generalised `r8_child_translate.py`.

In order:
1. BI R-3 Source/Check M:N -> AQ:AR; `OUT - Diagnostics` B7/C7 repointed.
2. BI key rows 79-81 (BIID, Active, ParentCol); copies from row 83.
3. BI rows rewritten for C..AP; premium rows gated on Active; roll-ups widened.

BI still borrows the building's computed rate (rows 3-13, 29-35) -- that is ISO's
own structure -- and so still carries backlog W-4 (BI follows the Building wind/hail
election). Preserved, not fixed.

Gate: premiums and every BI / Building / Contents / Special Class value unchanged.
Two-sided, in memory: each active BI record moves with its own Schedule limit; a
location-level change reaches BI through the parent chain; an 11th BI record entered
only on the Schedule rates. Aborts without saving on failure; re-verified on reopen.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import r8_building_translate as B                                  # noqa: E402
import r8_child_translate as C                                     # noqa: E402
from r8_contents_translate import colname                          # noqa: E402
from importlib import import_module                                # noqa: E402

p4a = import_module("112_r8_phase4a_building")
Gate, prem, show, grid, diff_rows, as_input, calc = (p4a.Gate, p4a.prem, p4a.show, p4a.grid,
                                                     p4a.diff_rows, p4a.as_input, p4a.calc)

BI = "CALC - BI Rating"
BI_COL = {11: "D", 36: "E", 37: "F", 38: "G", 47: "H", 48: "I", 70: "J", 39: "K",
          40: "L", 41: "M", 98: "N", 101: "O", 104: "P"}
BI_HDR = {"A": "ID", "B": "ParentID", "C": "Active", "D": "CovType", "H": "Limit",
          "J": "Coinsurance", "N": "WindHailExcl", "P": "TheftExcl"}
S_HDR, S_FIRST = 176, 177
KEY_HDR, ROW_ID, ROW_ACTIVE, ROW_PC, COPY_FIRST = 78, 79, 80, 81, 83
ROLLUPS = {26: 25, 46: 45, 60: 59, 76: 75}
PREM_ROWS = list(ROLLUPS.values())
AP = colname(B.LAST_COL)


def keys(k: int) -> dict[int, str]:
    R = S_FIRST + k - 1
    b0, b1 = B.BLDG_ROWS
    return {
        ROW_ID: f"=IF('{B.SC}'!$A${R}=\"\",\"\",'{B.SC}'!$A${R})",
        ROW_ACTIVE: f"=IF('{B.SC}'!$C${R}=\"Yes\",\"Yes\",\"No\")",
        ROW_PC: f"=IFERROR(MATCH('{B.SC}'!$B${R},'{B.SC}'!$A${b0}:$A${b1},0),1)",
    }


def migrate(app, wb) -> dict:
    bi, cs, sc, dg = (wb.Worksheets(s) for s in (BI, B.CS, B.SC, p4a.DG))
    calc(app)
    base = prem(wb)
    show("baseline", base)
    snap = {"BI": grid(bi, 76, 12), "BR": grid(wb.Worksheets(B.BR), 113, 42),
            "CR": grid(wb.Worksheets(p4a.CR), 168, 42), "SC": grid(wb.Worksheets(p4a.SCC), 158, 12),
            "CS": grid(cs, 285, 42)}

    wf = app.WorksheetFunction
    if bi.Range("M1").Value != "Source" or bi.Range("N1").Value != "Check":
        raise Gate(f"BI M1/N1 are {bi.Range('M1').Value!r}/{bi.Range('N1').Value!r}")
    for rng in ("AQ1:AR200", "A77:AR200", "O1:AP76"):
        if wf.CountA(bi.Range(rng)) != 0:
            raise Gate(f"BI!{rng} is not empty")
    for col, name in BI_HDR.items():
        if sc.Range(f"{col}{S_HDR}").Value != name:
            raise Gate(f"Schedule {col}{S_HDR} is {sc.Range(f'{col}{S_HDR}').Value!r}, expected {name!r}")

    # 1. Source/Check
    bi.Range("M1:N76").Cut(bi.Range("AQ1:AR76"))
    for cell, old, new in (("B7", "N:N", "AR:AR"), ("C7", "M:M", "AQ:AQ")):
        f = str(dg.Range(cell).Formula)
        nf = f.replace(f"'{BI}'!{old}", f"'{BI}'!{new}")
        if nf == f:
            raise Gate(f"Diagnostics {cell} did not reference {old}")
        dg.Range(cell).Formula = nf
    print("  1. BI Source/Check -> AQ:AR; Diagnostics B7/C7 repointed")

    # 2. keys + copies
    cs_f = {}
    for r, (f,) in enumerate(cs.Range("C1:C280").Formula, start=1):
        if isinstance(f, str) and f.startswith("="):
            cs_f[r] = f
    tpl = {}
    for r, (f,) in enumerate(bi.Range("C1:C76").Formula, start=1):
        if isinstance(f, str) and f.startswith("="):
            tpl[r] = f
    seeds = set()
    for r, f in tpl.items():
        if r not in ROLLUPS:
            seeds |= {row for sh, _, row, _ in C_refs(f)}
    rec = C.record_level_rows(cs_f, seeds, set(BI_COL))
    copy = {r: COPY_FIRST + i for i, r in enumerate(sorted(rec))}
    tr = C.ChildTranslator(BI, BI_COL, S_FIRST, ROW_PC, copy)

    bi.Range(f"B{KEY_HDR}").Value = "R-8 BI RECORD KEYS (column k = IN - Schedule BUSINESS INCOME row k)"
    for row, lab in ((ROW_ID, "BIID"), (ROW_ACTIVE, "Active"), (ROW_PC, "ParentCol")):
        bi.Range(f"B{row}").Value = lab
        bi.Cells(row, 43).Value = "R-8 key: IN - Schedule"
        bi.Range(bi.Cells(row, 3), bi.Cells(row, B.LAST_COL)).Formula = \
            (tuple(keys(k)[row] for k in range(1, B.RECORDS + 1)),)
    for r, row in copy.items():
        bi.Cells(row, 1).Value = f"CS{r}"
        bi.Cells(row, 2).Value = str(cs.Cells(r, 2).Value or "")
        bi.Cells(row, 43).Value = f"R-8 copy of CALC - CoreScratchpad row {r}"
        bi.Range(bi.Cells(row, 3), bi.Cells(row, B.LAST_COL)).Formula = \
            (tuple(tr.translate(cs_f[r], B.CS, k) for k in range(1, B.RECORDS + 1)),)
    print(f"  2. keys rows {ROW_ID}-{ROW_PC}; {len(copy)} CoreScratchpad copies at rows "
          f"{COPY_FIRST}-{max(copy.values())}")

    # 3. BI rows
    n = 0
    for r in range(1, 77):
        if r in ROLLUPS:
            f = str(bi.Cells(r, 3).Formula)
            nf = f.replace(f"SUM(C{ROLLUPS[r]}:L{ROLLUPS[r]})", f"SUM(C{ROLLUPS[r]}:{AP}{ROLLUPS[r]})")
            if nf == f:
                raise Gate(f"roll-up row {r} is {f!r}")
            bi.Cells(r, 3).Formula = nf
        elif r in tpl:
            fs = [tr.translate(tpl[r], BI, k) for k in range(1, B.RECORDS + 1)]
            if r in PREM_ROWS:
                fs = [f"=IF({colname(B.FIRST_COL + i)}${ROW_ACTIVE}<>\"Yes\",0,{x[1:]})"
                      for i, x in enumerate(fs)]
            bi.Range(bi.Cells(r, 3), bi.Cells(r, B.LAST_COL)).Formula = (tuple(fs),)
            n += 1
        else:
            vals = [bi.Cells(r, c).Value for c in range(3, 13)]
            if vals == [float(i) for i in range(1, 11)]:
                bi.Range(bi.Cells(r, 3), bi.Cells(r, B.LAST_COL)).Value = \
                    (tuple(float(i) for i in range(1, B.RECORDS + 1)),)
    print(f"  3. {n} BI rows -> C..{AP}; roll-ups widened; premium rows gated")

    # Gate 1a
    calc(app)
    after = prem(wb)
    show("after migration", after)
    if after != base:
        raise Gate("premiums moved")
    now = {"BI": grid(bi, 76, 12), "BR": grid(wb.Worksheets(B.BR), 113, 42),
           "CR": grid(wb.Worksheets(p4a.CR), 168, 42), "SC": grid(wb.Worksheets(p4a.SCC), 158, 12),
           "CS": grid(cs, 285, 42)}
    for k in snap:
        d = diff_rows(snap[k], now[k])
        if d:
            raise Gate(f"{k} values changed on rows {d[:20]}")
    print("  GATE 1a: premiums and every value on BI, Building, Contents, Special Class, "
          "CoreScratchpad unchanged")

    # Gate 1b
    def col_prem(c):
        return sum(float(bi.Cells(r, c).Value) for r in PREM_ROWS)

    def poke_restore(cell, value, c):
        before = col_prem(c)
        saved = cell.Formula
        cell.Value = value(cell) if callable(value) else value
        app.CalculateFull()
        moved = col_prem(c)
        cell.Formula = saved
        app.CalculateFull()
        return before, moved

    for k in range(1, 5):
        c = B.FIRST_COL + k - 1
        b, m = poke_restore(sc.Range(f"H{S_FIRST + k - 1}"), lambda x: x.Value + 100000, c)
        if b == m:
            raise Gate(f"BI record {k} did not respond to its Schedule limit")
        print(f"  GATE 1b BI record {k}: Schedule Limit +100k -> {b:g} -> {m:g}")
    b, m = poke_restore(sc.Range(f"F{B.LOC_ROWS[0] + 1}"), "'8", 4)
    if b == m:
        raise Gate("BI record 2 did not respond to its location's ProtClass")
    print(f"  GATE 1b location 2 ProtClass -> 8 reaches BI record 2: {b:g} -> {m:g}")

    src, dst = S_FIRST + 1, S_FIRST + 10
    vals = sc.Range(f"A{src}:P{src}").Value[0]
    target = sc.Range(f"A{dst}:P{dst}")
    saved = target.Formula
    t_before = prem(wb)["OUT_Prem_BI"]
    for i, v in enumerate(vals):
        sc.Cells(dst, 1 + i).Value = as_input(f"{vals[0]}b" if i == 0 else v)
    app.CalculateFull()
    p11, p2, t_after = col_prem(B.FIRST_COL + 10), col_prem(4), prem(wb)["OUT_Prem_BI"]
    pc = bi.Cells(ROW_PC, B.FIRST_COL + 10).Value
    target.Formula = saved
    app.CalculateFull()
    print(f"  GATE 1b BI record 11 (Schedule only, copy of record 2): ParentCol {pc}, "
          f"premium {p11:g} vs {p2:g}; BI total {t_before:g} -> {t_after:g}")
    if pc != 2 or p11 != p2 or t_after != t_before + p11:
        raise Gate("the 11th BI record did not rate like its twin")
    if prem(wb) != base:
        raise Gate("did not restore")
    show("restored", prem(wb))
    return base


def C_refs(f):
    """(sheet, col, row, is_range) for CoreScratchpad references in a BI formula."""
    for lit, chunk in C._strip_strings(f):
        if lit:
            continue
        for m in C.REF.finditer(chunk):
            sh = (m.group("sheet") or "").rstrip("!").strip("'")
            if sh == B.CS:
                yield sh, m.group("col"), int(m.group("row")), bool(m.group("rng"))


def main() -> int:
    if p4a.TARGET.name.lower() == p4a.FORBIDDEN:
        sys.exit("ABORT: refusing to write to the live rater.")
    pre = p4a.excel_pids()
    if pre:
        sys.exit(f"ABORT: Excel running {pre}")
    import win32com.client
    ok, base = False, None
    app = win32com.client.DispatchEx("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    app.EnableEvents = False
    wb = None
    try:
        wb = app.Workbooks.Open(str(p4a.TARGET), UpdateLinks=0)
        app.Calculation = -4135
        try:
            base = migrate(app, wb)
            ok = True
        except Gate as e:
            print(f"\n  GATE FAILED: {e}\n  NOT saving.")
        if ok:
            app.Calculation = -4105
            app.CalculateFull()
            wb.Save()
            print("  saved.")
        wb.Close(SaveChanges=False)
        wb = None
    finally:
        try:
            if wb is not None:
                wb.Close(SaveChanges=False)
        except Exception:                                   # noqa: BLE001
            pass
        app.Quit()
        del app
        p4a.reap_orphans(set(pre))
    if not ok:
        return 1

    app = win32com.client.DispatchEx("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    wb = None
    try:
        wb = app.Workbooks.Open(str(p4a.TARGET), UpdateLinks=0, ReadOnly=True)
        app.Calculation = -4135
        app.CalculateFull()
        final = prem(wb)
        show("after reopen", final)
        bi = wb.Worksheets(BI)
        checks = {
            "premiums": final == base,
            "AQ1=Source": bi.Range("AQ1").Value == "Source",
            "Diag B7->AR": "AR:AR" in str(wb.Worksheets(p4a.DG).Range("B7").Formula),
            "ParentCol D=2": bi.Range(f"D{ROW_PC}").Value == 2,
            "roll-up to AP": f":{AP}25" in str(bi.Range("C26").Formula),
            "no #REF names": not [x.Name for x in wb.Names if "#REF" in str(x.RefersTo)],
        }
        for k, v in checks.items():
            print(f"    {'ok ' if v else 'FAIL'} {k}")
        ok = all(checks.values())
        wb.Close(SaveChanges=False)
        wb = None
    finally:
        try:
            if wb is not None:
                wb.Close(SaveChanges=False)
        except Exception:                                   # noqa: BLE001
            pass
        app.Quit()
        del app
        p4a.reap_orphans(set(pre))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
