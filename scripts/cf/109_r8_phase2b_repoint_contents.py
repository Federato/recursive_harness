"""R-8 Phase 2b-ii -- migrate `CALC - Contents Rating` to one column per contents record.

After this, Contents column k (C..AP, k = 1..40) is the k-th row of the
`IN - Schedule` CONTENTS block, not "item k" of `IN - Location`. Each record resolves
its occupancy and building explicitly and reads building-level values through the
parent (`r8_contents_translate.py` holds the rule and its reasoning).

What this script changes, in order:

1. **Moves R-3's Source/Check columns M:N to AQ:AR.** They sat inside the M..AP range
   reserved for records -- the handoff missed it. Moved with Excel's own Cut so
   references follow; the two whole-column COUNTIFs on `OUT - Diagnostics` do not
   follow a partial-column cut and are rewritten explicitly.
2. **`IN - Schedule` CONTENTS gets column L = ParentBldg**, resolved through the
   occupancy record. That is the join key the TOTAL LIMIT roll-up needs.
3. **Contents rows 112-116: per-record keys** (ID, Active, OccIdx, ParentCol).
4. **Contents rows 118+: per-record copies of the 50 record-level CoreScratchpad
   rows**, including the Contents half of the R-5 wind/hail split (rows 60, 205).
5. **Contents rows 1-110 rewritten for all 40 columns** from the column-C template.
   The four premium rows are gated on Active.
6. **CoreScratchpad row 138 TOTAL LIMIT** = building Limit + SUMIFS over active
   contents records of that building + Special Class (C215, unchanged).
7. **CoreScratchpad rows 60 and 205, Building half of the R-5 split** -> read the
   Building wind/hail election (row 96) instead of the policy one (row 75).
8. **`CALC - BI Rating` row 74** read Contents column-by-column for a factor Contents
   itself copied from `CALC - Bldg Rating` row 111. Repointed at the source, because
   Contents columns no longer mean buildings.

Gate 1: every premium unchanged, every Contents value in C1:L110 unchanged, TOTAL
LIMIT unchanged -- and, two-sided, Contents moves when a contents input moves on each
active item, and the wind/hail split is live in both directions. Aborts without
saving on any failure. Structural state re-verified after save/close/reopen.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import r8_contents_translate as T                                   # noqa: E402

TARGET = Path(r"F:\Spreadsheet_Rater\CF\CFRater1.02.xlsb")
FORBIDDEN = "cfrater1.01.xlsb"
PREMIUMS = ["OUT_Prem_Building", "OUT_Prem_Contents", "OUT_Prem_BI",
            "OUT_Prem_SCBuilding", "OUT_Prem_SCBI", "OUT_Prem_Total"]
TOTALS = {31, 59, 82, 110}
PREM_ROWS = [30, 58, 81, 109]
OLD_COLS = range(3, 13)                       # C..L
SRC_COL, CHK_COL = 43, 44                     # AQ, AR
ACTIVE_ITEMS = range(3, 7)                    # C..F carry the four active risks


def excel_pids() -> dict[int, str]:
    out = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "Get-Process EXCEL -ErrorAction SilentlyContinue | "
         "ForEach-Object { \"$($_.Id)`t$($_.MainWindowTitle)\" }"],
        capture_output=True, text=True).stdout
    res = {}
    for line in out.splitlines():
        if line.strip():
            pid, _, title = line.partition("\t")
            res[int(pid)] = title
    return res


def reap_orphans(before: set[int]) -> None:
    for pid, title in excel_pids().items():
        if pid not in before and not title.strip():
            subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
            print(f"  reaped orphan Excel PID {pid}")


def prem(wb) -> dict:
    return {p: wb.Names(p).RefersToRange.Value for p in PREMIUMS}


def show(tag, p):
    print(f"  {tag:<34} " + "  ".join(f"{k.split('_')[-1]}={v}" for k, v in p.items()))


def block(ws, r0, c0, r1, c1):
    v = ws.Range(ws.Cells(r0, c0), ws.Cells(r1, c1)).Value
    return [list(r) for r in v]


class Gate(Exception):
    pass


def migrate(app, wb) -> None:
    cr = wb.Worksheets(T.CR)
    cs = wb.Worksheets(T.CS)
    sc = wb.Worksheets(T.SC)
    il = wb.Worksheets(T.IL)
    bi = wb.Worksheets("CALC - BI Rating")
    dg = wb.Worksheets("OUT - Diagnostics")

    app.CalculateFull()
    base = prem(wb)
    show("baseline", base)
    base_cr = block(cr, 1, 3, 110, 12)
    base_138 = block(cs, 138, 3, 138, 12)
    base_br = block(wb.Worksheets(T.BR), 1, 3, 113, 12)

    # ---- preconditions -------------------------------------------------------
    if cr.Cells(1, 13).Value != "Source" or cr.Cells(1, 14).Value != "Check":
        raise Gate(f"M1/N1 are {cr.Cells(1,13).Value!r}/{cr.Cells(1,14).Value!r}, "
                   "not Source/Check")
    if cr.Application.WorksheetFunction.CountA(cr.Range("AQ1:AR200")) != 0:
        raise Gate("AQ:AR not empty")
    if cr.Application.WorksheetFunction.CountA(cr.Range("A111:AR200")) != 0:
        raise Gate("Contents rows 111-200 not empty -- append target occupied")
    if sc.Cells(133, 12).Value not in (None, ""):
        raise Gate("IN - Schedule L133 not empty")
    if str(cr.Cells(31, 3).Formula).replace(" ", "") != "=SUM(C30:AP30)":
        raise Gate("Phase 2b-i roll-up not in place")
    for c in OLD_COLS:
        f = str(bi.Cells(74, c).Formula)
        if f != f"='{T.CR}'!{T.colname(c)}108":
            raise Gate(f"BI row 74 col {c} is {f!r}")
        if str(cr.Cells(108, c).Formula) != f"='{T.BR}'!{T.colname(c)}111":
            raise Gate(f"Contents row 108 col {c} no longer = Bldg Rating row 111")

    # ---- 1. move Source/Check ------------------------------------------------
    cr.Range("M1:N110").Cut(cr.Range("AQ1:AR110"))
    for cell, old, new in (("B6", "N:N", "AR:AR"), ("C6", "M:M", "AQ:AQ")):
        f = str(dg.Range(cell).Formula)
        nf = f.replace(f"'{T.CR}'!{old}", f"'{T.CR}'!{new}")
        if nf == f:
            raise Gate(f"Diagnostics {cell} did not contain {old}: {f!r}")
        dg.Range(cell).Formula = nf
    if cr.Range("AQ1").Value != "Source" or cr.Range("AR1").Value != "Check":
        raise Gate("Source/Check did not land in AQ/AR")
    print("  1. Source/Check moved M:N -> AQ:AR; Diagnostics B6/C6 repointed")

    # ---- 2. IN - Schedule CONTENTS.ParentBldg --------------------------------
    sc.Cells(133, 12).Value = "ParentBldg"
    s0 = T.SCHED_CONT_FIRST
    sc.Range(sc.Cells(s0, 12), sc.Cells(s0 + T.RECORDS - 1, 12)).Formula = \
        tuple((T.sched_parent_bldg(s0 + i),) for i in range(T.RECORDS))
    print("  2. IN - Schedule L133:L173 ParentBldg")

    # ---- 3/4. key rows and CoreScratchpad copies -----------------------------
    cs_f = {r: str(cs.Cells(r, 3).Formula) for r in range(1, 281)}
    cs_f = {r: f for r, f in cs_f.items() if f.startswith("=")}
    template = {r: str(cr.Cells(r, 3).Formula) for r in range(1, 111)}
    seeds = set()
    for r, f in template.items():
        if f.startswith("=") and r not in TOTALS:
            seeds |= {row for sh, _, row, _ in T.refs(f, T.CR) if sh == T.CS}
    rec = T.record_level_rows(cs_f, seeds)
    tr = T.Translator(rec)
    print(f"  record-level CoreScratchpad rows: {len(rec)}")

    cr.Cells(T.KEY_HDR, 2).Value = "R-8 RECORD KEYS (one column per IN - Schedule CONTENTS row)"
    for row, lab in ((T.ROW_ID, "ContentsID"), (T.ROW_ACTIVE, "Active"),
                     (T.ROW_OCC, "OccIdx"), (T.ROW_PC, "ParentCol")):
        cr.Cells(row, 2).Value = lab
        cr.Cells(row, SRC_COL).Value = "R-8 key: IN - Schedule"
        cr.Range(cr.Cells(row, 3), cr.Cells(row, T.LAST_COL)).Formula = \
            (tuple(T.key_formulas(k)[row] for k in range(1, T.RECORDS + 1)),)
    cr.Cells(T.COPY_HDR, 2).Value = ("R-8 PER-RECORD COPIES of CoreScratchpad rows that "
                                     "read contents/occupancy inputs (col A = source row)")
    for r in tr.rec_rows:
        row = tr.copy_row[r]
        f = T.CS_OVERRIDES.get(r, cs_f[r])
        cr.Cells(row, 1).Value = f"CS{r}"
        cr.Cells(row, 2).Value = str(cs.Cells(r, 2).Value or "")
        cr.Cells(row, SRC_COL).Value = (f"R-8 copy of CALC - CoreScratchpad row {r}"
                                        + (" (R-5 split: Contents wind/hail)"
                                           if r in T.CS_OVERRIDES else ""))
        cr.Range(cr.Cells(row, 3), cr.Cells(row, T.LAST_COL)).Formula = \
            (tuple(tr.translate(f, T.CS, k) for k in range(1, T.RECORDS + 1)),)
    print(f"  3/4. key rows {T.ROW_ID}-{T.ROW_PC}, copies rows "
          f"{T.COPY_FIRST}-{max(tr.copy_row.values())}")

    # ---- 5. rewrite rows 1-110 ------------------------------------------------
    n = 0
    for r, f in template.items():
        if r in TOTALS:
            continue
        if f.startswith("="):
            fs = [tr.translate(f, T.CR, k) for k in range(1, T.RECORDS + 1)]
            if r in PREM_ROWS:
                fs = [f"=IF({T.colname(T.FIRST_COL + k)}${T.ROW_ACTIVE}<>\"Yes\",0,{x[1:]})"
                      for k, x in enumerate(fs)]
            cr.Range(cr.Cells(r, 3), cr.Cells(r, T.LAST_COL)).Formula = (tuple(fs),)
            n += 1
        else:
            vals = [cr.Cells(r, c).Value for c in OLD_COLS]
            if vals == [float(i) for i in range(1, 11)]:
                cr.Range(cr.Cells(r, 3), cr.Cells(r, T.LAST_COL)).Value = \
                    (tuple(float(i) for i in range(1, T.RECORDS + 1)),)
    print(f"  5. {n} Contents rows rewritten across C..AP")

    # ---- 6/7. CoreScratchpad TOTAL LIMIT and the Building half of R-5 ---------
    for c in OLD_COLS:
        L = T.colname(c)
        cs.Cells(138, c).Formula = T.total_limit(L)
        for r, t in T.CS_BUILDING_SPLIT.items():
            cs.Cells(r, c).Formula = t.format(c=L)
        # ---- 8. BI row 74 at its real source
        bi.Cells(74, c).Formula = f"='{T.BR}'!{L}111"
    print("  6/7/8. CS138 roll-up, CS60/205 -> Building election, BI row 74 repointed")

    # ---- Gate 1: unchanged ------------------------------------------------------
    app.CalculateFull()
    after = prem(wb)
    show("after migration", after)
    if after != base:
        raise Gate("premiums moved")
    diffs = [(r + 1, c + 3, base_cr[r][c], v)
             for r, row in enumerate(block(cr, 1, 3, 110, 12))
             for c, v in enumerate(row) if v != base_cr[r][c]]
    if diffs:
        for d in diffs[:15]:
            print("   DIFF row", d[0], "col", T.colname(d[1]), d[2], "->", d[3])
        raise Gate(f"{len(diffs)} Contents cells in C1:L110 changed value")
    if block(cs, 138, 3, 138, 12) != base_138:
        raise Gate(f"TOTAL LIMIT changed: {base_138} -> {block(cs,138,3,138,12)}")
    if block(wb.Worksheets(T.BR), 1, 3, 113, 12) != base_br:
        raise Gate("a Bldg Rating value changed")
    errs = [(r, T.colname(c)) for r in PREM_ROWS + sorted(TOTALS)
            for c in range(3, T.LAST_COL + 1)
            if isinstance(cr.Cells(r, c).Value, int) and cr.Cells(r, c).Value < 0]
    if errs:
        raise Gate(f"error values in premium rows: {errs[:10]}")
    print("  GATE 1a: premiums, all 1,100 Contents values, TOTAL LIMIT and every "
          "Bldg Rating value unchanged")

    # ---- Gate 1b: two-sided, every active item --------------------------------
    def poke(cells, value):
        saved = [(cell, str(cell.Formula)) for cell in cells]
        for cell in cells:
            cell.Value = value(cell) if callable(value) else value
        app.CalculateFull()
        return saved

    def restore(saved):
        for cell, f in saved:
            cell.Formula = f

    def col_prem(c):
        return sum(cr.Cells(r, c).Value for r in PREM_ROWS)

    for c in ACTIVE_ITEMS:
        before = col_prem(c)
        saved = poke([il.Cells(45, c)], lambda cell: cell.Value + 100000)
        moved, p = col_prem(c), prem(wb)
        restore(saved)
        if moved == before or p["OUT_Prem_Contents"] == base["OUT_Prem_Contents"]:
            raise Gate(f"item {T.colname(c)}: Contents did not respond to its limit")
        print(f"  GATE 1b item {T.colname(c)}: +100k contents limit -> record premium "
              f"{before} -> {moved}")

    saved = poke([il.Cells(97, c) for c in ACTIVE_ITEMS], "Yes")
    p = prem(wb)
    restore(saved)
    show("Contents wind/hail = Yes", p)
    if p["OUT_Prem_Contents"] == base["OUT_Prem_Contents"] or \
            p["OUT_Prem_Building"] != base["OUT_Prem_Building"]:
        raise Gate("Contents wind/hail election not isolated to Contents")

    saved = poke([il.Cells(96, c) for c in ACTIVE_ITEMS], "Yes")
    p = prem(wb)
    restore(saved)
    show("Building wind/hail = Yes", p)
    if p["OUT_Prem_Building"] == base["OUT_Prem_Building"] or \
            p["OUT_Prem_Contents"] != base["OUT_Prem_Contents"]:
        raise Gate("Building wind/hail election not isolated to Building")
    print("  GATE 1b: R-5 split live -- each election moves only its own coverage")

    app.CalculateFull()
    if prem(wb) != base:
        raise Gate("did not restore after the responsiveness checks")
    show("restored", prem(wb))


def main() -> int:
    if TARGET.name.lower() == FORBIDDEN:
        sys.exit("ABORT: refusing to write to the live rater.")
    pre = excel_pids()
    if pre:
        titled = {p: t for p, t in pre.items() if t.strip()}
        sys.exit(f"ABORT: Excel running {pre}"
                 + (" -- the user has it open; not touching it." if titled else ""))

    import win32com.client
    ok = False
    app = win32com.client.DispatchEx("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    app.EnableEvents = False
    wb = None
    try:
        wb = app.Workbooks.Open(str(TARGET), UpdateLinks=0)
        app.Calculation = -4135
        base = None
        try:
            migrate(app, wb)
            ok = True
        except Gate as e:
            print(f"\n  GATE FAILED: {e}\n  NOT saving.")
        if ok:
            app.Calculation = -4105
            app.CalculateFull()
            wb.Save()
            print("\n  saved.")
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
        reap_orphans(set(pre))
    if not ok:
        return 1

    print("  reopening to verify the persisted state")
    app = win32com.client.DispatchEx("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    wb = None
    try:
        wb = app.Workbooks.Open(str(TARGET), UpdateLinks=0, ReadOnly=True)
        app.Calculation = -4135
        app.CalculateFull()
        final = prem(wb)
        show("after reopen", final)
        cr = wb.Worksheets(T.CR)
        stale = [nm.Name for nm in wb.Names if "#REF" in str(nm.RefersTo)]
        checks = {
            "AQ1=Source": cr.Range("AQ1").Value == "Source",
            "AR1=Check": cr.Range("AR1").Value == "Check",
            "Diag B6->AR": "AR:AR" in str(wb.Worksheets("OUT - Diagnostics").Range("B6").Formula),
            "Diag C6->AQ": "AQ:AQ" in str(wb.Worksheets("OUT - Diagnostics").Range("C6").Formula),
            "ParentCol D=2": cr.Cells(T.ROW_PC, 4).Value == 2,
            "no #REF names": not stale,
            "premiums": final == {"OUT_Prem_Building": 7183, "OUT_Prem_Contents": 8022,
                                  "OUT_Prem_BI": 2699, "OUT_Prem_SCBuilding": 1434,
                                  "OUT_Prem_SCBI": 406, "OUT_Prem_Total": 19744},
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
        reap_orphans(set(pre))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
