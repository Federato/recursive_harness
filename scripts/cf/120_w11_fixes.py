"""Backlog W-11, split into three rater fixes -- applied one at a time, each verified
against live ISO with `119_payload_three_way.py` before the next. Approved 2026-09-22.

    python scripts/cf/120_w11_fixes.py --fix W1     # then: 119 ... --state FL
    python scripts/cf/120_w11_fixes.py --fix W13
    python scripts/cf/120_w11_fixes.py --fix W12

**W-1 -- Legal Liability Additional Insurable Interest on Broad / Special contents.**
Contents rows 76 (Broad) and 104 (Special) tested the wrong input for "Legal Liability
Coverage Form" (occupancy severity / construction description), so the AII factor never
applied. They now test the coverage form exactly as rows 25 / 53 do.

**W-13 -- roof surfacing factor in Florida and West Virginia.** Both states file
`LimitationsOnCovForRoofSurfacingFactor` header-only (every edition on disk), so ISO
applies no roof factor there. New `TBL - RoofSurfacing` expands the factor per state
(no CW placeholder rows); FL / WV carry none, and Bldg Rating rows 9 / 40 fall back to
1.0 when a state has no row.

**W-12 -- the Group II symbol ISO actually rates on.** ISO swaps the building's Group II
symbol for open-sided buildings and classes 0580/0585/1300/1650/1150/1751/1752
(`SetBGIISymbolToUse`; Montana files its own version). New `TBL - BGIISymbolToUse`
(per state: GA, KS, MT file their own rows; NY and PR file header-only and get CW's,
flagged) and CoreScratchpad row 287 `BGIISymbolToUse`, which now feeds the base rate
(59), lowest base rate (72) and wind/hail exclusion (205, and Contents' copy).

Each stage: backup-free (the caller backs up), Excel-closed guard, 1.01 refused, gates
(untouched coverages unchanged; only the expected records move; an isolation check),
save, reopen-verify.
"""
from __future__ import annotations

import argparse
import sys
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from r8_contents_translate import colname                          # noqa: E402

p4a = import_module("112_r8_phase4a_building")
Gate, prem, show, grid, calc = p4a.Gate, p4a.prem, p4a.show, p4a.grid, p4a.calc

ISO = Path(r"C:\Projects\ISO_ERC_Files\CF\20260601")
CW = ISO / "CFCW20260601V01" / "Rate Tables"
BR, CR, CS, BI, SCH = ("CALC - Bldg Rating", "CALC - Contents Rating", "CALC - CoreScratchpad",
                       "CALC - BI Rating", "IN - Schedule")
COLS = range(3, 43)
AP = colname(42)
SCC = "CALC - Special Class"
PREM = {"OUT_Prem_Building": BR, "OUT_Prem_Contents": CR, "OUT_Prem_BI": BI,
        "OUT_Prem_SCBuilding": SCC, "OUT_Prem_SCBI": SCC}


def states(wb):
    v = wb.Worksheets("TBL - LCM").Range("A2:A47").Value
    return [r[0] for r in v if r[0]]


def read_csv(path):
    import csv
    with open(path, encoding="utf-8-sig") as fh:
        return list(csv.reader(fh))[1:]


def state_file(state, table):
    """The table from the state's LATEST package, across every edition folder.

    Searching only the 2026-06 folder missed Florida entirely -- its package
    (`CF FL 20241201`) sits under the 2023 edition folders -- and would have handed
    Florida the countrywide factor W-13 exists to remove."""
    import re
    pkgs = []
    for d in ISO.parent.glob(f"*/CF {state} *"):
        m = re.match(rf"CF {state} (\d{{8}}) V(\d+)", d.name)
        if m and d.is_dir():
            pkgs.append((m.group(1), int(m.group(2)), d))
    for _, _, d in sorted(pkgs, reverse=True):
        f = d / "Rate Tables" / f"{table}.RateTable.csv"
        if f.exists():
            return f
    return None


