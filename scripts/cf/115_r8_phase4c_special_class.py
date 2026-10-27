"""R-8 Phase 4c -- Special Class and SC Business Income to Schedule records.

`CALC - Special Class` rows 1-87: column k = Schedule SPECIAL CLASS row 219+k.
Rows 88-158: column k = Schedule SC BUSINESS INCOME row 262+k. See
`r8_sc_translate.py` for the rule, and for what replaces the old "building k" reads.

**This one changes a premium, by decision (backlog W-8, 2026-09-22).** The Group II
base rate now keys on the Special Class item's OWN construction symbol, as ISO does
(filed rule, and confirmed live by `114_r8_sc_symbol_probe.py`: symbol B -> 0.028,
AB -> 0.024). Item 1's own symbol is B; the rater used building 1's AB.

Also: the Schedule's SC BI Limit and both Active flags mirrored `IN - Special Class`
row 42, which nothing prices on. They now mirror row 20, the SC BI limit the rater
actually uses. No premium effect.

Gate, because a premium is meant to move:
  * Building, Contents, BI and every value on their sheets + CoreScratchpad unchanged.
  * **Isolation proof:** with the item's symbol set to building 1's "AB" in memory,
    every value of the active item (column C, rows 1-158) and both SC premiums return
    EXACTLY to today's. So the symbol is the only behavioural change. Inactive slots
    must price zero.
  * Moving: SC and SCBI records respond to their own Schedule limits and to their
    location's state; an 11th SC item and an 11th SC BI record entered only on the
    Schedule rate like their twins.
Aborts without saving on any failure; re-verified after reopen.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import r8_building_translate as B                                  # noqa: E402
import r8_sc_translate as S                                        # noqa: E402
from r8_contents_translate import colname                          # noqa: E402
from importlib import import_module                                # noqa: E402

p4a = import_module("112_r8_phase4a_building")
Gate, prem, show, grid, diff_rows, as_input, calc = (p4a.Gate, p4a.prem, p4a.show, p4a.grid,
                                                     p4a.diff_rows, p4a.as_input, p4a.calc)
AP = colname(B.LAST_COL)
SC_PREM, BI_PREM = [22, 46, 65, 86], [105, 126, 140, 157]
ROLLUPS = {23: 22, 47: 46, 66: 65, 87: 86, 106: 105, 127: 126, 141: 140, 158: 157}
UNMOVED = ["OUT_Prem_Building", "OUT_Prem_Contents", "OUT_Prem_BI"]


def col_c(g):
    """The active item's column. Inactive slots now resolve their own (empty) location
    instead of borrowing building k, so their intermediates legitimately differ; their
    premiums are checked to be zero instead."""
    return [[row[0]] for row in g]


def migrate(app, wb) -> dict:
    scc, cs, sc, isc, dg = (wb.Worksheets(s) for s in (S.SCC, S.CS, S.SC, S.ISC, p4a.DG))
    calc(app)
    base = prem(wb)
    show("baseline", base)
    snap = {"SCC": grid(scc, 158, 12), "BR": grid(wb.Worksheets(B.BR), 113, 42),
            "CR": grid(wb.Worksheets(p4a.CR), 168, 42), "BI": grid(wb.Worksheets(p4a.BI), 102, 42),
            "CS": grid(cs, 285, 42)}

    # ---- preconditions ------------------------------------------------------------
    wf = app.WorksheetFunction
    if scc.Range("M1").Value != "Source" or scc.Range("N1").Value != "Check":
        raise Gate(f"SC M1/N1 are {scc.Range('M1').Value!r}/{scc.Range('N1').Value!r}")
    for rng in ("AQ1:AR300", "A159:AR300", "O1:AP158"):
        if wf.CountA(scc.Range(rng)) != 0:
            raise Gate(f"CALC - Special Class!{rng} is not empty")
    for hdr, want in ((S.SC_HDR, S.SC_HEADERS), (S.SCBI_HDR, S.SCBI_HEADERS)):
        for col, name in want.items():
            if sc.Range(f"{col}{hdr}").Value != name:
                raise Gate(f"Schedule {col}{hdr} is {sc.Range(f'{col}{hdr}').Value!r}, expected {name!r}")
    if isc.Range("C31").Value != "B" or str(cs.Range("C59").Value) != "FLInlandAB":
        raise Gate("item 1 symbol / building 1 BGII key are not the surveyed B / FLInlandAB")

    # ---- 0. Schedule mirrors of the SC BI limit: row 42 -> row 20 -----------------------
    n0 = 0
    for rows, cols in ((range(S.SC_ROWS[0], S.SC_ROWS[0] + 10), ("C",)),
                       (range(S.SCBI_ROWS[0], S.SCBI_ROWS[0] + 10), ("C", "H"))):
        for r in rows:
            for c in cols:
                f = str(sc.Range(f"{c}{r}").Formula)
                nf = f.replace("'IN - Special Class'!$C$42:$L$42", "'IN - Special Class'!$C$20:$L$20")
                if nf == f:
                    raise Gate(f"Schedule {c}{r} does not read row 42: {f!r}")
                sc.Range(f"{c}{r}").Formula = nf
                n0 += 1
    print(f"  0. {n0} Schedule cells now mirror IN - Special Class row 20 (priced) not 42 (unread)")

    # ---- 1. Source/Check ---------------------------------------------------------------
    scc.Range("M1:N158").Cut(scc.Range("AQ1:AR158"))
    hits = 0
    for cell in dg.UsedRange:
        f = str(cell.Formula)
        nf = f.replace(f"'{S.SCC}'!N:N", f"'{S.SCC}'!AR:AR").replace(f"'{S.SCC}'!M:M", f"'{S.SCC}'!AQ:AQ")
        if nf != f:
            cell.Formula = nf
            hits += 1
    if hits != 2:
        raise Gate(f"expected 2 Diagnostics formulas on Special Class M:M/N:N, found {hits}")
    print("  1. Special Class Source/Check -> AQ:AR; 2 Diagnostics formulas repointed")

    # ---- 2. keys and copies ------------------------------------------------------------
    cs_f = {r: f for r, (f,) in enumerate(cs.Range("C1:C280").Formula, start=1)
            if isinstance(f, str) and f.startswith("=")}
    tpl = {r: f for r, (f,) in enumerate(scc.Range("C1:C158").Formula, start=1)
           if isinstance(f, str) and f.startswith("=")}
    seeds = {"SC": set(), "SCBI": set()}
    for r, f in tpl.items():
        if r not in ROLLUPS:
            seeds["SC" if r < S.SPLIT else "SCBI"] |= S.cs_deps(f)
    maps, row = {}, S.COPY_FIRST
    for ctx in ("SC", "SCBI"):
        maps[ctx] = {}
        for r in S.copy_set(cs_f, seeds[ctx]):
            maps[ctx][r] = row
            row += 1
        row += 1
    tr = S.SCTranslator(maps["SC"], maps["SCBI"])

    scc.Range(f"B{S.SC_KEY_HDR}").Value = "R-8 SPECIAL CLASS KEYS (rows 1-87: column k = Schedule SPECIAL CLASS row k)"
    scc.Range(f"B{S.BI_KEY_HDR}").Value = "R-8 SC BI KEYS (rows 88-158: column k = Schedule SC BUSINESS INCOME row k)"
    for r, lab in ((S.SC_ID, "SCID"), (S.SC_ACTIVE, "Active"), (S.SC_LOC, "LocIdx"),
                   (S.BI_ID, "SCBIID"), (S.BI_ACTIVE, "Active"), (S.BI_PARENT, "SCParentCol")):
        scc.Range(f"B{r}").Value = lab
        scc.Cells(r, 43).Value = "R-8 key: IN - Schedule"
        scc.Range(scc.Cells(r, 3), scc.Cells(r, B.LAST_COL)).Formula = \
            (tuple(S.keys(k)[r] for k in range(1, B.RECORDS + 1)),)
    scc.Range(f"B{S.COPY_HDR}").Value = "R-8 PER-RECORD COPIES of CoreScratchpad Special Class rows (col A = source row)"
    for ctx, m in maps.items():
        for r, dst in m.items():
            scc.Cells(dst, 1).Value = f"CS{r}"
            scc.Cells(dst, 2).Value = f"[{ctx}] {cs.Cells(r, 2).Value or ''}"
            scc.Cells(dst, 43).Value = f"R-8 copy of CALC - CoreScratchpad row {r} ({ctx})"
            scc.Range(scc.Cells(dst, 3), scc.Cells(dst, B.LAST_COL)).Formula = \
                (tuple(tr.translate(cs_f[r], S.CS, ctx, k) for k in range(1, B.RECORDS + 1)),)
    print(f"  2. keys rows {S.SC_ID}-{S.BI_PARENT}; copies SC {len(maps['SC'])} + SCBI "
          f"{len(maps['SCBI'])} at rows {S.COPY_FIRST}-{row - 2}")

    # ---- 3. the sheet ----------------------------------------------------------------------
    n = 0
    for r in range(1, 159):
        if r in ROLLUPS:
            f = str(scc.Cells(r, 3).Formula)
            d = ROLLUPS[r]
            nf = f.replace(f"SUM(C{d}:L{d})", f"SUM(C{d}:{AP}{d})")
            if nf == f:
                raise Gate(f"roll-up row {r} is {f!r}")
            scc.Cells(r, 3).Formula = nf
        elif r in tpl:
            ctx = "SC" if r < S.SPLIT else "SCBI"
            fs = [tr.translate(tpl[r], S.SCC, ctx, k) for k in range(1, B.RECORDS + 1)]
            if r in SC_PREM + BI_PREM:
                act = S.SC_ACTIVE if r in SC_PREM else S.BI_ACTIVE
                fs = [f"=IF({colname(B.FIRST_COL + i)}${act}<>\"Yes\",0,{x[1:]})" for i, x in enumerate(fs)]
            scc.Range(scc.Cells(r, 3), scc.Cells(r, B.LAST_COL)).Formula = (tuple(fs),)
            n += 1
        else:
            vals = [scc.Cells(r, c).Value for c in range(3, 13)]
            if vals == [float(i) for i in range(1, 11)]:
                scc.Range(scc.Cells(r, 3), scc.Cells(r, B.LAST_COL)).Value = \
                    (tuple(float(i) for i in range(1, B.RECORDS + 1)),)
    print(f"  3. {n} Special Class rows -> C..{AP}; roll-ups widened; premium rows gated")

    # ---- Gate A: other coverages untouched --------------------------------------------------
    calc(app)
    after = prem(wb)
    show("after migration", after)
    for p in UNMOVED:
        if after[p] != base[p]:
            raise Gate(f"{p} moved")
    for k, g in (("BR", grid(wb.Worksheets(B.BR), 113, 42)), ("CR", grid(wb.Worksheets(p4a.CR), 168, 42)),
                 ("BI", grid(wb.Worksheets(p4a.BI), 102, 42)), ("CS", grid(cs, 285, 42))):
        d = diff_rows(snap[k], g)
        if d:
            raise Gate(f"{k} values changed on rows {d[:20]}")
    now_scc = grid(scc, 158, 12)
    moved_rows = diff_rows(col_c(snap["SCC"]), col_c(now_scc))
    idle = [(r, colname(3 + c)) for r in SC_PREM + BI_PREM for c in range(1, 10)
            if now_scc[r - 1][c] not in (0, 0.0)]
    if idle:
        raise Gate(f"inactive Special Class slots carry premium: {idle[:10]}")
    print(f"  GATE A: Building/Contents/BI and their sheets unchanged; inactive SC slots price 0; "
          f"active item's rows that moved: {moved_rows}")

    # ---- Gate B: isolation -- building 1's symbol reproduces today exactly --------------------
    saved = isc.Range("C31").Formula
    isc.Range("C31").Value = "AB"
    app.CalculateFull()
    iso_p, iso_g = prem(wb), grid(scc, 158, 12)
    isc.Range("C31").Formula = saved
    app.CalculateFull()
    back = diff_rows(col_c(snap["SCC"]), col_c(iso_g))
    if iso_p != base or back:
        raise Gate(f"with symbol AB the sheet did not return to today: premiums {iso_p}, rows {back}")
    print("  GATE B: with the item's symbol set to building 1's 'AB', every Special Class value "
          "and every premium returns EXACTLY to today -- the symbol is the only change")

    # ---- Gate C: moving ------------------------------------------------------------------------
    scc_ = scc

    def col_prem(c, rows):
        return sum(float(scc_.Cells(r, c).Value) for r in rows)

    def poke(cell, v, c, rows):
        b = col_prem(c, rows)
        f = cell.Formula
        cell.Value = v(cell) if callable(v) else v
        app.CalculateFull()
        m = col_prem(c, rows)
        cell.Formula = f
        app.CalculateFull()
        return b, m

    for label, cell, rows in (("SC record 1 limit +100k", sc.Range(f"K{S.SC_ROWS[0]}"), SC_PREM),
                              ("SCBI record 1 limit +100k", sc.Range(f"H{S.SCBI_ROWS[0]}"), BI_PREM)):
        b, m = poke(cell, lambda x: x.Value + 100000, 3, rows)
        if b == m:
            raise Gate(f"{label}: no response")
        print(f"  GATE C {label}: {b:g} -> {m:g}")
    b, m = poke(sc.Range(f"C{B.LOC_ROWS[0]}"), "'GA", 3, SC_PREM)
    if b == m:
        raise Gate("SC record 1 did not respond to its location's state")
    print(f"  GATE C location 1 state FL -> GA reaches SC record 1: {b:g} -> {m:g}")

    s_src, s_dst = S.SC_ROWS[0], S.SC_ROWS[0] + 10
    b_src, b_dst = S.SCBI_ROWS[0], S.SCBI_ROWS[0] + 10
    sv = sc.Range(f"A{s_src}:W{s_src}").Value[0]
    bv = sc.Range(f"A{b_src}:O{b_src}").Value[0]
    saved_s, saved_b = sc.Range(f"A{s_dst}:W{s_dst}").Formula, sc.Range(f"A{b_dst}:O{b_dst}").Formula
    tot0 = prem(wb)
    new_id = f"{sv[0]}b"
    for i, v in enumerate(sv):
        sc.Cells(s_dst, 1 + i).Value = as_input(new_id if i == 0 else v)
    for i, v in enumerate(bv):
        sc.Cells(b_dst, 1 + i).Value = as_input(f"{bv[0]}b" if i == 0 else new_id if i == 1 else v)
    app.CalculateFull()
    m = B.FIRST_COL + 10
    got = (col_prem(m, SC_PREM), col_prem(m, BI_PREM), scc.Cells(S.BI_PARENT, m).Value)
    want = (col_prem(3, SC_PREM), col_prem(3, BI_PREM), 11.0)
    tot1 = prem(wb)
    sc.Range(f"A{s_dst}:W{s_dst}").Formula = saved_s
    sc.Range(f"A{b_dst}:O{b_dst}").Formula = saved_b
    app.CalculateFull()
    print(f"  GATE C 11th SC item + its SC BI (Schedule only, copies of record 1): SC {got[0]:g} "
          f"vs {want[0]:g}, SCBI {got[1]:g} vs {want[1]:g}, SCParentCol {got[2]}; totals "
          f"SC {tot0['OUT_Prem_SCBuilding']:g}->{tot1['OUT_Prem_SCBuilding']:g}, "
          f"SCBI {tot0['OUT_Prem_SCBI']:g}->{tot1['OUT_Prem_SCBI']:g}")
    if got != want:
        raise Gate("the 11th Special Class records did not rate like their twins")
    if prem(wb) != after:
        raise Gate("did not restore")
    show("restored", prem(wb))
    return after


def main() -> int:
    if p4a.TARGET.name.lower() == p4a.FORBIDDEN:
        sys.exit("ABORT: refusing to write to the live rater.")
    pre = p4a.excel_pids()
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
        wb = app.Workbooks.Open(str(p4a.TARGET), UpdateLinks=0)
        app.Calculation = -4135
        try:
            expected = migrate(app, wb)
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
        scc = wb.Worksheets(S.SCC)
        checks = {
            "premiums as saved": final == expected,
            "AQ1=Source": scc.Range("AQ1").Value == "Source",
            "SC LocIdx C=1": scc.Range(f"C{S.SC_LOC}").Value == 1,
            "roll-up to AP": f":{AP}22" in str(scc.Range("C23").Formula),
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
