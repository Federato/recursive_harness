"""R-8 Gate 2 follow-up -- apply Fix A and Fix B to `CALC - Contents Rating`.

Both were proven against live ISO in memory by `110_r8_gate2_multi_record.py`
(247 / 231 / 116, exact). Approved 2026-09-22.

**Fix A -- LOI on the occupancy total.** ISO looks up all four Personal Property LOI
factors on `OccupTotalLOIToUse`: the total PP limit under the occupancy class, not the
record's own limit. A new key row 117 `OccTotalLOI` holds that total per record; the
per-record copies of the three LOI chains (CoreScratchpad 131-137, 144-154, 156-166)
read it instead of the record's own limit. With one record per occupancy -- every risk
the workbook holds today -- the two are equal. **Gate: no premium moves.**

**Fix B -- BGI adjusted-rate rounding order (pre-existing, not R-8).** Row 17 was
`ROUND(COL x Coins x LOI, 3)`. ISO rounds `COL x Coins` first:
`ROUND(ROUND(COL x Coins, 3) x LOI, 3)`. **This moves the Contents premium by design.**
Gate: only Contents (and Total) move, and only through the BGI rows.

Aborts without saving on any gate failure. Re-verified after save/close/reopen.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import r8_contents_translate as T                                   # noqa: E402

TARGET = Path(r"C:\Projects\Spreadsheet_Rater\CF\CFRater1.02.xlsb")
FORBIDDEN = "cfrater1.01.xlsb"
PREMIUMS = ["OUT_Prem_Building", "OUT_Prem_Contents", "OUT_Prem_BI",
            "OUT_Prem_SCBuilding", "OUT_Prem_SCBI", "OUT_Prem_Total"]
ROW_OCCTOT = 117
LOI_CHAIN = set(range(131, 138)) | set(range(144, 155)) | set(range(156, 167))
BGI_ROWS = set(range(17, 31))          # row 17 feeds 20 -> 23 -> 30
COLS = range(T.FIRST_COL, T.LAST_COL + 1)


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


def prem(wb) -> dict:
    return {p: float(wb.Names(p).RefersToRange.Value) for p in PREMIUMS}


def show(tag, p):
    print(f"  {tag:<26} " + "  ".join(f"{k.split('_')[-1]}={v:g}" for k, v in p.items()))


def grid(ws, r0, r1):
    return [list(r) for r in ws.Range(ws.Cells(r0, 3), ws.Cells(r1, T.LAST_COL)).Value]


class Gate(Exception):
    pass


def apply(app, wb) -> dict:
    cr = wb.Worksheets(T.CR)
    app.CalculateFull()
    base = prem(wb)
    show("baseline", base)

    if cr.Cells(ROW_OCCTOT, 2).Value not in (None, ""):
        raise Gate(f"row {ROW_OCCTOT} not empty: {cr.Cells(ROW_OCCTOT, 2).Value!r}")
    if str(cr.Cells(17, 3).Formula).replace(" ", "") != "=ROUND(C14*C15*C16,3)":
        raise Gate(f"row 17 is {cr.Cells(17, 3).Formula!r}, not the expected single ROUND")

    # ---- Fix A ----------------------------------------------------------------
    s0, s1 = T.SCHED_CONT_FIRST, T.SCHED_CONT_FIRST + T.RECORDS - 1
    cr.Cells(ROW_OCCTOT, 2).Value = "OccTotalLOI"
    cr.Cells(ROW_OCCTOT, 43).Value = ("R-8 key: total PP limit under this record's occupancy "
                                      "(ISO OccupTotalLOIToUse)")
    cr.Range(cr.Cells(ROW_OCCTOT, 3), cr.Cells(ROW_OCCTOT, T.LAST_COL)).Formula = (tuple(
        f"=SUMIFS('{T.SC}'!$E${s0}:$E${s1},'{T.SC}'!$B${s0}:$B${s1},"
        f"'{T.SC}'!$B${s0 + k - 1},'{T.SC}'!$C${s0}:$C${s1},\"Yes\")"
        for k in range(1, T.RECORDS + 1)),)
    n = 0
    for r in range(T.COPY_FIRST, T.COPY_FIRST + 60):
        lab = str(cr.Cells(r, 1).Value or "")
        if not (lab.startswith("CS") and int(lab[2:]) in LOI_CHAIN):
            continue
        fs = []
        for k, c in enumerate(COLS, start=1):
            f = str(cr.Cells(r, c).Formula)
            own = f"'{T.SC}'!$E${s0 + k - 1}"
            if own in f:
                f = f.replace(own, f"{T.colname(c)}${ROW_OCCTOT}")
                n += 1
            fs.append(f)
        cr.Range(cr.Cells(r, 3), cr.Cells(r, T.LAST_COL)).Formula = (tuple(fs),)
    if n != 6 * T.RECORDS:
        raise Gate(f"expected 6 limit references per record in the LOI chains, rewrote {n}")
    app.CalculateFull()
    after_a = prem(wb)
    show("after Fix A", after_a)
    if after_a != base:
        raise Gate("Fix A moved a premium, but every occupancy has one record today")
    print(f"  Fix A: {n} cells now read row {ROW_OCCTOT}; premiums unchanged")

    # ---- Fix B ----------------------------------------------------------------
    before_cr = grid(cr, 1, 110)
    cr.Range(cr.Cells(17, 3), cr.Cells(17, T.LAST_COL)).Formula = (tuple(
        f"=ROUND(ROUND({L}14*{L}15,3)*{L}16,3)" for L in map(T.colname, COLS)),)
    app.CalculateFull()
    after_b = prem(wb)
    show("after Fix B", after_b)
    for k in ("OUT_Prem_Building", "OUT_Prem_BI", "OUT_Prem_SCBuilding", "OUT_Prem_SCBI"):
        if after_b[k] != base[k]:
            raise Gate(f"Fix B moved {k}; it should touch Contents only")
    stray = sorted({r + 1 for r, row in enumerate(grid(cr, 1, 110))
                    for c, v in enumerate(row) if v != before_cr[r][c]} - BGI_ROWS - {31})
    if stray:
        raise Gate(f"Fix B changed Contents rows outside the BGI chain: {stray}")
    print("  Fix B: per item BGI premium " + "  ".join(
        f"{T.colname(c)} {before_cr[29][c - 3]:g}->{cr.Cells(30, c).Value:g}"
        for c in range(3, 7)))
    print(f"  Contents {base['OUT_Prem_Contents']:g} -> {after_b['OUT_Prem_Contents']:g}")
    return after_b


def main() -> int:
    if TARGET.name.lower() == FORBIDDEN:
        sys.exit("ABORT: refusing to write to the live rater.")
    pre = excel_pids()
    if pre:
        sys.exit(f"ABORT: Excel running {pre}")

    import win32com.client
    ok, expected = False, None
    app = win32com.client.DispatchEx("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    app.EnableEvents = False
    wb = None
    try:
        wb = app.Workbooks.Open(str(TARGET), UpdateLinks=0)
        app.Calculation = -4135
        try:
            expected = apply(app, wb)
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
        reap_orphans(set(pre))
    if not ok:
        return 1

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
        ok = (final == expected
              and cr.Cells(ROW_OCCTOT, 2).Value == "OccTotalLOI"
              and "ROUND(ROUND(" in str(cr.Cells(17, 42).Formula)
              and not [n.Name for n in wb.Names if "#REF" in str(n.RefersTo)])
        print("  reopen check:", "ok" if ok else "FAIL")
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