def new_sheet(wb, name):
    if name in [w.Name for w in wb.Worksheets]:
        raise Gate(f"'{name}' already exists")
    ws = wb.Worksheets.Add(After=wb.Worksheets(wb.Worksheets.Count))
    ws.Name = name
    return ws


def write_rows(ws, top, left, rows):
    rng = ws.Range(ws.Cells(top, left), ws.Cells(top + len(rows) - 1, left + len(rows[0]) - 1))
    rng.Value = tuple(tuple(p4a.as_input(x) if isinstance(x, str) else x for x in r) for r in rows)


# ---------------------------------------------------------------------------- W-1

def fix_w1(app, wb):
    cr = wb.Worksheets(CR)
    n = 0
    for c in COLS:
        src = str(cr.Cells(53, c).Formula)
        if "'IN - Schedule'!$H$91:$H$130" not in src:
            raise Gate(f"Contents row 53 col {colname(c)} is not the coverage-form test: {src!r}")
        for r in (76, 104):
            cr.Cells(r, c).Formula = src
            n += 1
    return f"W-1: {n} cells -- Contents rows 76/104 now test the coverage form (as row 53)", {CR}


# ---------------------------------------------------------------------------- W-13

def fix_w13(app, wb):
    cw = {r[1]: float(r[2]) for r in read_csv(CW / "LimitationsOnCovForRoofSurfacingFactor.RateTable.csv")}
    gii = wb.Worksheets("TBL - BldgBGIIRating").Range("S2:T5").Value
    gii = {r[0]: r[1] for r in gii if r[0]}
    none, rows = [], [("Key", "State", "Limitation", "BGIFactor", "BGIIFactor")]
    for st in states(wb):
        f = state_file(st, "LimitationsOnCovForRoofSurfacingFactor")
        filed = read_csv(f) if f else None
        if filed is not None and not filed:
            none.append(st)                                   # header-only: no factor
            continue
        src = {r[1]: float(r[2]) for r in filed} if filed else cw
        for lim, fac in src.items():
            rows.append((f"{st}|{lim}", st, lim, fac, gii.get(lim, fac)))
    ws = new_sheet(wb, "TBL - RoofSurfacing")
    write_rows(ws, 1, 1, rows)
    ws.Range("H1").Value = "Source"
    ws.Range("H2").Value = ("ISO ERC CF 20260601 LimitationsOnCovForRoofSurfacingFactor, per state. "
                            f"Header-only (ISO applies NO roof factor): {', '.join(none)}. BGIIFactor "
                            "kept from the rater's own Group II table (not traced against ISO).")
    last = len(rows)
    br = wb.Worksheets(BR)
    for c in COLS:
        X = colname(c)
        key = f"'{CS}'!{X}$2&\"|\"&'{SCH}'!$Y${45 + c}"
        br.Cells(9, c).Formula = f"=IFERROR(VLOOKUP({key},'TBL - RoofSurfacing'!$A$2:$E${last},4,FALSE),1)"
        br.Cells(40, c).Formula = f"=IFERROR(VLOOKUP({key},'TBL - RoofSurfacing'!$A$2:$E${last},5,FALSE),1)"
    return (f"W-13: TBL - RoofSurfacing {last - 1} rows; no factor in {none}; Bldg Rating rows 9/40 "
            f"read it per state"), {BR}


# ---------------------------------------------------------------------------- W-12

