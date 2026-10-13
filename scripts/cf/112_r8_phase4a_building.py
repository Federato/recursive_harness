"""R-8 Phase 4a -- Building reads IN - Schedule and holds 40 buildings.

After this, `CALC - Bldg Rating` column k and the 110 CoreScratchpad rows Building
depends on are **row k of the Schedule BUILDING block**, reading building fields from
that row and location fields through a LocIdx key. Both widen from 10 columns to 40.
The translation rule and its reasoning are in `r8_building_translate.py`.

In order:
1. `CALC - Bldg Rating` R-3 Source/Check M:N -> AQ:AR (Cut, so references follow);
   `OUT - Diagnostics` B5/C5 whole-column COUNTIFs repointed by hand.
2. `IN - Schedule` BUILDING column AI `ConstrDesc` (derived; `IN - Location` row 61).
3. CoreScratchpad key rows 283-285: BldgID, Active, LocIdx.
4. The 110 CoreScratchpad rows in Building's dependency closure rewritten for C..AP.
   Everything else on CoreScratchpad (BI, Special Class, IN - Location derivations,
   legacy Contents rows) is untouched and stays 10 columns wide.
5. `CALC - Bldg Rating` rewritten for C..AP; premium rows gated on Active; roll-ups
   widened.
6. `CALC - Contents Rating`: INDEX ranges over CoreScratchpad / Bldg Rating widened
   to AP; its building- and location-level `IN - Location` reads moved to the Schedule.

Found by the survey and standardised here: CoreScratchpad rows 9-12 (sub-standard
condition keys) held a different formula in D..L than in C -- the drag-filled copies
had drifted onto the wrong input rows. Column C's form is the one consistent with
row 8 and with the table's key. No premium moves today (sub-standard is "No" on
items 2-10).

Gate: every premium unchanged; every CoreScratchpad and Bldg Rating value in C..L,
every Contents value, every BI and Special Class value unchanged. Two-sided, in
memory: Building moves when a Schedule building input or location input changes
on each active building, and an 11th building entered only on the Schedule rates.
Aborts without saving on any failure; re-verified after reopen.
"""
from __future__ import annotations

import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import r8_building_translate as B                                  # noqa: E402
from r8_contents_translate import colname                          # noqa: E402

TARGET = Path(r"F:\Spreadsheet_Rater\CF\CFRater1.02.xlsb")
FORBIDDEN = "cfrater1.01.xlsb"
PREMIUMS = ["OUT_Prem_Building", "OUT_Prem_Contents", "OUT_Prem_BI",
            "OUT_Prem_SCBuilding", "OUT_Prem_SCBI", "OUT_Prem_Total"]
CR, BI, SCC, DG = ("CALC - Contents Rating", "CALC - BI Rating", "CALC - Special Class",
                   "OUT - Diagnostics")
ROLLUPS = {33: 32, 63: 62, 87: 86, 113: 112}
PREM_ROWS = list(ROLLUPS.values())
STANDARDISED = {9, 10, 11, 12}
AP = colname(B.LAST_COL)


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
    print(f"  {tag:<34} " + "  ".join(f"{k.split('_')[-1]}={v:g}" for k, v in p.items()))


def grid(ws, r1, c1, r0=1, c0=3):
    return [list(r) for r in ws.Range(ws.Cells(r0, c0), ws.Cells(r1, c1)).Value]


def diff_rows(a, b, r0=1):
    return sorted({i + r0 for i, (x, y) in enumerate(zip(a, b)) if x != y})


def as_input(v):
    """Write text as text -- Excel coerces '0951', '1,000', '2 - 2' otherwise."""
    return f"'{v}" if isinstance(v, str) else v


class Gate(Exception):
    pass


def calc(app) -> float:
    t = time.perf_counter()
    app.CalculateFull()
    return time.perf_counter() - t