def fix_w12(app, wb):
    cw_add = read_csv(CW / "BasicGroupIISymbolAdditionalClasses.RateTable.csv")
    cw_roof = read_csv(CW / "BGIISymbolAdditionalClassesRoofConstruction.RateTable.csv")
    cw_oil = read_csv(CW / "BasicGroupIISymbolOilDistributingStations.RateTable.csv")
    add, roof, oil, flags = [("Key", "Symbol")], [("Key", "Symbol")], [("Key", "Symbol")], []
    for st in states(wb):
        for table, src, out, keyf in (
                ("BasicGroupIISymbolAdditionalClasses", cw_add, add,
                 lambda r, st=st: (f"{st}|{r[1]}|{int(float(r[2]))}", r[3])),
                ("BGIISymbolAdditionalClassesRoofConstruction", cw_roof, roof,
                 lambda r, st=st: (f"{st}|{r[1]}", r[2])),
                ("BasicGroupIISymbolOilDistributingStations", cw_oil, oil,
                 lambda r, st=st: (f"{st}", r[2]))):
            f = state_file(st, table)
            filed = read_csv(f) if f else None
            if filed is not None and not filed:
                flags.append(f"{st}:{table}")
                filed = None                                  # header-only -> CW, flagged
            out.extend(keyf(r) for r in (filed or src))
    ws = new_sheet(wb, "TBL - BGIISymbolToUse")
    write_rows(ws, 1, 1, add)
    write_rows(ws, 1, 4, roof)
    write_rows(ws, 1, 7, oil)
    sup = [("SuperiorRoofing",)] + [(r[1],) for r in cw_roof]
    write_rows(ws, 1, 10, sup)
    ws.Range("L1").Value = "Source"
    ws.Range("L2").Value = ("ISO ERC CF 20260601: BasicGroupIISymbolAdditionalClasses (A:B), "
                            "BGIISymbolAdditionalClassesRoofConstruction (D:E), "
                            "BasicGroupIISymbolOilDistributingStations (G:H), per state; GA/KS/MT "
                            "from their own packages. Header-only in ISO (CW rows used, flagged -- "
                            f"ISO itself cannot rate these): {', '.join(sorted(set(flags)))}. "
                            "Superior-roofing list (J) = SetSuperiorRoofingIndicator's constants.")
    A, D, G = (f"'TBL - BGIISymbolToUse'!$A$2:$B${len(add)}",
               f"'TBL - BGIISymbolToUse'!$D$2:$E${len(roof)}",
               f"'TBL - BGIISymbolToUse'!$G$2:$H${len(oil)}")
    J = f"'TBL - BGIISymbolToUse'!$J$2:$J${len(sup)}"
    cs = wb.Worksheets(CS)
    if cs.Range("B287").Value not in (None, ""):
        raise Gate("CoreScratchpad row 287 is not free")
    cs.Range("B287").Value = "BGIISymbolToUse (ISO SetBGIISymbolToUse; W-12)"
    fs = []
    for c in COLS:
        X, b = colname(c), 45 + c
        st, cls, op = f"{X}$2", f"'{SCH}'!$E${b}", f"'{SCH}'!$M${b}"
        code, ctype, sym = f"'{SCH}'!$H${b}", f"'{SCH}'!$I${b}", f"'{SCH}'!$J${b}"
        look = lambda k, T=A: f"IFERROR(VLOOKUP({k},{T},2,FALSE),\"\")"        # noqa: E731
        sup_ = f"ISNUMBER(MATCH({ctype},{J},0))"
        roofL = look(f"{st}&\"|\"&{ctype}", D)
        oilL = look(st, G)
        cw_f = (f"IF(OR({op}=\"Yes\",{cls}=\"0580\",{cls}=\"0585\",{cls}=\"1300\",{cls}=\"1650\",{cls}=\"1150\"),"
                f"IF(AND({sup_},{ctype}<>\"\"),{roofL},"
                f"IF({op}=\"Yes\",{look(f'{st}&\"|OpenSides|\"&{code}')},"
                f"IF(OR({cls}=\"0580\",{cls}=\"0585\",{cls}=\"1300\",{cls}=\"1650\"),"
                f"{look(f'{st}&\"|\"&{cls}&\"|1\"')},{look(f'{st}&\"|\"&{cls}&\"|\"&{code}')}))),"
                f"IF(OR({cls}=\"1751\",{cls}=\"1752\"),{oilL},{sym}))")
        mt_f = (f"IF({sup_},{roofL},"
                f"IF(AND({op}=\"Yes\",N({code})<>0),{look(f'{st}&\"|OpenSides|\"&{code}')},"
                f"IF(OR({cls}=\"0580\",{cls}=\"1300\",{cls}=\"1650\"),{look(f'{st}&\"|\"&{cls}&\"|1\"')},"
                f"IF(AND({cls}=\"1150\",N({code})<>0),{look(f'{st}&\"|\"&{cls}&\"|\"&{code}')},"
                f"IF(OR({cls}=\"1751\",{cls}=\"1752\"),{oilL},{sym})))))")
        fs.append(f"=IF({st}=\"MT\",{mt_f},{cw_f})")
    cs.Range(cs.Cells(287, 3), cs.Cells(287, 42)).Formula = (tuple(fs),)
    n = 0
    for r in (59, 72, 205):
        for c in COLS:
            X, b = colname(c), 45 + c
            f = str(cs.Cells(r, c).Formula)
            nf = f.replace(f"'{SCH}'!$J${b}", f"{X}$287")
            if nf == f:
                raise Gate(f"CoreScratchpad {r}{X} did not read the Schedule symbol: {f!r}")
            cs.Cells(r, c).Formula = nf
            n += 1
    cr = wb.Worksheets(CR)
    for c in COLS:
        X = colname(c)
        f = str(cr.Cells(166, c).Formula)
        nf = f.replace(f"INDEX('{SCH}'!$J$48:$J$87,{X}$116)", f"INDEX('{CS}'!$C$287:${AP}$287,1,{X}$116)")
        if nf == f:
            raise Gate(f"Contents 166{X} did not read the Schedule symbol: {f!r}")
        cr.Cells(166, c).Formula = nf
        n += 1
    return (f"W-12: TBL - BGIISymbolToUse ({len(add) - 1}/{len(roof) - 1}/{len(oil) - 1} rows); "
            f"CoreScratchpad 287 + {n} key cells repointed"), {BR, CR, BI}


# ---------------------------------------------------------------------------- W-17 / W-6

def fix_w17(app, wb):
    """Contents Special RATE omitted the personal-property territory multiplier it had
    just computed (row 87). ISO: SpecialRate = SpecialBaseRate x LCM x
    PrsnlPropTerrMultiplier (CA 0.14 x 1.318 = 0.185)."""
    cr = wb.Worksheets(CR)
    n = 0
    for c in COLS:
        X = colname(c)
        f = str(cr.Cells(88, c).Formula)
        nf = f.replace(f"ROUND({X}85*{X}86,3)", f"ROUND({X}85*{X}86*{X}87,3)")
        if nf == f:
            raise Gate(f"Contents 88{X} is not the expected RATE formula: {f!r}")
        cr.Cells(88, c).Formula = nf
        n += 1
    return f"W-17: {n} cells -- Contents Special RATE now applies the territory multiplier", {CR}


def fix_w6(app, wb):
    """Contents Special deductible factor banded on the record's own contents limit
    (its copy of CoreScratchpad 176-182). ISO copies DeductibleFactorSpecial down from
    the Structure -- the building's own Special factor, Bldg Rating row 100."""
    cr = wb.Worksheets(CR)
    n = 0
    for c in COLS:
        X = colname(c)
        cr.Cells(97, c).Formula = f"=INDEX('{BR}'!$C$100:${AP}$100,1,{X}$116)"
        n += 1
    return f"W-6: {n} cells -- Contents row 97 = the parent building's Special deductible factor", {CR}