def migrate(app, wb) -> dict:
    cs, br, cr, sc, il = (wb.Worksheets(s) for s in (B.CS, B.BR, CR, B.SC, B.IL))
    dg = wb.Worksheets(DG)
    t0 = calc(app)
    base = prem(wb)
    show("baseline", base)
    snap = {
        "CS": grid(cs, 280, 12), "BR": grid(br, 113, 12), "CR": grid(cr, 168, 42),
        "BI": grid(wb.Worksheets(BI), 76, 12), "SC": grid(wb.Worksheets(SCC), 158, 12),
    }

    # ---- preconditions ---------------------------------------------------------
    wf = app.WorksheetFunction
    if br.Range("M1").Value != "Source" or br.Range("N1").Value != "Check":
        raise Gate("Bldg Rating M1/N1 are not Source/Check")
    for ws, rng in ((br, "AQ1:AR200"), (cs, f"M1:{AP}300"), (cs, "A281:L300"),
                    (sc, "AI47:AI87")):
        if wf.CountA(ws.Range(rng)) != 0:
            raise Gate(f"{ws.Name}!{rng} is not empty")
    for hdr_row, want in ((47, B.BLD_HEADERS), (4, B.LOC_HEADERS)):
        for col, name in want.items():
            if sc.Range(f"{col}{hdr_row}").Value != name:
                raise Gate(f"Schedule {col}{hdr_row} is {sc.Range(f'{col}{hdr_row}').Value!r}, "
                           f"expected {name!r}")

    # ---- 1. Source/Check ----------------------------------------------------------
    br.Range("M1:N113").Cut(br.Range("AQ1:AR113"))
    for cell, old, new in (("B5", "N:N", "AR:AR"), ("C5", "M:M", "AQ:AQ")):
        f = str(dg.Range(cell).Formula)
        nf = f.replace(f"'{B.BR}'!{old}", f"'{B.BR}'!{new}")
        if nf == f:
            raise Gate(f"Diagnostics {cell} did not reference {old}: {f!r}")
        dg.Range(cell).Formula = nf
    print("  1. Bldg Rating Source/Check -> AQ:AR; Diagnostics B5/C5 repointed")

    # ---- 2. ConstrDesc ---------------------------------------------------------------
    il61 = str(il.Range("C61").Formula)
    sc.Range("AI47").Value = "ConstrDesc"
    b0, b1 = B.BLDG_ROWS
    sc.Range(f"AI{b0}:AI{b1}").Formula = tuple((B.constr_desc(il61, r),) for r in range(b0, b1 + 1))
    print("  2. IN - Schedule AI47:AI87 ConstrDesc")

    # ---- 3/4. keys and the CoreScratchpad closure -----------------------------------
    cs.Range(f"B{B.KEY_HDR}").Value = "R-8 BUILDING RECORD KEYS (column k = IN - Schedule BUILDING row k)"
    for row, lab in ((B.ROW_ID, "BldgID"), (B.ROW_ACTIVE, "Active"), (B.ROW_LOC, "LocIdx")):
        cs.Range(f"B{row}").Value = lab
        cs.Range(cs.Cells(row, 3), cs.Cells(row, B.LAST_COL)).Formula = \
            (tuple(B.keys(k)[row] for k in range(1, B.RECORDS + 1)),)

    tpl = {}
    for ws, sh, last in ((cs, B.CS, 280), (br, B.BR, 113)):
        col = ws.Range(ws.Cells(1, 3), ws.Cells(last, 3)).Formula
        for r, (f,) in enumerate(col, start=1):
            if isinstance(f, str) and f.startswith("="):
                tpl[(sh, r)] = f
    seeds = [n for n in tpl if n[0] == B.BR and n[1] not in ROLLUPS]
    cl = B.closure(tpl, seeds)
    cs_rows = sorted(r for s, r in cl if s == B.CS)
    tr = B.Translator()
    for r in cs_rows:
        cs.Range(cs.Cells(r, 3), cs.Cells(r, B.LAST_COL)).Formula = \
            (tuple(tr.translate(tpl[(B.CS, r)], B.CS, k) for k in range(1, B.RECORDS + 1)),)
    print(f"  3/4. keys rows {B.ROW_ID}-{B.ROW_LOC}; {len(cs_rows)} CoreScratchpad rows -> C..{AP}")

    # ---- 5. Bldg Rating -----------------------------------------------------------------
    n = 0
    for r in range(1, 114):
        if r in ROLLUPS:
            f = str(br.Cells(r, 3).Formula)
            nf = re.sub(rf"SUM\(C{ROLLUPS[r]}:L{ROLLUPS[r]}\)", f"SUM(C{ROLLUPS[r]}:{AP}{ROLLUPS[r]})", f)
            if nf == f:
                raise Gate(f"roll-up row {r} is {f!r}")
            br.Cells(r, 3).Formula = nf
            continue
        if (B.BR, r) in tpl:
            fs = [tr.translate(tpl[(B.BR, r)], B.BR, k) for k in range(1, B.RECORDS + 1)]
            if r in PREM_ROWS:
                fs = [f"=IF('{B.CS}'!{colname(B.FIRST_COL + i)}${B.ROW_ACTIVE}<>\"Yes\",0,{x[1:]})"
                      for i, x in enumerate(fs)]
            br.Range(br.Cells(r, 3), br.Cells(r, B.LAST_COL)).Formula = (tuple(fs),)
            n += 1
        else:
            vals = [br.Cells(r, c).Value for c in range(3, 13)]
            if vals == [float(i) for i in range(1, 11)]:
                br.Range(br.Cells(r, 3), br.Cells(r, B.LAST_COL)).Value = \
                    (tuple(float(i) for i in range(1, B.RECORDS + 1)),)
    print(f"  5. {n} Bldg Rating rows -> C..{AP}; roll-ups widened; premium rows gated")

    # ---- 6. Contents ----------------------------------------------------------------------
    loc_key = f"INDEX('{B.CS}'!$C${B.ROW_LOC}:${AP}${B.ROW_LOC},1,{{X}}$116)"
    kept, moved = set(), 0
    for r in range(1, 169):
        rng = cr.Range(cr.Cells(r, 3), cr.Cells(r, B.LAST_COL))
        row_f = list(rng.Formula[0])
        new_f = []
        for i, f in enumerate(row_f):
            X = colname(B.FIRST_COL + i)
            if not (isinstance(f, str) and f.startswith("=")):
                new_f.append(f)
                continue
            g = re.sub(rf"'({re.escape(B.CS)}|{re.escape(B.BR)})'!\$C\$(\d+):\$L\$(\d+)",
                       rf"'\1'!$C$\2:${AP}$\3", f)

            def il_sub(m, X=X):
                row = int(m.group(1))
                if row in B.BLD_COL:
                    c = B.BLD_COL[row]
                    return f"INDEX('{B.SC}'!${c}${b0}:${c}${b1},{X}$116)"
                if row in B.LOC_COL:
                    c = B.LOC_COL[row]
                    return (f"INDEX('{B.SC}'!${c}${B.LOC_ROWS[0]}:${c}${B.LOC_ROWS[1]},"
                            + loc_key.format(X=X) + ")")
                kept.add(row)
                return m.group(0)
            g = re.sub(rf"INDEX\('IN - Location'!\$C\$(\d+):\$L\$\d+,1,{X}\$116\)", il_sub, g)
            moved += g != f
            new_f.append(g)
        rng.Formula = (tuple(new_f),)
    print(f"  6. Contents: {moved} cells repointed; still on IN - Location (no Schedule "
          f"home yet): rows {sorted(kept)}")

    # ---- Gate: unchanged -------------------------------------------------------------------
    t1 = calc(app)
    after = prem(wb)
    show("after migration", after)
    print(f"  recalc {t0:.1f}s -> {t1:.1f}s")
    if after != base:
        raise Gate("premiums moved")
    now = {"CS": grid(cs, 280, 12), "BR": grid(br, 113, 12), "CR": grid(cr, 168, 42),
           "BI": grid(wb.Worksheets(BI), 76, 12), "SC": grid(wb.Worksheets(SCC), 158, 12)}
    for k in snap:
        d = diff_rows(snap[k], now[k])
        if k == "CS":
            d = [r for r in d if r not in STANDARDISED]
        if d:
            raise Gate(f"{k} values changed on rows {d[:20]}")
    std = diff_rows(snap["CS"], now["CS"])
    print(f"  GATE 1a: premiums and every value on 5 sheets unchanged"
          f"{'' if not std else f' (standardised rows changed value: {std})'}")
    errs = [(r, colname(c)) for r in PREM_ROWS for c in range(3, B.LAST_COL + 1)
            if isinstance(br.Cells(r, c).Value, int) and br.Cells(r, c).Value < 0]
    if errs:
        raise Gate(f"error values in Building premium rows: {errs[:8]}")

    # ---- Gate: moving, in memory -------------------------------------------------------------
    def col_prem(c):
        return sum(float(br.Cells(r, c).Value) for r in PREM_ROWS)

    def poke(cells, fn):
        saved = [(c, c.Formula) for c in cells]
        for c in cells:
            c.Value = fn(c)
        app.CalculateFull()
        return saved

    def restore(saved):
        for c, f in saved:
            c.Formula = f
        app.CalculateFull()

    for k in range(1, 5):
        c, row = B.FIRST_COL + k - 1, b0 + k - 1
        before = col_prem(c)
        s = poke([sc.Range(f"N{row}")], lambda x: x.Value + 100000)
        moved_to = col_prem(c)
        restore(s)
        if moved_to == before:
            raise Gate(f"building {k} did not respond to its Schedule limit")
        print(f"  GATE 1b building {k}: Schedule Limit +100k -> {before:g} -> {moved_to:g}")

    loc_row = B.LOC_ROWS[0] + 1                     # location 2
    before = col_prem(4)
    s = poke([sc.Range(f"F{loc_row}")], lambda x: "'8")
    moved_to = col_prem(4)
    restore(s)
    if moved_to == before:
        raise Gate("building 2 did not respond to its location's Schedule ProtClass")
    print(f"  GATE 1b location 2: ProtClass -> 8 moves building 2 {before:g} -> {moved_to:g}")

    # An 11th building, entered ONLY on the Schedule: a copy of building 2.
    src, dst = b0 + 1, b0 + 10
    vals = sc.Range(f"A{src}:AH{src}").Value[0]
    target = sc.Range(f"A{dst}:AH{dst}")
    saved = target.Formula
    b_before = prem(wb)["OUT_Prem_Building"]
    for i, v in enumerate(vals):
        sc.Cells(dst, 1 + i).Value = as_input("2 - 2" if i == 0 else v)
    app.CalculateFull()
    m = B.FIRST_COL + 10
    p11, p2 = col_prem(m), col_prem(4)
    b_after = prem(wb)["OUT_Prem_Building"]
    lr = [cs.Cells(B.ROW_LOC, m).Value, cs.Cells(B.ROW_ACTIVE, m).Value]
    rows_diff = [r for r in range(1, 113) if br.Cells(r, m).Value != br.Cells(r, 4).Value]
    target.Formula = saved
    app.CalculateFull()
    print(f"  GATE 1b building 11 (Schedule only, copy of building 2): LocIdx/Active {lr}, "
          f"premium {p11:g} vs building 2 {p2:g}; Building total {b_before:g} -> {b_after:g}")
    print(f"           rows where it differs from building 2: {rows_diff}")
    if not p11 > 0 or b_after <= b_before or lr != [2.0, "Yes"]:
        raise Gate("the 11th building did not rate")
    if prem(wb) != base:
        raise Gate("did not restore after the responsiveness checks")
    show("restored", prem(wb))
    return base


def main() -> int:
    if TARGET.name.lower() == FORBIDDEN:
        sys.exit("ABORT: refusing to write to the live rater.")
    pre = excel_pids()
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
        wb = app.Workbooks.Open(str(TARGET), UpdateLinks=0)
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
        br = wb.Worksheets(B.BR)
        checks = {
            "premiums": final == base,
            "AQ1=Source": br.Range("AQ1").Value == "Source",
            "Diag B5->AR": "AR:AR" in str(wb.Worksheets(DG).Range("B5").Formula),
            "LocIdx D=2": wb.Worksheets(B.CS).Range(f"D{B.ROW_LOC}").Value == 2,
            "ConstrDesc": wb.Worksheets(B.SC).Range("AI49").Value
                          == wb.Worksheets(B.IL).Range("D61").Value,
            "roll-up to AP": f":{AP}32" in str(br.Range("C33").Formula),
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
        reap_orphans(set(pre))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