def fix_w14(app, wb):
    """BI Group II RATE (row 33) left out the BCEG factor. ISO's BI BasicGroupIIRate =
    base x LCM x numeric value x BGIIBaseRateAdjustmentFactor x BCEGFactor
    (FL: 0.129 x 4 x 0.7 x 0.91 = 0.329). The building's chain has it (Bldg Rating 41)."""
    bi = wb.Worksheets(BI)
    n = 0
    for c in COLS:
        X = colname(c)
        f = str(bi.Cells(33, c).Formula)
        old = f"ROUND({X}29*{X}30*{X}31*{X}32,3)"
        if old not in f:
            raise Gate(f"BI 33{X} is not the expected RATE formula: {f!r}")
        bi.Cells(33, c).Formula = f.replace(
            old, f"ROUND({X}29*{X}30*{X}31*{X}32*INDEX('{BR}'!$C$41:${AP}$41,1,{X}$81),3)")
        n += 1
    return f"W-14: {n} cells -- BI Group II RATE now applies the building's BCEG factor", {BI}


def fix_w14r(app, wb):
    """W-14 refinement: ISO rounds the adjusted Group II base BEFORE applying BCEG --
    ROUND(ROUND(base x LCM x numeric x adj, 3) x BCEG, 3). AK: round(0.014 x 0.75) =
    0.011, x 0.97 -> 0.011 (the rater's single ROUND gave 0.010)."""
    bi = wb.Worksheets(BI)
    n = 0
    for c in COLS:
        X = colname(c)
        f = str(bi.Cells(33, c).Formula)
        bce = f"INDEX('{BR}'!$C$41:${AP}$41,1,{X}$81)"
        old = f"ROUND({X}29*{X}30*{X}31*{X}32*{bce},3)"
        if old not in f:
            raise Gate(f"BI 33{X} is not the W-14 formula: {f!r}")
        bi.Cells(33, c).Formula = f.replace(old, f"ROUND(ROUND({X}29*{X}30*{X}31*{X}32,3)*{bce},3)")
        n += 1
    return f"W-14r: {n} cells -- BI Group II RATE rounds before BCEG, as ISO", {BI}


# ---------------------------------------------------------------------------- W-10 / W-18 / W-19

def sc_state(X):
    return f"INDEX('{SCH}'!$C$5:$C$44,{X}$163)"


def fix_w10(app, wb):
    """Special Class Group I base rate keyed on the ITEM's own protection class. ISO
    uses ProtectionClassToUse, from the LOCATION's class (FL: band "1 to 4" from 4)."""
    sc = wb.Worksheets(SCC)
    n = 0
    for c in COLS:
        X, r = colname(c), 217 + c
        f = str(sc.Cells(172, c).Formula)
        own = f"'{SCH}'!$P${r}"
        if own not in f:
            raise Gate(f"SC 172{X} does not read the item's ProtClass: {f!r}")
        sc.Cells(172, c).Formula = f.replace(own, f"INDEX('{SCH}'!$F$5:$F$44,{X}$163)")
        n += 1
    return f"W-10: {n} cells -- Special Class rate key uses the location's protection class", {SCC}


def fix_w18(app, wb):
    """Florida subtracts a vandalism exclusion RATE (VandalismExclRate) instead of the
    x0.95 factor. Data-driven: where the rater's rate table ('TBL - Special Class'
    CL:CO, already used by SC BI row 92) has a row for state+class, subtract it and
    neutralise the factor; elsewhere the factor stands."""
    sc = wb.Worksheets(SCC)
    if sc.Range("B221").Value not in (None, ""):
        raise Gate("Special Class row 221 is not free")
    sc.Range("B221").Value = "VandalismExclRate (rate states, ISO; W-18)"
    sc.Cells(221, 43).Value = "R-8 W-18: 'TBL - Special Class' CL:CO x LCM, when the vandalism exclusion is elected"
    n = 0
    for c in COLS:
        X, r = colname(c), 217 + c
        sc.Cells(221, c).Formula = (
            f"=IF('{SCH}'!$U${r}=\"Yes\",IFERROR(ROUND(VLOOKUP({sc_state(X)}&{X}173,"
            f"'TBL - Special Class'!$CL$2:$CO$150,4,FALSE)*{X}5,3),0),0)")
        f7 = str(sc.Cells(7, c).Formula)
        sc.Cells(7, c).Formula = f"=IF({X}$221>0,1,{f7[1:]})"
        f9 = str(sc.Cells(9, c).Formula)
        old9 = f"ROUND({X}6*{X}7*{X}8,3)"
        if old9 not in f9:
            raise Gate(f"SC 9{X} is not the expected COL adjustment: {f9!r}")
        sc.Cells(9, c).Formula = f9.replace(old9, f"ROUND(({X}6-{X}$221)*{X}7*{X}8,3)")
        n += 3
    return f"W-18: {n} cells -- Special Class subtracts the vandalism rate where a state files one", {SCC}


def fix_w19(app, wb):
    """Florida files DeductibleByLocationFactor header-only: no 0.995 credit. Per-state
    table, no CW placeholder rows; the hard-coded 0.995s read it."""
    cw = read_csv(CW / "DeductibleByLocationFactor.RateTable.csv")
    rows, none = [("State", "Factor")], []
    for st in states(wb):
        f = state_file(st, "DeductibleByLocationFactor")
        filed = read_csv(f) if f else None
        if filed is not None and not filed:
            none.append(st)
            continue
        rows.append((st, float((filed or cw)[0][2])))
    ws = new_sheet(wb, "TBL - DeductibleByLocation")
    write_rows(ws, 1, 1, rows)
    ws.Range("D1").Value = "Source"
    ws.Range("D2").Value = (f"ISO ERC CF DeductibleByLocationFactor, each state's latest package. Header-only "
                            f"(ISO applies NO credit): {', '.join(none)}")
    T = f"'TBL - DeductibleByLocation'!$A$2:$B${len(rows)}"
    n = 0
    for ws_, rws, stf in ((wb.Worksheets(BR), (19, 49), lambda X: f"'{CS}'!{X}$2"),
                          (wb.Worksheets(SCC), (12, 36), sc_state)):
        for r in rws:
            for c in COLS:
                X = colname(c)
                f = str(ws_.Cells(r, c).Formula)
                if "0.995" not in f:
                    raise Gate(f"{ws_.Name}!{X}{r} has no 0.995: {f!r}")
                ws_.Cells(r, c).Formula = f.replace("0.995", f"IFERROR(VLOOKUP({stf(X)},{T},2,FALSE),1)")
                n += 1
    return f"W-19: {n} cells -- deductible-by-location credit per state; none in {none}", {SCC, BR}


def com_retry(fn, tries=30):
    """Excel answers 'Call was rejected by callee' while busy; wait and retry."""
    import time
    import pywintypes
    for i in range(tries):
        try:
            return fn()
        except pywintypes.com_error as e:
            if e.args[0] != -2147418111 or i == tries - 1:
                raise
            time.sleep(1)


_ACTIVE_CACHE: dict = {}


def active_cols(wb, sheet, row):
    key_ = (sheet, row >= 88 if sheet == "CALC - Special Class" else None)
    if key_ in _ACTIVE_CACHE:
        return _ACTIVE_CACHE[key_]
    name, key = {BR: (CS, 284), CR: (CR, 114), BI: (BI, 80),
                 "CALC - Special Class": ("CALC - Special Class", 162 if row < 88 else 167)}[sheet]
    ws = com_retry(lambda: wb.Worksheets(name))
    vals = com_retry(lambda: ws.Range(ws.Cells(key, 3), ws.Cells(key, 42)).Value[0])
    _ACTIVE_CACHE[key_] = {i for i, v in enumerate(vals) if v == "Yes"}
    return _ACTIVE_CACHE[key_]


FIXES = {"W1": fix_w1, "W13": fix_w13, "W12": fix_w12, "W17": fix_w17, "W6": fix_w6, "W14": fix_w14, "W14R": fix_w14r, "W10": fix_w10, "W18": fix_w18, "W19": fix_w19}
#: fixes that must leave every active record's numbers exactly as they were (input restructures)
NO_MOVE: set = set()
#: which calc-sheet columns each fix may move (0-based from C): item 1 only today
EXPECT_COLS = {"W1": {0}, "W13": {0}, "W12": {0}, "W17": {0, 1, 2, 3}, "W6": {0, 1, 2, 3}, "W14": {0, 1, 2, 3}, "W14R": {0, 1, 2, 3}, "W10": {0}, "W18": {0}, "W19": {0}}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fix", choices=FIXES, required=True)
    a = ap.parse_args()
    if p4a.TARGET.name.lower() == p4a.FORBIDDEN:
        sys.exit("ABORT: refusing to write to the live rater.")
    pre = p4a.excel_pids()
    if pre:
        sys.exit(f"ABORT: Excel running {pre}")
    import win32com.client
    app = win32com.client.DispatchEx("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    app.EnableEvents = False
    wb, ok, after = None, False, None
    try:
        wb = app.Workbooks.Open(str(p4a.TARGET), UpdateLinks=0)
        app.Calculation = -4135
        calc(app)
        base = prem(wb)
        snap = {s: grid(wb.Worksheets(s), n, 42) for s, n in
                ((BR, 113), (CR, 168), (BI, 102), ("CALC - Special Class", 219))}
        try:
            note, allowed = FIXES[a.fix](app, wb)
            print(" ", note)
            calc(app)
            after = prem(wb)
            show("before", base)
            show("after", after)
            moved_sheets, idle = set(), 0
            for s, g0 in snap.items():
                g1 = com_retry(lambda s=s, g0=g0: grid(wb.Worksheets(s), len(g0), 42))
                labels = com_retry(lambda s=s, g0=g0: wb.Worksheets(s).Range(f"B1:B{len(g0)}").Value)
                for r, (a0, a1) in enumerate(zip(g0, g1), start=1):
                    if str(labels[r - 1][0] or "").strip().upper().startswith("TOTAL"):
                        continue        # SUM across records, parked in column C; totals are gated below
                    act = active_cols(wb, s, r)
                    for c, (x, y) in enumerate(zip(a0, a1)):
                        if x != y:
                            if c not in act:
                                idle += 1             # empty slot: listed, not failed
                                continue
                            if s not in allowed or c not in EXPECT_COLS[a.fix]:
                                raise Gate(f"{s}!{colname(c + 3)}{r} moved ({x} -> {y}) -- outside "
                                           f"what {a.fix} may change")
                            moved_sheets.add(s)
            for k, s in PREM.items():
                if after[k] != base[k] and s not in allowed:
                    raise Gate(f"{k} moved but {a.fix} should not touch it")
            if not moved_sheets and a.fix not in NO_MOVE:
                raise Gate(f"{a.fix} changed nothing -- inert")
            if a.fix in NO_MOVE and (moved_sheets or after != base):
                raise Gate(f"{a.fix} must not move any active premium, and did")
            print(f"  GATE: among ACTIVE records only the expected columns moved, only on {sorted(moved_sheets)}"
                  f" ({idle} intermediate cells moved in empty slots; premiums there stay gated to 0)")
            ok = True
        except Gate as e:
            print(f"\n  GATE FAILED: {e}\n  NOT saving.")
        if ok:
            app.Calculation = -4105
            app.CalculateFull()
            # Late-bound COM sometimes resolves `wb.Save` as a property and invokes the
            # method on attribute access, returning a bool (W-20, 2026-09-23: saved, then
            # "'bool' object is not callable" skipped the reopen check). Call it only if
            # it is still callable; the reopen-verify below is the proof either way.
            save = wb.Save
            if callable(save):
                save()
            print("  saved.")
        # AK / W-24, 2026-09-23: "call rejected" here, and late-bound COM may run Close when the
        # attribute is read (returning a bool), exactly as with Save above.
        close = com_retry(lambda: wb.Close)
        if callable(close):
            com_retry(lambda: close(SaveChanges=False))
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
        ok = final == after and not [x.Name for x in wb.Names if "#REF" in str(x.RefersTo)]
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
