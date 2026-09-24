"""Backlog W-16 -- Business Income Group I below ISO in every state (AK -9, FL -7, CA -1).
Traced 2026-09-23 against live ISO; two causes, both in ISO's countrywide rules.

**1. Rounding order (BI row 10).** ISO `SetBasicGroupIRate` (Class rating) rounds three
times: ROUND(ROUND((ROUND(base x LCM, 3) + substd + vacant) x terr x PC, 3) x adj, 3).
The rater rounded once. AK: 0.097 x 1.05 = 0.102, x 0.75 = 0.0765 -> 0.077 (ISO);
the single ROUND gave 0.076.

**2. The Cyber cause-of-loss-exceptions factor is Business Income's own.** ISO looks up
`CyberIncidentExclusionCOLExcptnsFactorBusnIncome*` with `CyberTypeOfLimitBusinessIncome`,
which is "Sublimit" only when a Cyber BUSINESS INCOME (or, for Extra Expense Only, EXTRA
EXPENSE) limit is entered. The rater has no such input -- only the property-damage sublimit
and the aggregate -- so Business Income is always "Full Limit": Group I / II / Broad = 1,
Special = 0.997 (aggregate) or 0.998. The rater borrowed the BUILDING's factors (0.997 and
0.996, which are the Sublimit rows). Same rule for Special Class Business Income.

**SC BI premium rounding.** ISO rounds limit x rate x IRPM x package mod to the dollar, then
applies the two Cyber factors and rounds again; the rater's SC BI rows rounded once.

    python scripts/cf/124_w16_bi_fixes.py --fix W16

Runs through `120_w11_fixes.main` (Excel-closed guard, 1.01 refused, gates, save,
reopen-verify). The caller backs up first.
"""
from __future__ import annotations

import sys
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from r8_contents_translate import colname                          # noqa: E402

w11 = import_module("120_w11_fixes")
Gate, BI, SCC, COLS = w11.Gate, w11.BI, w11.SCC, w11.COLS

POL = "'IN - Policy'"
#: ISO CyberIncidentExclusionWithEnsuingCauseOfLossExceptionsFactors, "Full Limit" rows
BI_SPECIAL = f"=IF({POL}!$F$4<>\"Yes\",1,IF({POL}!$F$6>0,0.997,0.998))"


def fix_w16(app, wb):
    bi, sc = wb.Worksheets(BI), wb.Worksheets(SCC)
    n = 0
    for c in COLS:
        X = colname(c)
        old10 = f"=ROUND((({X}3*{X}4)+{X}5+{X}6)*{X}7*{X}9*{X}8,3)"
        if str(bi.Cells(10, c).Formula) != old10:
            raise Gate(f"BI 10{X} is not the expected RATE formula: {bi.Cells(10, c).Formula!r}")
        bi.Cells(10, c).Formula = f"=ROUND(ROUND((ROUND({X}3*{X}4,3)+{X}5+{X}6)*{X}7*{X}8,3)*{X}9,3)"
        if "'CALC - Bldg Rating'!$C$31:$AP$31" not in str(bi.Cells(24, c).Formula):
            raise Gate(f"BI 24{X} does not borrow the building's factor: {bi.Cells(24, c).Formula!r}")
        bi.Cells(24, c).Formula = "=1"
        if "'CALC - Bldg Rating'!$C$111:$AP$111" not in str(bi.Cells(74, c).Formula):
            raise Gate(f"BI 74{X} does not borrow the building's factor: {bi.Cells(74, c).Formula!r}")
        bi.Cells(74, c).Formula = BI_SPECIAL
        n += 3
        for col_row, prem_row, special in ((104, 105, False), (125, 126, False),
                                           (139, 140, False), (156, 157, True)):
            sc.Cells(col_row, c).Formula = BI_SPECIAL if special else "=1"
            p = prem_row
            old = (f"=IF({X}$167<>\"Yes\",0,ROUND(({X}{p - 7}/100)*{X}{p - 6}*{X}{p - 5}*{X}{p - 4}"
                   f"*{X}{p - 3}*{X}{p - 2}*{X}{p - 1},0))")
            if str(sc.Cells(p, c).Formula) != old:
                raise Gate(f"SC {p}{X} is not the expected premium formula: {sc.Cells(p, c).Formula!r}")
            sc.Cells(p, c).Formula = (f"=IF({X}$167<>\"Yes\",0,ROUND(ROUND(({X}{p - 7}/100)*{X}{p - 6}"
                                      f"*{X}{p - 5}*{X}{p - 4}*{X}{p - 3},0)*{X}{p - 2}*{X}{p - 1},0))")
            n += 2
    bi.Range("B24").Value = "CyberExclCOLExcpnsFactorBGI (BI own: Full Limit = 1; W-16)"
    bi.Range("B74").Value = "CyberExclCOLExcpnsFactorSpecial (BI own: Full Limit; W-16)"
    return (f"W-16: {n} cells -- BI Group I rate rounds as ISO; BI and SC BI use Business Income's "
            f"own Cyber exceptions factors; SC BI premium rounds before Cyber"), {BI, SCC}


BR, CR = w11.BR, w11.CR
#: premium row -> (final-rate row, LegalLiab row, AII row), Building and Contents
LL_ROWS = {BR: {32: (24, 25, 26), 62: (54, 55, 56), 86: (78, 79, 80), 112: (104, 105, 106)},
           CR: {30: (23, 24, 25), 58: (51, 52, 53), 81: (74, 75, 76), 109: (102, 103, 104)}}
#: premium rows whose last two factors are the Cyber pair
CYBER_ROWS = {BR: (32, 62, 86, 112), CR: (30, 58, 81, 109), BI: (25, 45, 59, 75),
              SCC: (105, 126, 140, 157)}
SC_ROWS = (22, 46, 65, 86)


def fix_w20(app, wb):
    """Legal Liability: ISO rounds the rate before the limit --
    ROUND(ROUND(rate x LegalLiabFactor, 3) x AII, 3) (Structure and PersonalProperty
    `SetPremium`, CovType / CovForm = Legal Liability). FL Building BGI: 0.249 x 0.25 =
    0.062, x 1.25 = 0.078, x 6750 = 527 (ISO); the rater's unrounded product gave 525.
    Off Legal Liability both factors are 1 and the rate is already 3dp: no change."""
    n = 0
    for sheet, rows in LL_ROWS.items():
        ws = wb.Worksheets(sheet)
        for p, (r, ll, aii) in rows.items():
            for c in COLS:
                X = colname(c)
                f = str(ws.Cells(p, c).Formula)
                old = f"{X}{r}*{X}{ll}*{X}{aii}"
                if f.count(old) != 1:
                    raise Gate(f"{sheet}!{X}{p} lacks {old}: {f!r}")
                ws.Cells(p, c).Formula = f.replace(old, f"ROUND(ROUND({X}{r}*{X}{ll},3)*{X}{aii},3)")
                n += 1
    return f"W-20: {n} cells -- Legal Liability rate rounds as ISO before the limit", {BR, CR}


def fix_w21(app, wb):
    """ISO applies the two Cyber factors one at a time, rounding to the dollar after
    each (every coverage's `SetPremium`: nested Product DecimalPlaces="0"). The rater
    multiplied both, then rounded once. AK Building BGII: 100 x 0.995 = 99.5 -> 100,
    x 0.997 -> 100 (ISO); rater 100 x 0.992 = 99.2 -> 99. Special Class rounded
    everything in one ROUND; it now rounds the base, then each Cyber factor."""
    n = 0
    for sheet, rows in CYBER_ROWS.items():
        ws = wb.Worksheets(sheet)
        for p in rows:
            for c in COLS:
                X = colname(c)
                f = str(ws.Cells(p, c).Formula)
                tail = f",0)*{X}{p - 2}*{X}{p - 1},0))"
                if not f.endswith(tail) or "ROUND(ROUND(" not in f:
                    raise Gate(f"{sheet}!{X}{p} is not ROUND(ROUND(base,0)*cyber*cyber,0): {f!r}")
                head = f[:-len(tail)]
                i = head.index("ROUND(ROUND(")
                ws.Cells(p, c).Formula = (head[:i] + "ROUND(ROUND(ROUND(" + head[i + len("ROUND(ROUND("):]
                                          + f",0)*{X}{p - 2},0)*{X}{p - 1},0))")
                n += 1
    ws = wb.Worksheets(SCC)
    for p in SC_ROWS:
        for c in COLS:
            X = colname(c)
            f = str(ws.Cells(p, c).Formula)
            base = f"({X}{p - 7}/100)*{X}{p - 6}*{X}{p - 5}*{X}{p - 4}*{X}{p - 3}"
            old = f"=IF({X}$162<>\"Yes\",0,ROUND({base}*{X}{p - 2}*{X}{p - 1},0))"
            if f != old:
                raise Gate(f"SC {X}{p} is not the expected premium formula: {f!r}")
            ws.Cells(p, c).Formula = (f"=IF({X}$162<>\"Yes\",0,ROUND(ROUND(ROUND({base},0)*{X}{p - 2},0)"
                                      f"*{X}{p - 1},0))")
            n += 1
    return f"W-21: {n} cells -- Cyber factors applied one at a time, rounding after each", {BR, CR, BI, SCC}


GROUPS = ("Basic Group I", "Basic Group II", "Broad", "Special")


def fix_cy(app, wb):
    """User decision 2026-09-23: drop Cyber where ISO files none. `CyberIncidentExclusionFactors`
    and `…WithEnsuingCauseOfLossExceptionsFactors` are header-only in every FL and NY package, so
    ISO has no factor there. New `TBL - Cyber` expands both tables per state from each state's
    latest package (no rows for FL / NY); every Cyber factor row looks up its own state and
    group, and a state with no row gets 1. Property damage uses the Sublimit row when a
    property-damage sublimit is entered; Business Income is always Full Limit (S-5)."""
    import csv
    CWT = w11.CW
    excl_cw = w11.read_csv(CWT / "CyberIncidentExclusionFactors.RateTable.csv")
    col_cw = w11.read_csv(CWT / "CyberIncidentExclusionWithEnsuingCauseOfLossExceptionsFactors.RateTable.csv")
    ex, cx, none = [("Key", "Factor")], [("Key", "Factor")], []
    for st in w11.states(wb):
        rows = {}
        for table, cw, out, keyf in (
                ("CyberIncidentExclusionFactors", excl_cw, ex, lambda r, st=st: (f"{st}|{r[1]}", float(r[2]))),
                ("CyberIncidentExclusionWithEnsuingCauseOfLossExceptionsFactors", col_cw, cx,
                 lambda r, st=st: (f"{st}|{r[1]}|{r[2]}|{r[3]}", float(r[4])))):
            f = w11.state_file(st, table)
            filed = w11.read_csv(f) if f else None
            rows[table] = filed
            if filed is not None and not filed:
                continue                                      # header-only: ISO has no factor
            out.extend(keyf(r) for r in (filed or cw))
        if all(v is not None and not v for v in rows.values()):
            none.append(st)
        elif any(v is not None and not v for v in rows.values()):
            raise Gate(f"{st}: only one of the two Cyber tables is header-only -- decide before building")
    ws = w11.new_sheet(wb, "TBL - Cyber")
    w11.write_rows(ws, 1, 1, ex)
    w11.write_rows(ws, 1, 4, cx)
    ws.Range("G1").Value = "Source"
    ws.Range("G2").Value = ("ISO ERC CF CyberIncidentExclusionFactors (A:B) and CyberIncidentExclusionWith"
                            "EnsuingCauseOfLossExceptionsFactors (D:E), each state's latest package. Header-only "
                            f"(ISO has no Cyber factor; the rater applies none): {', '.join(none)}")
    TA, TD = f"'TBL - Cyber'!$A$2:$B${len(ex)}", f"'TBL - Cyber'!$D$2:$E${len(cx)}"
    agg = f"IF({POL}!$F$6>0,\"Yes\",\"No\")"
    prop_type = f"IF({POL}!$F$5>0,\"Sublimit\",\"Full Limit\")"

    def excl(st, g):
        return f"=IF({POL}!$F$3=\"Yes\",IFERROR(VLOOKUP({st}&\"|{g}\",{TA},2,FALSE),1),1)"

    def colx(st, g, typ):
        return (f"=IF({POL}!$F$4<>\"Yes\",1,IFERROR(VLOOKUP({st}&\"|{g}|\"&{typ}&\"|\"&{agg},"
                f"{TD},2,FALSE),1))")

    br, cr, bi, sc = (wb.Worksheets(s) for s in (BR, CR, BI, SCC))
    n = 0
    for c in COLS:
        X = colname(c)
        bst = f"'{w11.CS}'!{X}$2"
        bist = f"INDEX('{w11.CS}'!$C$2:${w11.AP}$2,1,{X}$81)"
        sst = w11.sc_state(X)
        sbst = f"INDEX('{w11.SCH}'!$C$5:$C$44,INDEX($C$163:${w11.AP}$163,1,{X}$168))"
        par = lambda r, k: f"=INDEX('{BR}'!$C${r}:${w11.AP}${r},1,{X}${k})"  # noqa: E731
        cells = []
        for g, (er, cr_) in zip(GROUPS, ((30, 31), (60, 61), (84, 85), (110, 111))):
            cells += [(br, er, excl(bst, g)), (br, cr_, colx(bst, g, prop_type))]
        for er, cr_, ber, bcr in ((28, 29, 30, 31), (56, 57, 60, 61), (79, 80, 84, 85), (107, 108, 110, 111)):
            cells += [(cr, er, par(ber, 116)), (cr, cr_, par(bcr, 116))]
        for g, (er, cr_, ber) in zip(GROUPS, ((23, 24, 30), (43, 44, 60), (57, 58, 84), (73, 74, 110))):
            cells += [(bi, er, par(ber, 81)), (bi, cr_, colx(bist, g, '"Full Limit"'))]
        for g, (er, cr_) in zip(GROUPS, ((20, 21), (44, 45), (63, 64), (84, 85))):
            cells += [(sc, er, excl(sst, g)), (sc, cr_, colx(sst, g, prop_type))]
        for g, (er, cr_, src) in zip(GROUPS, ((103, 104, 20), (124, 125, 44), (138, 139, 63), (155, 156, 84))):
            cells += [(sc, er, f"=INDEX(${'C'}${src}:${w11.AP}${src},1,{X}$168)"),
                      (sc, cr_, colx(sbst, g, '"Full Limit"'))]
        for ws_, r, f in cells:
            ws_.Cells(r, c).Formula = f
            n += 1
    return (f"CY: TBL - Cyber ({len(ex) - 1} / {len(cx) - 1} rows; none for {none}); {n} Cyber factor "
            f"cells look up their own state and group"), {BR, CR, BI, SCC}


AK_AREAS = ("Bristol Bay", "Gateway", "Greater Anchorage Area", "Greater Juneau", "Greater Sitka",
            "Kenai Peninsula", "Kodiak Island", "Matanuska Susitna", "North Star", "Remainder of State")


def fix_ak(app, wb):
    """D-1a, user decision 2026-09-23. ISO Alaska never reads a district: it takes the ISO
    RATING AREA (`City`) and, for Remainder of State only, whether the location is east of
    the 141st meridian (`BasicGroupIDistrictTerritory`), looks up RatingTerrGroupICodeAK, and
    rates District I for 020 / 040 / 050 / 100 (Gateway, Greater Juneau, Greater Sitka,
    Remainder of State + Yes), District II otherwise. New Schedule inputs O / P; column H
    derives Alaska's district from them (`TBL - AKRatingArea`, from AK's latest package), and
    the ZIP lookup is retired for AK. A blank area gives "Select", which blocks (Diagnostics
    trap 7) instead of guessing. Must not move today's AK premium: the test location (Haines,
    99827, southeast Alaska, east of the meridian) is entered as Remainder of State + Yes,
    which is District I -- what the ZIP mapping gave."""
    ed_ws = wb.Worksheets("TBL - Editions")
    ed_row = next(r for r in range(2, 60) if ed_ws.Range(f"A{r}").Value == "AK")
    edition = ed_ws.Range(f"B{ed_row}").Value                  # the edition the rater rates AK on
    pkg = next(w11.ISO.parent.glob(f"*/{edition}"), None)
    if pkg is None:
        raise Gate(f"AK edition {edition!r} (TBL - Editions) not found on disk")
    code_f = pkg / "Rate Tables" / "RatingTerrGroupICodeAK.RateTable.csv"
    dom_f = pkg / "Domain Tables" / "DomainDistrictAlaska.DomainTable.csv"
    codes = {(r[1], r[2]): r[3] for r in w11.read_csv(code_f)}
    dist = {(r[1], r[2]): r[4] for r in w11.read_csv(dom_f)}
    if set(codes) != set(dist) or {a for a, _ in codes} != set(AK_AREAS):
        raise Gate(f"AK package tables disagree with the expected 10 areas: {sorted(codes)}")
    rows = [("Key", "RatingArea", "EastOf141st", "Code", "District")]
    rows += [(f"{a}|{e}", a, e, codes[(a, e)], dist[(a, e)]) for a, e in sorted(codes)]
    ws = w11.new_sheet(wb, "TBL - AKRatingArea")
    w11.write_rows(ws, 1, 1, rows)
    w11.write_rows(ws, 1, 7, [("RatingAreaList",)] + [(a,) for a in AK_AREAS] + [("Not Applicable",)])
    ws.Range("I1").Value = "Source"
    ws.Range("I2").Value = (f"ISO ERC {code_f.parent.parent.name}: RatingTerrGroupICodeAK (Code) and "
                            "DomainDistrictAlaska (District). EastOf141st is ISO's BasicGroupIDistrictTerritory "
                            "(East of the 141st meridian of West longitude), asked for Remainder of State only.")
    T = f"'TBL - AKRatingArea'!$A$2:$E${len(rows)}"
    sch = wb.Worksheets(w11.SCH)
    if any(str(sch.Range(a).Formula) for a in ("O4", "P4")) or \
            any(c.Formula for c in sch.Range("O5:P44")):
        raise Gate("Schedule O4:P44 is not free")
    sch.Range("N4:N44").Copy(sch.Range("O4:P44"))              # header / cell formats
    sch.Range("O5:P44").ClearContents()
    sch.Range("O4").Value, sch.Range("P4").Value = "AKRatingArea", "AKEastOf141st"
    for rng, f1 in ((sch.Range("O5:O44"), f"='TBL - AKRatingArea'!$G$2:$G${len(AK_AREAS) + 2}"),
                    (sch.Range("P5:P44"), "Yes,No,Not Applicable")):
        rng.Validation.Delete()
        rng.Validation.Add(Type=3, AlertStyle=1, Operator=1, Formula1=f1)
    n = 0
    for r in range(5, 45):
        st = sch.Range(f"C{r}").Value
        if st == "AK":
            sch.Range(f"O{r}").Value, sch.Range(f"P{r}").Value = "Remainder of State", "Yes"
        elif st not in (None, "", "State"):
            sch.Range(f"O{r}").Value = sch.Range(f"P{r}").Value = "Not Applicable"
        f = str(sch.Range(f"H{r}").Formula)
        old = f"VLOOKUP($D{r},'TBL - BGI Territories'!$K$2:$M$274,3,FALSE)"
        if old not in f:
            if f.startswith("="):
                raise Gate(f"Schedule H{r} has a formula without the AK ZIP lookup: {f!r}")
            continue                                      # a typed district (CA test row): leave it
        new = (f"IF(OR($O{r}=\"\",$O{r}=\"Not Applicable\"),\"Select\",IFERROR(VLOOKUP($O{r}&\"|\"&"
               f"IF($O{r}=\"Remainder of State\",$P{r},\"Not Applicable\"),{T},5,FALSE),\"Select\"))")
        sch.Range(f"H{r}").Formula = f.replace(old, new)
        n += 1
    dg = wb.Worksheets("OUT - Diagnostics")
    if any(dg.Range(f"{c}19").Formula for c in "ABCD"):
        raise Gate("Diagnostics row 19 is not free")
    S = f"'{w11.SCH}'!"
    cnt = (f"SUMPRODUCT(({S}$B$5:$B$44=\"Yes\")*({S}$C$5:$C$44=\"AK\")*({S}$H$5:$H$44=\"Select\"))")
    dg.Range("A19").Value = 7
    dg.Range("B19").Value = "Every active Alaska location has an ISO rating area"
    dg.Range("C19").Formula = f"=IF({cnt}=0,\"ok\",\"BLOCK - \"&{cnt}&\" Alaska location(s) have no rating area\")"
    dg.Range("D19").Value = ("Pick ISO Rating Area (col O) on IN - Schedule; for Remainder of State also answer "
                             "East of 141st Meridian (col P). ISO derives the district from these, not the ZIP")
    for rng in (dg.Range("C28"), ed_ws.Range(f"F{ed_row}")):
        if str(rng.Formula).startswith("="):
            raise Gate(f"{rng.Worksheet.Name}!{rng.Address} is a formula; not editing it blind")
    dg.Range("C28").Value = ("NY a built shortcut. AK fixed 2026-09-23 (D-1a): district derived from ISO rating "
                             "area + east-of-141st, as ISO does. CA district is user-picked")
    ed_ws.Range(f"F{ed_row}").Value = ("District split (BasicGroupIDistrictI/II), derived from ISO Rating Area + "
                                       "East of 141st on IN - Schedule O / P, as ISO does (D-1a, 2026-09-23)")
    return (f"AK: TBL - AKRatingArea ({len(rows) - 1} rows); Schedule O/P inputs + dropdowns; {n} District "
            f"formulas derive AK from them; Diagnostics trap 7"), set()


NYC_CODES = ("030", "240", "310", "410", "430")


def fix_ny(app, wb):
    """D-1b + W-23, user decision 2026-09-23. ISO New York takes the Group I territory code
    from (City, County), falling back to (Remainder of State, County); the five borough
    counties -- Bronx 030, Kings 240, New York 310, Queens 410, Richmond 430 -- rate from
    `BasicGroupIRateNYC`, all else from `BasicGroupIRate`. The rater had no County and took
    NYC from the Group I territory dropdown. And in those five territories NY's
    `SetProtectionClassFactor` (Structure; PersonalProperty reads the Structure's territory)
    gives 1.0 instead of looking the factor up. New Schedule input Q `County` (NY's 62
    counties, from ISO's DomainCountyState); column H derives NY's district from it;
    CoreScratchpad 22 reads H; Bldg Rating 8 = 1 in NYC (Contents / BI borrow row 8)."""
    ed_ws = wb.Worksheets("TBL - Editions")
    ed_row = next(r for r in range(2, 60) if ed_ws.Range(f"A{r}").Value == "NY")
    edition = ed_ws.Range(f"B{ed_row}").Value
    pkg = next(w11.ISO.parent.glob(f"*/{edition}"), None)
    if pkg is None:
        raise Gate(f"NY edition {edition!r} (TBL - Editions) not found on disk")
    counties = [r[2] for r in w11.read_csv(pkg / "Domain Tables" / "DomainCountyState.DomainTable.csv") if r[0] == "NY"]
    codes = {r[2]: r[3] for r in w11.read_csv(pkg / "Rate Tables" / "RatingTerrGroupICode.RateTable.csv")
             if r[1] == "Remainder of State"}
    boroughs = sorted(c for c, k in codes.items() if k in NYC_CODES)
    if boroughs != ["Bronx", "Kings", "New York", "Queens", "Richmond"] or len(counties) != 62:
        raise Gate(f"NY package disagrees with the expected boroughs / 62 counties: {boroughs}, {len(counties)}")
    rows = [("County", "RemainderCode", "NYDistrict")]
    rows += [(c, codes.get(c, ""), "New York City" if c in boroughs else "All Other") for c in counties]
    rows += [("Not Applicable", "", "")]
    ws = w11.new_sheet(wb, "TBL - NYCounty")
    w11.write_rows(ws, 1, 1, rows)
    ws.Range("E1").Value = "Source"
    ws.Range("E2").Value = (f"ISO ERC {edition}: DomainCountyState (NY) and RatingTerrGroupICode (Remainder of State "
                            f"rows). NYC = {', '.join(boroughs)} (codes {', '.join(NYC_CODES)}) -> BasicGroupIRateNYC "
                            "and no protection-class factor (SetProtectionClassFactor)")
    T = f"'TBL - NYCounty'!$A$2:$C${len(rows) - 1}"
    sch = wb.Worksheets(w11.SCH)
    if str(sch.Range("Q4").Formula) or any(c.Formula for c in sch.Range("Q5:Q44")):
        raise Gate("Schedule Q4:Q44 is not free")
    sch.Range("N4:N44").Copy(sch.Range("Q4:Q44"))
    sch.Range("Q5:Q44").ClearContents()
    sch.Range("Q4").Value = "County"
    q = sch.Range("Q5:Q44")
    q.Validation.Delete()
    q.Validation.Add(Type=3, AlertStyle=1, Operator=1, Formula1=f"='TBL - NYCounty'!$A$2:$A${len(rows)}")
    n = 0
    for r in range(5, 45):
        st = sch.Range(f"C{r}").Value
        if st == "NY":
            sch.Range(f"Q{r}").Value = "Kings"                    # test location: Brooklyn 11236
        elif st not in (None, "", "State"):
            sch.Range(f"Q{r}").Value = "Not Applicable"
        f = str(sch.Range(f"H{r}").Formula)
        old = (f"IFERROR(INDEX('TBL - BGI Territories'!$I$2:$I$6,MATCH($G{r},'TBL - BGI Territories'!$H$2:$H$6,0)),"
               f"\"All Other\")")
        if old not in f:
            if f.startswith("="):
                raise Gate(f"Schedule H{r} has a formula without the NY district branch: {f!r}")
            continue
        new = (f"IF(OR($Q{r}=\"\",$Q{r}=\"Not Applicable\"),\"Select\",IFERROR(VLOOKUP($Q{r},{T},3,FALSE),\"Select\"))")
        sch.Range(f"H{r}").Formula = f.replace(old, new)
        n += 1
    cs, br = wb.Worksheets(w11.CS), wb.Worksheets(BR)
    for c in COLS:
        X = colname(c)
        cs.Cells(22, c).Formula = f"=INDEX('{w11.SCH}'!$H$5:$H$44,{X}$285)"
        f8 = str(br.Cells(8, c).Formula)
        if not f8.startswith("=IF('CALC - CoreScratchpad'!"):
            raise Gate(f"Bldg Rating {X}8 is not the expected ProtClassFactor formula: {f8!r}")
        br.Cells(8, c).Formula = (f"=IF(AND('{w11.CS}'!{X}$2=\"NY\",'{w11.CS}'!{X}$22=\"New York City\"),1,"
                                  f"{f8[1:]})")
        n += 2
    dg = wb.Worksheets("OUT - Diagnostics")
    if any(dg.Range(f"{c}20").Formula for c in "ABCD") and dg.Range("A20").Value != "3. ADJUDICATED":
        raise Gate("Diagnostics row 20 unexpected")
    # trap 7 took row 19; insert row 20 for trap 8 (section 3 and everything below shift down one)
    dg.Rows(20).Insert()
    S = f"'{w11.SCH}'!"
    cnt = f"SUMPRODUCT(({S}$B$5:$B$44=\"Yes\")*({S}$C$5:$C$44=\"NY\")*({S}$H$5:$H$44=\"Select\"))"
    dg.Range("A20").Value = 8
    dg.Range("B20").Value = "Every active New York location has a county"
    dg.Range("C20").Formula = f"=IF({cnt}=0,\"ok\",\"BLOCK - \"&{cnt}&\" New York location(s) have no county\")"
    dg.Range("D20").Value = ("Pick County (col Q) on IN - Schedule. ISO rates the five NYC boroughs from the NYC table "
                             "with no protection-class factor, and everything else from the regular table")
    c28 = dg.Range("C29")                                        # D-1 row, shifted by the insert
    if not str(c28.Value or "").startswith("NY a built shortcut"):
        raise Gate(f"Diagnostics D-1 text not where expected: {c28.Value!r}")
    c28.Value = ("AK (D-1a) and NY (D-1b) fixed 2026-09-23: districts derived from ISO rating area / county as ISO "
                 "does. CA district is user-picked. NY territory FACTOR still comes from the Group I dropdown")
    if str(ed_ws.Range(f"F{ed_row}").Formula).startswith("="):
        raise Gate("TBL - Editions NY note is a formula")
    ed_ws.Range(f"F{ed_row}").Value = ("District split (NYC) derived from County, IN - Schedule Q, as ISO does: 5 boroughs -> "
                                       "NYC table, no protection-class factor (D-1b / W-23, 2026-09-23). Special "
                                       "Class BGI base rate deviates from CW on 84 values")
    return (f"NY: TBL - NYCounty ({len(rows) - 1} rows); Schedule Q County + dropdown; {n} cells (H, "
            f"CoreScratchpad 22, Bldg 8); Diagnostics trap 8"), {BR, w11.CR, BI}


#: CoreScratchpad rows R-8 never widened past record 10 (M..AP blank) that something reads
W24_LIVE = (140, 173, 180, 181, 208, 210, 211)


def fix_w24(app, wb):
    """W-24 (found by the RC-1 column audit + clone test, 2026-09-23): R-8 widened the calc
    sheets from 10 records to 40, but seven live CoreScratchpad rows kept only columns C..L.
    A record in slots 11-40 then read blanks: Contents Group I deductible factor 0 (row 140 ->
    142), Contents Special base rate 0 (173), the $250 contents factor (180 / 181), BI Special
    base rate and theft factor 0 (208 / 210 / 211) -- $0 premiums. Each row now holds column
    C's formula in every column (identical in R1C1: none of them reads a per-record Schedule
    cell). Also Special Class rows 32 / 50 read `'IN - Policy'!C3` RELATIVE in every column;
    now `$C$3` (same cell, same value, copy-safe). Twelve other drifted rows have no readers
    (consumer scan) and are left alone."""
    cs = wb.Worksheets(w11.CS)
    n = 0
    for r in W24_LIVE:
        base = cs.Cells(r, 3).FormulaR1C1
        if not str(base).startswith("="):
            raise Gate(f"CoreScratchpad C{r} has no formula")
        filled = [str(cs.Cells(r, c).FormulaR1C1) for c in range(3, 13)]
        if any(f != base for f in filled):
            raise Gate(f"CoreScratchpad row {r}: columns C..L disagree -- not a plain widening")
        cs.Range(cs.Cells(r, 13), cs.Cells(r, 42)).FormulaR1C1 = base
        n += 30
    sc = wb.Worksheets(SCC)
    for r in (32, 50):
        for c in COLS:
            f = str(sc.Cells(r, c).Formula)
            if "'IN - Policy'!C3" not in f:
                raise Gate(f"Special Class {colname(c)}{r} lacks the relative Policy reference: {f!r}")
            sc.Cells(r, c).Formula = f.replace("'IN - Policy'!C3", "'IN - Policy'!$C$3")
            n += 1
    return f"W-24: {n} cells -- 7 CoreScratchpad rows widened to 40 records; SC 32/50 Policy ref absolute", set()


def fix_cyny(app, wb):
    """CY-NY (correction to CY, 2026-09-23). New York files both Cyber tables header-only, but
    unlike Florida it OVERRIDES the rules: `SetCyberIncidentExclusionFactor*` = 1.0, and the
    ensuing-causes-of-loss exceptions factor (Group I / II / Broad / Special; property, Business
    Income and Extra Expense alike) comes from NY's own one-row
    `CyberIncidentExclusionWithEnsuingCauseOfLossExceptionsFactorNY` (1.005), whatever the type of
    limit. Live ISO rates NY with both Cyber records. Adds NY rows to `TBL - Cyber`, inserted
    inside the table so every lookup range extends; the payload then sends NY's Cyber records."""
    ed_ws = wb.Worksheets("TBL - Editions")
    ed_row = next(r for r in range(2, 60) if ed_ws.Range(f"A{r}").Value == "NY")
    pkg = next(w11.ISO.parent.glob(f"*/{ed_ws.Range(f'B{ed_row}').Value}"), None)
    rows = w11.read_csv(pkg / "Rate Tables" / "CyberIncidentExclusionWithEnsuingCauseOfLossExceptionsFactorNY.RateTable.csv")
    if len(rows) != 1 or rows[0][0] != "NY":
        raise Gate(f"NY exceptions table not the expected single row: {rows}")
    fac = float(rows[0][2])
    ws = wb.Worksheets("TBL - Cyber")
    if any(str(ws.Range(f"A{r}").Value or "").startswith("NY|") for r in range(2, 400)):
        raise Gate("TBL - Cyber already has NY rows")
    ex = [(f"NY|{g}", 1.0) for g in GROUPS]
    cx = [(f"NY|{g}|{t}|{a}", fac) for g in GROUPS for t in ("Full Limit", "Sublimit") for a in ("No", "Yes")]
    k = max(len(ex), len(cx))
    ws.Rows(f"3:{2 + k}").Insert()                     # inside both tables: every range reference extends
    w11.write_rows(ws, 3, 1, ex)
    w11.write_rows(ws, 3, 4, cx)
    ws.Range("G2").Value = (str(ws.Range("G2").Value) + f" NY (added 2026-09-23, CY-NY): NY files both tables "
                            f"header-only but overrides the rules -- exclusion 1.0, exceptions {fac} from "
                            "CyberIncidentExclusionWithEnsuingCauseOfLossExceptionsFactorNY. FL alone has no rows.")
    return f"CY-NY: {len(ex)} + {len(cx)} NY rows in TBL - Cyber (exclusion 1.0, exceptions {fac})", {BR, w11.CR, BI}


#: (column, first row, last row, source row whose dropdown is the pattern)
DV_GAPS = (("G", 5, 44, 5), ("I", 5, 44, 6), ("J", 5, 44, 5), ("I", 48, 87, 48))


def fix_dv(app, wb):
    """RC-1 dropdowns. Four Schedule columns had their dropdown only on the rows the test
    risks use (records 1-4; Location BGIITerr not even on record 1), so records 5-40 took typed,
    unvalidated values: Location G (BGI territory), I (BGII territory), J (Special territory),
    Building I (construction type). Each column now carries the same dropdown on all 40 rows,
    anchored to the block's first row so Excel steps the row reference down. Values untouched."""
    # FL was the one state with no `<ST>_bgiiterr` list (45 / 46 had one), so its Group II territory
    # dropdown showed nothing. Values: ISO's DomainBasicGroupIIRatingTerrFL (distinct), which equal
    # the FL keys in TBL - BldgBGIIRating. ISO cascades them by county; that needs a FL county input.
    if "FL_bgiiterr" in [x.Name for x in wb.Names]:
        raise Gate("FL_bgiiterr already exists")
    fl_pkg = next(w11.ISO.parent.glob("*/CF FL 20241201 V01"))
    fl = sorted({r[2] for r in w11.read_csv(fl_pkg / "Domain Tables" / "DomainBasicGroupIIRatingTerrFL.DomainTable.csv")})
    t = wb.Worksheets("TBL - BGIITerritory")
    last_row = max(r for r in range(2, 200) if t.Range(f"A{r}").Value not in (None, ""))
    if any(t.Range(f"{c}{r}").Value not in (None, "") for c in "AB" for r in range(last_row + 1, last_row + 1 + len(fl))):
        raise Gate("TBL - BGIITerritory A:B below the list is not free")
    w11.write_rows(t, last_row + 1, 1, [("FL", v) for v in fl])
    wb.Names.Add(Name="FL_bgiiterr", RefersTo=f"='TBL - BGIITerritory'!$B${last_row + 1}:$B${last_row + len(fl)}")
    sch = wb.Worksheets(w11.SCH)
    n = 0
    for col, top, last, src in DV_GAPS:
        # Copy the source row's dropdown down the column (Excel adjusts the relative row itself).
        # Validation.Add evaluates the list source on the anchor row and refuses when it errors:
        # record 1 is FL, and there is no FL_bgiiterr list, so Add failed for column I.
        sch.Range(f"{col}{src}").Copy()
        for a, b in ((top, src - 1), (src + 1, last)):
            if a <= b:
                sch.Range(f"{col}{a}:{col}{b}").PasteSpecial(Paste=6)      # xlPasteValidation
        app.CutCopyMode = False
        n += last - top + 1
    return f"DV: dropdowns on all 40 rows for {len(DV_GAPS)} Schedule columns ({n} cells)", set()


def fix_z(app, wb):
    """RC-1: make ISO's filed ZERO factors visible (backlog Z-2, Z-3; Z-1 is trap 3).
    Z-2: Special Class BI vandalism -- when the exclusion gate passes and the class code is blank,
    ISO's VandalismExclFactor is 0.0; the rater reproduces it (Special Class row 198), so a trap
    BLOCKs any active SC BI record with that factor at 0. Z-3: BI type of risk "Educational
    Institutions" (or "Combined Educational ...") -- ISO's TypeOfRiskFactor is 0 unless the
    Changes - Educational Institutions endorsement (with a month count) is attached; the rater
    does not model that endorsement and prices from its table, so the trap WARNs."""
    dg = wb.Worksheets("OUT - Diagnostics")
    if dg.Range("A21").Value != "3. ADJUDICATED" or dg.Range("A20").Value != 8:
        raise Gate(f"Diagnostics rows 20/21 not as expected: {dg.Range('A20').Value!r} / {dg.Range('A21').Value!r}")
    dg.Rows("21:22").Insert()
    S, SC = f"'{w11.SCH}'!", f"'{SCC}'!"
    z2 = f"SUMPRODUCT(({SC}$C$167:$AP$167=\"Yes\")*({SC}$C$198:$AP$198=0))"
    z3 = f"SUMPRODUCT(({S}$C$177:$C$216=\"Yes\")*ISNUMBER(SEARCH(\"Educational\",{S}$E$177:$E$216)))"
    dg.Range("A21").Value, dg.Range("A22").Value = 9, 10
    dg.Range("B21").Value = "Special Class BI vandalism factor is not zero (ISO's blank-class-code zero, Z-2)"
    dg.Range("C21").Formula = f"=IF({z2}=0,\"ok\",\"BLOCK - \"&{z2}&\" SC BI record(s) price at $0\")"
    dg.Range("D21").Value = ("The vandalism exclusion applies but the Special Class code is blank, so ISO's factor is 0.0. "
                             "Pick the Special Class description so it resolves to a class code")
    dg.Range("B22").Value = "No Business Income risk is an educational institution (Z-3)"
    dg.Range("C22").Formula = (f"=IF({z3}=0,\"ok\",\"WARN - \"&{z3}&\" educational BI record(s): ISO prices $0 "
                               f"without the Changes - Educational Institutions endorsement\")")
    dg.Range("D22").Value = ("ISO's TypeOfRiskFactor is 0 unless that endorsement (with a month count) is attached. "
                             "The rater doesn't model it and prices from its table, so its figure is unconfirmed")
    return "Z: Diagnostics traps 9 (Z-2, BLOCK) and 10 (Z-3, WARN)", set()


def fix_scded(app, wb):
    """RC-4 P1 (found by the 42-state run, 2026-09-23): Special Class Group I deductible factor
    (row 174) banded the item's limit in a table with NO state column (`TBL - Special Class`
    X:AB, countrywide values). ISO's `SetDeductibleFactorBasicGroupI` looks up the state's own
    `DeductibleFactor` table on TotAmtInsuranceToUse (= the item's limit), and 9 states file
    different factors: AL, CT, IA, KY, MI, NC, NJ, UT, WV all came out -20 on SC Group I (AL:
    ISO 0.99 at 513,000, rater 0.96). Row 174 now uses the per-state table the Building's own
    Group I deductible already uses (`TBL - BldgBGIRating` AX:BB), keyed on the item's state and
    limit (C175). The $250 branch is unchanged."""
    sc = wb.Worksheets(SCC)
    n = 0
    for c in COLS:
        X, r = colname(c), 217 + c
        f = str(sc.Cells(174, c).Formula)
        old = (f"SUMPRODUCT(('TBL - Special Class'!$X$2:$X$241=VALUE(SUBSTITUTE('IN - Schedule'!$N${r},\",\",\"\")))"
               f"*('TBL - Special Class'!$Y$2:$Y$241<={X}175)*('TBL - Special Class'!$Z$2:$Z$241>{X}175)"
               f"*('TBL - Special Class'!$AA$2:$AA$241=\"Basic Group I\")*'TBL - Special Class'!$AB$2:$AB$241)")
        if old not in f:
            raise Gate(f"Special Class {X}174 is not the expected deductible lookup: {f!r}")
        B = "'TBL - BldgBGIRating'!"
        new = (f"SUMPRODUCT(({B}$AX$2:$AX$6703={w11.sc_state(X)})*({B}$AY$2:$AY$6703='IN - Schedule'!$N${r})"
               f"*({B}$AZ$2:$AZ$6703<{X}175)*({B}$BA$2:$BA$6703>={X}175)*{B}$BB$2:$BB$6703)")
        sc.Cells(174, c).Formula = f.replace(old, new)
        n += 1
    return f"SCDED: {n} cells -- Special Class Group I deductible uses the item's state table", set()


def effective_date(wb) -> str:
    """The rater's policy effective date (Defaults), as YYYYMMDD: ISO picks each state's package
    in force on this date."""
    d = wb.Worksheets("Defaults")
    for r in range(1, 60):
        if d.Range(f"A{r}").Value == "EffectiveDate":
            return str(d.Range(f"B{r}").Value)[:10].replace("-", "")
    raise Gate("Defaults has no EffectiveDate")


def state_file_in_force(state, table, eff):
    """The table from the state's package IN FORCE on `eff` (latest effective date <= eff, all
    edition folders), else None (ISO then uses countrywide). `w11.state_file` takes the NEWEST
    package on disk, which includes future-dated ones (AL 20270301 on a 2026-09-22 policy)."""
    import re
    pkgs = []
    for d in w11.ISO.parent.glob(f"*/CF {state} *"):
        m = re.match(rf"CF {state} (\d{{8}}) V(\d+)", d.name)
        if m and d.is_dir() and m.group(1) <= eff:
            pkgs.append((m.group(1), int(m.group(2)), d))
    for _, _, d in sorted(pkgs, reverse=True):
        f = d / "Rate Tables" / f"{table}.RateTable.csv"
        if f.exists():
            return f
    return None


def fix_scspb(app, wb):
    """RC-4 (42-state run, 2026-09-23): the Special Class Special base rate list (`TBL - Special
    Class` CG:CJ) was built from each state's NEWEST package, future-dated ones included, so 10
    states carried a rate that is not yet in force (AL 0.039 from CF AL 20270301; ISO rates a
    2026-09-22 policy on CF AL 20260601, 0.040). Rates are rebuilt from the package in force on
    the rater's effective date; the source-table column (CJ, e.g. FL's NonResidential) is kept."""
    eff = effective_date(wb)
    t = wb.Worksheets("TBL - Special Class")
    cw_dir = w11.CW
    changed = []
    for r in range(2, 48):
        st, table = t.Range(f"CG{r}").Value, t.Range(f"CJ{r}").Value
        if not st:
            continue
        f = state_file_in_force(st, table, eff) or (cw_dir / f"{table}.RateTable.csv")
        rows = w11.read_csv(f)
        if not rows:
            raise Gate(f"{st}: {table} in {f.parent.parent.name} is header-only")
        rate = float(rows[0][2])
        old = t.Range(f"CI{r}").Value
        if abs(float(old or 0) - rate) > 1e-12:
            t.Range(f"CI{r}").Value = rate
            changed.append(f"{st} {old}->{rate} ({f.parent.parent.name})")
    t.Range("CK1").Value = "Source (RC-4)"
    t.Range("CK2").Value = (f"CI rebuilt 2026-09-23 from each state's package IN FORCE on {eff} (not the newest on "
                            f"disk). Changed: {'; '.join(changed) or 'none'}")
    print("   ", "\n    ".join(changed))
    return f"SCSPB: {len(changed)} Special Class Special base rates now from the in-force package", {SCC}


def fix_w25(app, wb):
    """RC-4 (42-state run, 2026-09-23). Two ISO rate rules round after EVERY factor and the rater
    rounded once, and the rater folded two roof factors into one.

    BI Group II (row 33) -- ISO `SetBasicGroupIIRate` (BI): ROUND(ROUND(ROUND(ROUND(base x LCM) x
    numeric) x BCEG) x adjustment). W-14R had adjustment before BCEG; AK / FL gave the same answer
    either way, VA / WV / MN / NE / RI did not (+-3 to 5).

    Building Group II (row 42) -- ISO `SetBasicGroupIIRate` (Structure): ROUND(ROUND(ROUND(ROUND(
    ROUND(base x LCM) x numeric) x roof ACV) x roof COSMETIC) x BCEG). Reproduced ISO exactly in
    AL / CT / MI / UT (the rater's single ROUND was -7 to +21). ISO's roof factors
    (`SetLimitationsOnCovForRoofSurfacing*`): ACV = the paragraph's factor for Paragraph A or A and B,
    else 1; cosmetic = the state's Paragraph B factor for Paragraph B or A and B, else 1. Group I,
    Broad and Special use ACV only. Row 9 (the ACV factor Group I / Broad / Special read) now
    gives 1 for Paragraph B alone; row 40 becomes the cosmetic factor (was a pre-multiplied
    0.9702 from the rater's old Group II table)."""
    br, bi = wb.Worksheets(BR), wb.Worksheets(BI)
    T = "'TBL - RoofSurfacing'!$A$2:$E$123"
    n = 0
    for c in COLS:
        X, b = colname(c), 45 + c
        para, st = f"'{w11.SCH}'!$Y${b}", f"'{w11.CS}'!{X}$2"
        if "'TBL - RoofSurfacing'" not in str(br.Cells(9, c).Formula) or \
                "'TBL - RoofSurfacing'" not in str(br.Cells(40, c).Formula):
            raise Gate(f"Bldg {X}9 / {X}40 are not the roof lookups")
        br.Cells(9, c).Formula = (f"=IF(OR({para}=\"Paragraph A\",{para}=\"Paragraph A and B\"),"
                                  f"IFERROR(VLOOKUP({st}&\"|\"&{para},{T},4,FALSE),1),1)")
        br.Cells(40, c).Formula = (f"=IF(OR({para}=\"Paragraph B\",{para}=\"Paragraph A and B\"),"
                                   f"IFERROR(VLOOKUP({st}&\"|Paragraph B\",{T},4,FALSE),1),1)")
        f42 = str(br.Cells(42, c).Formula)
        old = f"ROUND({X}36*{X}38*{X}39*{X}40*{X}41,3)"
        if f42.count(old) != 1:
            raise Gate(f"Bldg {X}42 lacks the single-ROUND Group II rate: {f42!r}")
        low = f"ROUND('CALC - Bldg Rating'!{X}37*'CALC - Bldg Rating'!{X}38*'CALC - Bldg Rating'!{X}40,3)"
        if f42.count(low) != 1:
            raise Gate(f"Bldg {X}42 lacks the lowest-rate branch: {f42!r}")
        # Lowest-rate branch (wind/hail excluded): ISO BasicGroupIICauseOfLossAdjustment =
        # ROUND(ROUND(ROUND(lowest x LCM) x ACV) x cosmetic) ... ; row 40 is now cosmetic only.
        br.Cells(42, c).Formula = f42.replace(
            old, f"ROUND(ROUND(ROUND(ROUND(ROUND({X}36*{X}38,3)*{X}39,3)*{X}9,3)*{X}40,3)*{X}41,3)").replace(
            low, f"ROUND(ROUND(ROUND({X}37*{X}38,3)*{X}9,3)*{X}40,3)")
        bce = f"INDEX('{BR}'!$C$41:${w11.AP}$41,1,{X}$81)"
        f33 = str(bi.Cells(33, c).Formula)
        old33 = f"ROUND(ROUND({X}29*{X}30*{X}31*{X}32,3)*{bce},3)"
        if old33 not in f33:
            raise Gate(f"BI {X}33 is not the W-14R formula: {f33!r}")
        bi.Cells(33, c).Formula = f33.replace(
            old33, f"ROUND(ROUND(ROUND(ROUND({X}29*{X}30,3)*{X}31,3)*{bce},3)*{X}32,3)")
        n += 4
    br.Range("B9").Value = "RoofSurfacingACVFactor (ISO ACV: Paragraph A / A and B; W-25)"
    br.Range("B40").Value = "RoofSurfacingCosmeticExclFactor (ISO: Paragraph B / A and B; W-25)"
    return f"W-25: {n} cells -- roof ACV / cosmetic split; Building and BI Group II rates round per ISO", {BR, BI}


def fix_scfin(app, wb):
    """RC-4 (42-state run, 2026-09-23). ISO Special Class `SetFinal{BasicGroupI,BasicGroupII,Broad,
    Special}Rate` = ROUND(ROUND(adjusted x deductible-by-location credit, 3) x deductible factor, 3).
    The rater rounded the three-way product once. AL: Group I 0.159 x 0.995 = 0.158, x 0.99 = 0.156
    (ISO) vs 0.157; Special 0.035 x 0.995 = 0.035, x 0.96 = 0.034 (ISO) vs 0.033. Only visible where a
    state grants the per-location credit (FL files none)."""
    sc = wb.Worksheets(SCC)
    n = 0
    for p in (14, 38, 57, 78):
        a, b, d = p - 3, p - 2, p - 1
        for c in COLS:
            X = colname(c)
            old = f"=ROUND({X}{a}*{X}{b}*{X}{d},3)"
            if str(sc.Cells(p, c).Formula) != old:
                raise Gate(f"Special Class {X}{p} is not {old}: {sc.Cells(p, c).Formula!r}")
            sc.Cells(p, c).Formula = f"=ROUND(ROUND({X}{a}*{X}{b},3)*{X}{d},3)"
            n += 1
    return f"SCFIN: {n} cells -- Special Class final rates round after the per-location credit", {SCC}


def fix_w26(app, wb):
    """RC-4 (CT in the 42-state run, 2026-09-23). Five states file the roof-surfacing table with ONE
    row instead of Paragraph A / B / A and B: CT, IN, NH key it "ACV", MA and WY key it "Y" (0.98).
    Their `SetLimitationsOnCovForRoofSurfacingACVFactor` applies that row whenever a roof
    limitation is present (any paragraph) and the cosmetic factor is 1.0. The rater looked up
    "<ST>|Paragraph ...", found nothing and used 1 (CT Building Group I +14, Group II +21).
    Rows 9 (ACV) / 40 (cosmetic) now use the single row when the state files one. NH's cosmetic
    rule is ambiguous in the file; treated as 1 like the others (unverified)."""
    br = wb.Worksheets(BR)
    T = "'TBL - RoofSurfacing'!$A$2:$E$123"
    n = 0
    for c in COLS:
        X, b = colname(c), 45 + c
        para, st = f"'{w11.SCH}'!$Y${b}", f"'{w11.CS}'!{X}$2"
        single = f"IFERROR(VLOOKUP({st}&\"|ACV\",{T},4,FALSE),IFERROR(VLOOKUP({st}&\"|Y\",{T},4,FALSE),\"\"))"
        anyp = f"OR({para}=\"Paragraph A\",{para}=\"Paragraph B\",{para}=\"Paragraph A and B\")"
        f9, f40 = str(br.Cells(9, c).Formula), str(br.Cells(40, c).Formula)
        if not (f9.startswith(f"=IF(OR({para}=\"Paragraph A\"") and f40.startswith(f"=IF(OR({para}=\"Paragraph B\"")):
            raise Gate(f"Bldg {X}9 / {X}40 are not the W-25 roof formulas")
        br.Cells(9, c).Formula = f"=IF(AND({anyp},{single}<>\"\"),{single},{f9[1:]})"
        br.Cells(40, c).Formula = f"=IF({single}<>\"\",1,{f40[1:]})"
        n += 2
    return f"W-26: {n} cells -- single-row roof tables (CT / IN / NH 'ACV', MA / WY 'Y')", {BR}


w11.FIXES.update(W16=fix_w16, W20=fix_w20, W21=fix_w21, CY=fix_cy, AK=fix_ak, NY=fix_ny, W24=fix_w24,
                 CYNY=fix_cyny, DV=fix_dv, Z=fix_z, SCDED=fix_scded, SCSPB=fix_scspb, W25=fix_w25, SCFIN=fix_scfin,
                 W26=fix_w26)
def fix_sctheft(app, wb):
    """RC-4 (CT in the 42-state run, 2026-09-23). Special Class row 72 hard-coded the Special theft
    exclusion factor at 0.88 (CW). ISO `SpecialBldgTheftExclusionFactor` is per state and 30 states
    file 0.91 or 0.94 (CT 0.94: Special Class Special -31). Row 72 now reads the same per-state table
    the Building's own Special theft factor uses (`TBL - BldgSpecialRating` M:O, Bldg row 93)."""
    sc = wb.Worksheets(SCC)
    n = 0
    for c in COLS:
        X, r = colname(c), 217 + c
        old = f"=IF('IN - Schedule'!$W${r}=\"Yes\",0.88,1)"
        if str(sc.Cells(72, c).Formula) != old:
            raise Gate(f"Special Class {X}72 is not {old}: {sc.Cells(72, c).Formula!r}")
        sc.Cells(72, c).Formula = (f"=IF('IN - Schedule'!$W${r}=\"Yes\",IFERROR(VLOOKUP({w11.sc_state(X)},"
                                   f"'TBL - BldgSpecialRating'!$M$2:$O$47,3,FALSE),1),1)")
        n += 1
    return f"SCTHEFT: {n} cells -- Special Class Special theft factor per state", {SCC}


def fix_edcasc(app, wb):
    """RC-4 ED-CA-SC (2026-09-24), three parts, each traced against ISO's files and a live CA probe.

    1. **Edition.** `TBL - Special Class` BA:BE (Group II deductible), CA:CE (Other Cause Of Loss
       deductible) and BK:BO (wind/hail %) held CA's FUTURE filing (CF CA 20261001 / 20261101).
       CA's in-force package (CF CA 20251201 V01) files neither table, so ISO uses countrywide.
       CA's rows are rewritten from CW; left-over CA rows are blanked.
    2. **Schedule defaults.** Special Class rows 220-229 read Deductible = policy THEFT deductible,
       WindHailDed = the item's Deductible, TheftDed = the item's WindHailDed (shifted by one).
       Now Deductible / WindHail / Theft = `IN - Policy` C8 / C9 / C10, as the Building rows.
    3. **Special deductible (row 191/194).** ISO `SetDeductibleFactorSpecial` (Special Class) uses
       TheftDeductible only when theft is covered and it differs from Deductible (and is not 250 /
       Not Applicable); otherwise Deductible. The rater always used TheftDed -- the CA probe with a
       1% wind/hail deductible priced Special at $0 (ISO $32)."""
    import csv
    t = wb.Worksheets("TBL - Special Class")
    cw = w11.CW
    ded = list(csv.reader(open(cw / "DeductibleFactor.RateTable.csv", encoding="utf-8-sig")))[1:]
    wind = list(csv.reader(open(cw / "WindstormOrHailDeductibleFactor.RateTable.csv", encoding="utf-8-sig")))[1:]

    def rewrite(state_col, width, rows, top, bottom):
        have = [r for r in range(top, bottom + 1) if t.Range(f"{state_col}{r}").Value == "CA"]
        if not have or have != list(range(have[0], have[-1] + 1)):
            raise Gate(f"CA rows in {state_col} are not one contiguous run: {have[:3]}...")
        if len(rows) > len(have):
            raise Gate(f"{state_col}: {len(rows)} CW rows do not fit in {len(have)} CA rows")
        first = t.Range(f"{state_col}1").Column
        for i, r in enumerate(have):
            vals = rows[i] if i < len(rows) else [None] * width
            for j, v in enumerate(vals):
                t.Cells(r, first + j).Value = v
        return len(have), len(rows)

    g2 = [["CA", "'" + x[1], float(x[2]), float(x[3]), float(x[5])] for x in ded if x[4] == "Basic Group II"]
    oc = [["CA", float(x[1].replace(",", "")), float(x[2]), float(x[3]), float(x[5])]
          for x in ded if x[4] == "Other Cause Of Loss"]
    wh = [["CA", float(x[1].rstrip("%")) / 100, float(x[2]), float(x[3]), float(x[4])] for x in wind]
    notes = [f"BA {rewrite('BA', 5, g2, 2, 6776)}", f"CA {rewrite('CA', 5, oc, 2, 6744)}",
             f"BK {rewrite('BK', 5, wh, 2, 1100)}"]

    sch = wb.Worksheets(w11.SCH)
    for r in range(220, 230):
        want = {"N": "='IN - Policy'!$C$10", "S": f"='IN - Schedule'!$N${r}", "T": f"='IN - Schedule'!$S${r}"}
        for col, old in want.items():
            if str(sch.Range(f"{col}{r}").Formula) != old:
                raise Gate(f"Schedule {col}{r} is not {old}: {sch.Range(f'{col}{r}').Formula!r}")
        sch.Range(f"N{r}").Formula = "='IN - Policy'!$C$8"
        sch.Range(f"S{r}").Formula = "='IN - Policy'!$C$9"
        sch.Range(f"T{r}").Formula = "='IN - Policy'!$C$10"

    sc = wb.Worksheets(SCC)
    n = 0
    for c in COLS:
        X, r = colname(c), 217 + c
        N, T, W = (f"'IN - Schedule'!${k}${r}" for k in "NTW")
        old191 = (f"=IF(OR({T}=\"\",{T}=\"Not Applicable\"),0,IFERROR(VALUE(SUBSTITUTE({T},\",\",\"\")),0))")
        old194 = (f"=IF({T}=\"250\",{X}193,IF({T}=\"Not Applicable\",1,IF({T}=\"\",0,{X}192)))")
        if str(sc.Cells(191, c).Formula) != old191 or str(sc.Cells(194, c).Formula) != old194:
            raise Gate(f"Special Class {X}191 / {X}194 are not the expected theft-deductible formulas")
        use_t = f"AND({W}<>\"Yes\",{T}<>\"\",{T}<>\"Not Applicable\",{T}<>\"250\",{T}<>{N})"
        sc.Cells(191, c).Formula = (f"=IF({use_t},IFERROR(VALUE(SUBSTITUTE({T},\",\",\"\")),0),"
                                    f"IF(OR({N}=\"\",{N}=\"Not Applicable\"),0,IFERROR(VALUE(SUBSTITUTE({N},\",\",\"\")),0)))")
        sc.Cells(194, c).Formula = (f"=IF(OR({N}=\"250\",{T}=\"250\"),{X}193,IF({N}=\"Not Applicable\",1,"
                                    f"IF({N}=\"\",0,{X}192)))")
        n += 2
    return (f"ED-CA-SC: CA rows -> CW ({'; '.join(notes)} [CA rows, CW rows]); Special Class defaults "
            f"rows 220-229 -> C8/C9/C10; {n} Special deductible cells"), set()


def fix_roofrnd(app, wb):
    """RC-4 NH-COS probe (2026-09-24). NH, Paragraph B: ISO applied the 0.98 ACV roof factor exactly
    as the rater does (W-26), but Building Group I was Excel 1932 vs ISO 1881 -- ISO rounds after
    the roof factor and the rater did not. ISO `SetBasicGroupIRate` (Class):
    ROUND(ROUND((ROUND(base x LCM,3) + substd + vacant) x terr x PC,3) x ACV,3); Specific:
    ROUND(ROUND(specific x LCM,3) x ... x ACV,3). `SetAdjustedBroadRate`: ROUND(ROUND(ROUND(broad x ACV)
    x coins) x LOI). `SetSpecialCauseOfLossAdjustment`: ROUND(ROUND(special x theft) x ACV).
    Rows 10 / 72 / 95 each rounded once. Premium-neutral wherever ACV = 1."""
    br = wb.Worksheets(BR)
    n = 0
    for c in COLS:
        X = colname(c)
        cs = f"'CALC - CoreScratchpad'!{X}"
        old = {10: f"=IF({cs}277<>\"Yes\",0,IFERROR(ROUND((({X}3*{X}4)+{X}5+{X}6)*{X}7*{X}8*{X}9,3),0))",
               72: f"=ROUND({X}68*{X}69*{X}70*{X}71,3)",
               95: f"=ROUND({X}92*{X}93*{X}94,3)"}
        for r, f in old.items():
            if str(br.Cells(r, c).Formula) != f:
                raise Gate(f"Bldg {X}{r} is not {f!r}: {br.Cells(r, c).Formula!r}")
        br.Cells(10, c).Formula = (f"=IF({cs}277<>\"Yes\",0,IFERROR(IF({cs}6=\"No\","
                                   f"ROUND(ROUND({X}3*{X}4,3)*{X}7*{X}8*{X}9,3),"
                                   f"ROUND(ROUND((ROUND({X}3*{X}4,3)+{X}5+{X}6)*{X}7*{X}8,3)*{X}9,3)),0))")
        br.Cells(72, c).Formula = f"=ROUND(ROUND(ROUND({X}68*{X}70,3)*{X}69,3)*{X}71,3)"
        br.Cells(95, c).Formula = f"=ROUND(ROUND({X}92*{X}93,3)*{X}94,3)"
        n += 3
    return f"ROOFRND: {n} cells -- Building Group I / Broad / Special round after the roof ACV factor", {BR}


def fix_thded(app, wb):
    """RC-4 TH-DED (2026-09-24). The rater had NO live theft-deductible logic: Building and Contents
    Special always used `Deductible` (CoreScratchpad 125); Contents 160-165 were dead rows.
    ISO `SetDeductibleFactorSpecial` (Structure and PersonalProperty, CW):
      - theft covered (own SpecialTheftExclusionIndicator = 0) and TheftDeductible not "", Not
        Applicable, 250 and <> Deductible -> LookupDeductibleFactor(TheftDeductible,
        SpecialIncludingTheftTotAmtInsurance, "Other Cause Of Loss");
      - Deductible = 250 or TheftDeductible = 250 -> the $250 factor;
      - else LookupDeductibleFactor(Deductible, ...).
    SpecialIncludingTheftTotAmtInsurance = the structure's limit when it is Special with theft
    covered + its occupancies' Special-including-theft contents (+ Special Class, not modelled).
    New CoreScratchpad rows 127-131 (retired R-8 rows); Bldg row 100 and Contents row 97 use them.
    The Contents check reads the CONTENTS record's own theft exclusion, as ISO does."""
    cs, br, cr = wb.Worksheets(w11.CS), wb.Worksheets(BR), wb.Worksheets("CALC - Contents Rating")
    B = "'TBL - BldgSpecialRating'!"
    labels = {127: "[TH] Special incl. theft total (ISO SpecialIncludingTheftTotAmtInsurance)",
              128: "[TH] Theft deductible row offset", 129: "[TH] Theft DeductibleFactor",
              130: "[TH] Theft deductible differs?", 131: "[TH] DeductibleFactorSpecial (theft-aware)"}
    for r, t in labels.items():
        if cs.Range(f"C{r}").Formula not in ("", None) or cs.Range(f"D{r}").Formula not in ("", None):
            raise Gate(f"CoreScratchpad row {r} is not empty")
        cs.Range(f"A{r}").Value = "TH-DED 2026-09-24"
        cs.Range(f"B{r}").Value = t
    n = 0
    for c in COLS:
        X, b = colname(c), 45 + c
        S = lambda k: f"'IN - Schedule'!${k}${b}"                       # noqa: E731
        P, Q, R, AG, N_, A = S("P"), S("Q"), S("R"), S("AG"), S("N"), S("A")
        cs.Range(f"{X}127").Formula = (f"=IF(AND({P}=\"Special\",{AG}=\"No\"),{N_},0)+IF({P}=\"Special\","
                                       f"SUMIFS('IN - Schedule'!$E$134:$E$173,'IN - Schedule'!$L$134:$L$173,{A},"
                                       f"'IN - Schedule'!$C$134:$C$173,\"Yes\",'IN - Schedule'!$K$134:$K$173,\"No\"),0)")
        cs.Range(f"{X}128").Formula = (f"=SUMPRODUCT(({B}$W$2:$W$6670=INDEX('IN - Schedule'!$C$5:$C$44,{X}$285))"
                                       f"*({B}$X$2:$X$6670={R})*({B}$Y$2:$Y$6670<{X}127)*({B}$Z$2:$Z$6670>={X}127)"
                                       f"*(ROW({B}$W$2:$W$6670)-ROW({B}$W$2)+1))")
        cs.Range(f"{X}129").Formula = f"=IF({X}128=0,0,INDEX({B}$AA:$AA,{X}128+1))"
        cs.Range(f"{X}130").Formula = (f"=AND({R}<>\"\",{R}<>\"Not Applicable\",{R}<>\"250\",{R}<>{Q})")
        cs.Range(f"{X}131").Formula = (f"=IF(OR({Q}=\"250\",{R}=\"250\"),{X}124,"
                                       f"IF(AND({AG}=\"No\",{X}130),{X}129,{X}125))")
        old100 = f"=IF('IN - Schedule'!$P${b}<>\"Special\",1,'CALC - CoreScratchpad'!{X}125)"
        if str(br.Cells(100, c).Formula) != old100:
            raise Gate(f"Bldg {X}100 is not {old100!r}: {br.Cells(100, c).Formula!r}")
        br.Cells(100, c).Formula = f"=IF('IN - Schedule'!$P${b}<>\"Special\",1,'CALC - CoreScratchpad'!{X}131)"
        k = f"'IN - Schedule'!$K${131 + c}"
        old97 = f"=INDEX('CALC - Bldg Rating'!$C$100:$AP$100,1,{X}$116)"
        if str(cr.Cells(97, c).Formula) != old97:
            raise Gate(f"Contents {X}97 is not {old97!r}: {cr.Cells(97, c).Formula!r}")
        I = lambda row: f"INDEX('CALC - CoreScratchpad'!$C${row}:$AP${row},1,{X}$116)"   # noqa: E731
        J = lambda col: f"INDEX('IN - Schedule'!${col}$48:${col}$87,{X}$116)"            # noqa: E731
        cr.Cells(97, c).Formula = (f"=IF({J('P')}<>\"Special\",1,IF(OR({J('Q')}=\"250\",{J('R')}=\"250\"),{I(124)},"
                                   f"IF(AND({k}=\"No\",{I(130)}),{I(129)},{I(125)})))")
        n += 7
    return f"TH-DED: {n} cells -- theft deductible on Building / Contents Special", {BR, "CALC - Contents Rating"}


def fix_w22(app, wb):
    """RC-4 W-22 (2026-09-24). Every premium row multiplied IRPM x package mod x MPD inside ONE ROUND.
    ISO `SetPremium` (all 20 coverage x group files, traced):
      Building BGI / BGII / Broad   one ROUND(limit x rate x IRPM x MPD x PM)          (unchanged)
      Building Special              ROUND(ROUND(ROUND(ROUND(rate x lim) x PM) x MPD) x IRPM)
      Contents all four             same chain (Special: rate x lim rounded to 3 dp first)
      Legal Liability (Bldg + Cont) ROUND(ROUND(ROUND(rate x lim) x PM) x IRPM)       no MPD
      BI BGI / Broad / Special      one ROUND(limit x rate x IRPM x PM)               no MPD
      BI BGII                       ROUND(ROUND(ROUND(rate x lim) x PM) x IRPM)       no MPD
      Special Class all four        chain PM -> MPD -> IRPM
      SC BI all four                one ROUND(limit x rate x IRPM x PM)               no MPD
    The two Cyber factors still round after, as before. Neutral while all three factors are 1."""
    import re
    sheets = {"CALC - Bldg Rating": [32, 62, 86, 112], "CALC - Contents Rating": [30, 58, 81, 109],
              "CALC - BI Rating": [25, 45, 59, 75], SCC: [22, 46, 65, 86, 105, 126, 140, 157]}
    tmpl = {}
    for s, rows in sheets.items():
        for p in rows:
            tmpl[(s, p)] = str(wb.Worksheets(s).Cells(p, 3).Formula)
    swap = lambda f, X: re.sub(r"(?<![A-Z$'])C(?=\$?\d)", X, f)          # noqa: E731
    cyb = lambda X, a, b, core: f"ROUND(ROUND({core}*{X}{a},0)*{X}{b},0)"  # noqa: E731
    R0 = lambda e: f"ROUND({e},0)"                                       # noqa: E731
    n = 0
    for c in COLS:
        X = colname(c)
        for (s, p), t in tmpl.items():
            if str(wb.Worksheets(s).Cells(p, c).Formula) != swap(t, X):
                raise Gate(f"{s}!{X}{p} does not follow column C's formula")
        # Building: base b = p-9: IRPM b, rate b+1..b+3, MPD b+4, PM b+5, limit b+6, cyber b+7/b+8
        for p in sheets["CALC - Bldg Rating"]:
            b = p - 9
            A = f"ROUND(ROUND({X}{b+1}*{X}{b+2},3)*{X}{b+3},3)*({X}{b+6}/100)"
            ll = f"'IN - Schedule'!$D${45 + c}=\"Legal Liability\""
            chain_ll = R0(f"{R0(f'{R0(A)}*{X}{b+5}')}*{X}{b}")
            if p == 112:
                other = R0(f"{R0(f'{R0(f'{R0(A)}*{X}{b+5}')}*{X}{b+4}')}*{X}{b}")
            else:
                other = R0(f"{X}{b}*{X}{b+4}*{X}{b+5}*{A}")
            wb.Worksheets("CALC - Bldg Rating").Cells(p, c).Formula = (
                f"=IF('CALC - CoreScratchpad'!{X}$284<>\"Yes\",0,"
                f"{cyb(X, b + 7, b + 8, f'IF({ll},{chain_ll},{other})')})")
            n += 1
        # Contents: b = p-9: IRPM b, MPD b+1, rate b+2..b+4, PM b+5, limit b+6, cyber b+7/b+8
        for p in sheets["CALC - Contents Rating"]:
            b = p - 9
            A = f"ROUND(ROUND({X}{b+2}*{X}{b+3},3)*{X}{b+4},3)*({X}{b+6}/100)"
            first = f"ROUND({A},3)" if p == 109 else R0(A)
            ll = f"INDEX('IN - Schedule'!$H$91:$H$130,{X}$115)=\"Legal Liability Coverage Form\""
            chain_ll = R0(f"{R0(f'{R0(A)}*{X}{b+5}')}*{X}{b}")
            chain = R0(f"{R0(f'{R0(f'{first}*{X}{b+5}')}*{X}{b+1}')}*{X}{b}")
            wb.Worksheets("CALC - Contents Rating").Cells(p, c).Formula = (
                f"=IF({X}$114<>\"Yes\",0,{cyb(X, b + 7, b + 8, f'IF({ll},{chain_ll},{chain})')})")
            n += 1
        # BI: b = p-6: rate b-1, IRPM b, MPD b+1 (dropped), PM b+2, limit b+3, cyber b+4/b+5
        for p in sheets["CALC - BI Rating"]:
            b = p - 6
            A = f"{X}{b-1}*({X}{b+3}/100)"
            core = (R0(f"{R0(f'{R0(A)}*{X}{b+2}')}*{X}{b}") if p == 45 else R0(f"{X}{b}*{X}{b+2}*{A}"))
            wb.Worksheets("CALC - BI Rating").Cells(p, c).Formula = (
                f"=IF({X}$80<>\"Yes\",0,{cyb(X, b + 4, b + 5, core)})")
            n += 1
        # Special Class / SC BI: b = p-7: limit b, rate b+1, PM b+2, MPD b+3, IRPM b+4, cyber b+5/b+6
        for p in sheets[SCC]:
            b = p - 7
            A = f"({X}{b}/100)*{X}{b+1}"
            gate = "162" if p < 100 else "167"
            if p < 100:
                core = R0(f"{R0(f'{R0(f'{R0(A)}*{X}{b+2}')}*{X}{b+3}')}*{X}{b+4}")
            else:
                core = R0(f"{A}*{X}{b+2}*{X}{b+4}")
            wb.Worksheets(SCC).Cells(p, c).Formula = f"=IF({X}${gate}<>\"Yes\",0,{cyb(X, b + 5, b + 6, core)})"
            n += 1
    return f"W-22: {n} premium cells -- ISO's modifier order, rounding and MPD scope", \
        {"CALC - Bldg Rating", "CALC - Contents Rating", "CALC - BI Rating", SCC}


def fix_scgist(app, wb):
    """RC-4 SC-GI-ST (2026-09-24). Special Class Group I rate (row 4) read only the COUNTRYWIDE
    `BasicGroupIRateSpecialClass` (`TBL - Special Class` E:I). ISO's lookups are FirstNonNull:
    the state's row, else CW -- both for `SpecialClassDescriptionConvertedOption` (description ->
    option) and for the rate (option + protection class). FL, NY and PR file their own rate tables
    in force (NY: all 189 rows differ from CW); FL also files its own option mapping (Option1..N).
    New block EI:EK = State|Description|PC -> rate for those states, built from the packages in
    force on the rater's effective date; row 4 reads it first and falls back to E:I."""
    import csv
    eff = effective_date(wb)
    t = wb.Worksheets("TBL - Special Class")
    if any(t.Range(f"{c}1").Value not in (None, "") for c in ("EI", "EJ", "EK")):
        raise Gate("TBL - Special Class EI:EK is not empty")
    rd = lambda f: list(csv.reader(open(f, encoding="utf-8-sig")))[1:]           # noqa: E731
    cw_conv = {r[1]: r[2] for r in rd(w11.CW / "SpecialClassDescriptionConvertedOption.RateTable.csv")}
    rows, src = [], []
    for st in ("FL", "NY", "PR"):
        rf = state_file_in_force(st, "BasicGroupIRateSpecialClass", eff)
        if rf is None:
            continue
        cf = state_file_in_force(st, "SpecialClassDescriptionConvertedOption", eff)
        conv = dict(cw_conv)
        conv.update({r[1]: r[2] for r in rd(cf)} if cf else {})
        rate = {}
        for r in rd(rf):
            lo, hi = (r[2].split(" to ") + [r[2]])[:2] if " to " in r[2] else (r[2], r[2])
            for pc in range(int(lo), int(hi) + 1):
                rate[(r[1], pc)] = float(r[3])
        k = 0
        for desc, opt in conv.items():
            for pc in range(1, 11):
                if (opt, pc) in rate:
                    rows.append((f"{st}|{desc}|{pc}", rate[(opt, pc)]))
                    k += 1
        src.append(f"{st}: {k} rows from {rf.parent.parent.name}"
                   f"{' + own option map' if cf else ' (CW option map)'}")
    t.Range("EI1:EK1").Value = (("Key (State|Description|PC)", "Rate", "Source (RC-4 SC-GI-ST)"),)
    t.Range(f"EI2:EJ{len(rows) + 1}").Value = tuple(rows)
    t.Range("EK2").Value = f"Built 2026-09-24 from packages in force on {eff}: " + "; ".join(src)
    last = len(rows) + 1
    sc = wb.Worksheets(SCC)
    n = 0
    for c in COLS:
        X, r = colname(c), 217 + c
        old = f"=IFERROR(VLOOKUP({X}172,'TBL - Special Class'!$E$2:$I$711,5,FALSE),0)"
        if str(sc.Cells(4, c).Formula) != old:
            raise Gate(f"Special Class {X}4 is not {old!r}: {sc.Cells(4, c).Formula!r}")
        key = f"{w11.sc_state(X)}&\"|\"&'IN - Schedule'!$D${r}&\"|\"&INDEX('IN - Schedule'!$F$5:$F$44,{X}$163)"
        sc.Cells(4, c).Formula = (f"=IFERROR(VLOOKUP({key},'TBL - Special Class'!$EI$2:$EJ${last},2,FALSE),"
                                  f"{old[1:]})")
        n += 1
    print("   ", "; ".join(src))
    return f"SC-GI-ST: {len(rows)} state rate rows; {n} cells", {SCC}


def fix_scgistfl(app, wb):
    """RC-4 SC-GI-ST follow-up (2026-09-24). FL's rows in EI:EJ came from CF FL 20241201 V01 (the only
    FL on disk). Live ISO runs V02 (ED-FL) and maps 'Swimming Pools in the Open - Above Ground (All
    Other)' to Option29b2 = 0.556 (= CW), where V01 swapped the above- / in-ground rates (0.152).
    V01 equals CW on every other description, so FL goes back to CW until V02 is on disk."""
    t = wb.Worksheets("TBL - Special Class")
    last = t.Cells(t.Rows.Count, "EI").End(-4162).Row
    vals = t.Range(f"EI2:EJ{last}").Value
    keep = tuple(r for r in vals if not str(r[0]).startswith("FL|"))
    if len(keep) == len(vals):
        raise Gate("no FL rows in EI:EJ")
    t.Range(f"EI2:EJ{last}").ClearContents()
    t.Range(f"EI2:EJ{len(keep) + 1}").Value = keep
    t.Range("EK3").Value = ("2026-09-24: FL rows removed -- live ISO runs CF FL 20241201 V02 (not on disk); "
                            "V01's swimming-pool rates are swapped vs live ISO. FL uses CW (E:I) until V02 (ED-FL).")
    return f"SC-GI-ST FL: {len(vals) - len(keep)} FL rows removed, {len(keep)} kept", {SCC}


def fix_w5(app, wb):
    """RC-2 W-5 (2026-09-24). Contents Group II coinsurance (row 43) read the BUILDING's factor.
    ISO `SetBasicGroupIICoinsuranceFactor` (PersonalProperty): the Contents record's own
    CoinsuranceFactor (Contents row 15), except 50% / 60% / 70% / None -> the flat factor
    (`BasicGroupIIFlatCoinsuranceFactor`, CW 1.5; only PR files its own). Probe
    `scenarios/rc2/w5_contents_coins_100.json`: AK Contents 100% vs Building 80%, 68 vs ISO 60."""
    cr = wb.Worksheets("CALC - Contents Rating")
    n = 0
    for c in COLS:
        X, g = colname(c), f"'IN - Schedule'!$G${131 + c}"
        old = f"=INDEX('CALC - Bldg Rating'!$C$46:$AP$46,1,{X}$116)"
        if str(cr.Cells(43, c).Formula) != old:
            raise Gate(f"Contents {X}43 is not {old!r}: {cr.Cells(43, c).Formula!r}")
        cr.Cells(43, c).Formula = f"=IF(OR({g}=0.5,{g}=0.6,{g}=0.7,{g}=\"None\"),1.5,{X}15)"
        n += 1
    return f"W-5: {n} cells -- Contents Group II coinsurance is the contents' own", {"CALC - Contents Rating"}


def fix_s2(app, wb):
    """RC-2 S-2 (2026-09-24). SC Business Income Group II (rows 109-116) borrowed the Special Class
    ITEM's base / lowest rate, which switch on the ITEM's wind/hail exclusion (Schedule V), and row 115
    (its W/H factor) pointed at row 32 (StdPropPol). ISO (SpecialClassBusnIncome, CW):
      BasicGroupIIRate = ROUND(ROUND(base(state, terr, item symbol, Bldg) x LCM) x item numeric)
      CoL adjustment   = BasicGroupIIRate                                    no SC BI exclusion
                       = ROUND(ROUND(lowest(state, item symbol) x LCM) x W/H excl factor)  SC BI excludes
    keyed on SC BI's OWN exclusion (Schedule N 263+). Probe `scenarios/rc2/s2_scbi_windhail_differs`:
    FL SC BI BGII 162 vs ISO 2."""
    sc = wb.Worksheets(SCC)
    n = 0
    for c in COLS:
        X = colname(c)
        i = f"{X}$168"                                           # the Special Class item's column
        loc = f"INDEX($C$163:$AP$163,1,{i})"
        st = f"INDEX('IN - Schedule'!$C$5:$C$44,{loc})"
        terr = f"INDEX('IN - Schedule'!$I$5:$I$44,{loc})"
        sym = f"INDEX('IN - Schedule'!$R$220:$R$259,{i})"
        ex = f"'IN - Schedule'!$N${260 + c}"
        old = {109: f"=INDEX($C$26:$AP$26,1,{i})", 110: f"=INDEX($C$27:$AP$27,1,{i})",
               112: f"=INDEX($C$29:$AP$29,1,{i})", 113: f"=ROUND(({X}109+{X}110)*{X}111*{X}112,3)",
               115: f"=INDEX($C$32:$AP$32,1,{i})", 116: f"=ROUND({X}113*{X}114*{X}115,3)"}
        for r, f in old.items():
            if str(w11.com_retry(lambda r=r: sc.Cells(r, c).Formula)) != f:
                raise Gate(f"Special Class {X}{r} is not {f!r}")
        B = "'TBL - BldgBGIIRating'!"
        new = {109: f"=IFERROR(INDEX({B}$E$2:$E$382,MATCH({st}&{terr}&{sym},{B}$A$2:$A$382,0)),0)",
               110: f"=IFERROR(INDEX({B}$AE$2:$AE$358,MATCH({st}&{sym},{B}$AB$2:$AB$358,0)),0)",
               112: (f"=IFERROR(VLOOKUP(INDEX($C$176:$AP$176,1,{i}),"
                     f"'TBL - Special Class'!$AK$2:$AO$3335,4,FALSE),0)"),
               113: f"=ROUND(ROUND({X}109*{X}111,3)*{X}112,3)",
               115: (f"=IF({ex}=\"Yes\",IFERROR(VLOOKUP(INDEX($C$177:$AP$177,1,{i}),"
                     f"'TBL - Special Class'!$AQ$2:$AT$189,4,FALSE),1),1)"),
               116: (f"=IF({ex}=\"Yes\",ROUND(ROUND({X}110*{X}111,3)*{X}115,3),"
                     f"ROUND({X}113*{X}114,3))")}
        for r, f in new.items():
            w11.com_retry(lambda r=r, f=f: setattr(sc.Cells(r, c), "Formula", f))
        n += 6
    return f"S-2: {n} cells -- SC Business Income Group II uses its own rates and exclusion", {SCC}


def fix_whx(app, wb):
    """RC-2 ED-WHX + W-4 (2026-09-24). What an EXCLUDED wind/hail does to the Group II cause-of-loss
    adjustment is a state family (every in-force `SetBasicGroupIICauseOfLossAdjustment`, all five
    coverages, traced):
      CW (and lowest-rate variants)  ROUND chain lowest x LCM x ... x W/H excl factor x StdPol
      NONE  AR DC NY RI              the regular Group II rate; the exclusion changes nothing
      TX                             regular rate x `WindstormOrHailExclFactorTX` (0.1)
      FL                             `BasicGroupIIWindstormOrHailExclRate` (0.001) x LCM (x numeric: BI / SC / SC BI)
      KS                             `BasicGroupIIWindstormOrHailExclRate` (0.023) x LCM (Bldg x ACV x cosmetic;
                                     BI x BGIIBaseRateAdjustmentFactor)
    The rater applied CW everywhere (TX probe: Building / BI Group II $0 vs ISO 559 / 364). New sheet
    `TBL - WHExclMode` (State, Mode, Value); a state not listed is CW. Each coverage keys on its OWN
    election (Building AE, Contents I, BI N, SC V, SC BI N). W-4: BI's base no longer borrows the
    Building's (which is the LOWEST rate when the Building excludes) -- ISO's BI looks up its own."""
    import csv
    ws = w11.new_sheet(wb, "TBL - WHExclMode")
    rd = lambda f: list(csv.reader(open(f, encoding="utf-8-sig")))[1:]            # noqa: E731
    eff = effective_date(wb)
    tx = float(rd(state_file_in_force("TX", "WindstormOrHailExclFactorTX", eff))[0][2])
    fl = {r[2] for r in rd(state_file_in_force("FL", "BasicGroupIIWindstormOrHailExclRate", eff))}
    if len(fl) != 1:
        raise Gate(f"FL exclusion rate varies by symbol: {fl}")
    ks = float(rd(state_file_in_force("KS", "BasicGroupIIWindstormOrHailExclRate", eff))[0][2])
    rows = [("State", "Mode", "Value", "Source (RC-2 ED-WHX, 2026-09-24)"),
            ("AR", "NONE", 1, "exclusion leaves the Group II rate unchanged"), ("DC", "NONE", 1, ""),
            ("NY", "NONE", 1, ""), ("RI", "NONE", 1, ""),
            ("TX", "TX", tx, "WindstormOrHailExclFactorTX x regular rate"),
            ("FL", "FL", float(fl.pop()), "BasicGroupIIWindstormOrHailExclRate x LCM"),
            ("KS", "KS", ks, "BasicGroupIIWindstormOrHailExclRate x LCM"),
            ("(other)", "CW", "", "not listed = CW lowest-rate method")]
    ws.Range("A1:D9").Value = tuple(rows)
    M = lambda st: f"IFERROR(VLOOKUP({st},'TBL - WHExclMode'!$A$2:$C$9,2,FALSE),\"CW\")"   # noqa: E731
    V = lambda st: f"IFERROR(VLOOKUP({st},'TBL - WHExclMode'!$A$2:$C$9,3,FALSE),1)"        # noqa: E731

    def edit(sh, r, c, pairs):
        f = str(w11.com_retry(lambda: sh.Cells(r, c).Formula))
        for a, b in pairs:
            if a not in f:
                raise Gate(f"{sh.Name}!{colname(c)}{r}: expected {a!r} in {f!r}")
            f = f.replace(a, b)
        w11.com_retry(lambda: setattr(sh.Cells(r, c), "Formula", f))

    def setf(sh, r, c, f):
        w11.com_retry(lambda: setattr(sh.Cells(r, c), "Formula", f))

    br, cr, bi, sc = (wb.Worksheets(s) for s in ("CALC - Bldg Rating", "CALC - Contents Rating",
                                                 "CALC - BI Rating", SCC))
    n = 0
    for c in COLS:
        X = colname(c)
        # ---------------- Building (schedule row 45+c)
        AE = f"'IN - Schedule'!$AE${45 + c}"
        st = f"'CALC - CoreScratchpad'!{X}$2"
        ex_cw = f"AND({AE}=\"Yes\",{M(st)}=\"CW\")"
        edit(br, 36, c, [(f"=IF({AE}=\"Yes\",0,", f"=IF({ex_cw},0,")])
        edit(br, 37, c, [(f"=IF({AE}=\"No\",0,", f"=IF(NOT({ex_cw}),0,")])
        regular = f"ROUND(ROUND(ROUND(ROUND(ROUND({X}36*{X}38,3)*{X}39,3)*{X}9,3)*{X}40,3)*{X}41,3)"
        lowest = f"ROUND(ROUND(ROUND({X}37*{X}38,3)*{X}9,3)*{X}40,3)"
        edit(br, 42, c, [(f"IF({AE}=\"No\",{regular},IF({AE}=\"Yes\",{lowest},0))",
                          f"IF(OR({AE}<>\"Yes\",{M(st)}=\"NONE\",{M(st)}=\"TX\"),{regular},"
                          f"IF({M(st)}=\"FL\",ROUND({V(st)}*{X}38,3),"
                          f"IF({M(st)}=\"KS\",ROUND(ROUND(ROUND({V(st)}*{X}38,3)*{X}9,3)*{X}40,3),{lowest})))")])
        old44 = str(w11.com_retry(lambda: br.Cells(44, c).Formula))
        setf(br, 44, c, f"=IF({AE}<>\"Yes\",1,IF({M(st)}=\"TX\",{V(st)},IF({M(st)}=\"CW\",{old44[1:]},1)))")
        edit(br, 45, c, [(f"=ROUND({X}42*{X}43*{X}44,3)", f"=ROUND(ROUND({X}42*{X}44,3)*{X}43,3)")])
        # ---------------- Contents (schedule row 131+c)
        I = f"'IN - Schedule'!$I${131 + c}"
        cst = f"INDEX('CALC - CoreScratchpad'!$C$2:$AP$2,1,{X}$116)"
        cex_cw = f"AND({I}=\"Yes\",{M(cst)}=\"CW\")"
        edit(cr, 34, c, [(f"=IF({I}=\"Yes\",0,", f"=IF({cex_cw},0,")])
        edit(cr, 35, c, [(f"=IF({I}=\"No\",0,", f"=IF(NOT({cex_cw}),0,")])
        edit(cr, 39, c, [(f"IF({I}=\"No\",ROUND({X}34*{X}36*{X}37*{X}38,3),IF({I}=\"Yes\",ROUND({X}35*{X}36,3),0))",
                          f"IF(OR({I}<>\"Yes\",{M(cst)}=\"NONE\",{M(cst)}=\"TX\"),ROUND({X}34*{X}36*{X}37*{X}38,3),"
                          f"IF(OR({M(cst)}=\"FL\",{M(cst)}=\"KS\"),ROUND({V(cst)}*{X}36,3),ROUND({X}35*{X}36,3)))")])
        old41 = str(w11.com_retry(lambda: cr.Cells(41, c).Formula))
        setf(cr, 41, c, f"=IF({I}<>\"Yes\",1,IF({M(cst)}=\"TX\",{V(cst)},IF({M(cst)}=\"CW\",{old41[1:]},1)))")
        edit(cr, 42, c, [(f"=ROUND({X}39*{X}40*{X}41,3)", f"=ROUND(ROUND({X}39*{X}41,3)*{X}40,3)")])
        # ---------------- Business Income (schedule row 174+c; building = X$81)
        N = f"'IN - Schedule'!$N${174 + c}"
        bst = f"INDEX('CALC - CoreScratchpad'!$C$2:$AP$2,1,{X}$81)"
        B2 = "'TBL - BldgBGIIRating'!"
        edit(bi, 29, c, [(f"INDEX('CALC - Bldg Rating'!$C$36:$AP$36,1,{X}$81)+INDEX('CALC - Bldg Rating'!$C$37:$AP$37,1,{X}$81)",
                          f"IFERROR(INDEX({B2}$E$2:$E$382,MATCH(INDEX('CALC - CoreScratchpad'!$C$59:$AP$59,1,{X}$81),"
                          f"{B2}$A$2:$A$382,0)),0)")])
        low = (f"IFERROR(INDEX({B2}$AE$2:$AE$358,MATCH(INDEX('CALC - CoreScratchpad'!$C$72:$AP$72,1,{X}$81),"
               f"{B2}$AB$2:$AB$358,0)),0)")
        key = f"\"Yes\"&{bst}&INDEX('CALC - CoreScratchpad'!$C$287:$AP$287,1,{X}$81)"
        setf(bi, 35, c, f"=IF({N}<>\"Yes\",1,IF({M(bst)}=\"TX\",{V(bst)},IF({M(bst)}=\"CW\","
                        f"IFERROR(VLOOKUP({key},'TBL - ContentsTables'!$DL$2:$DP$188,5,FALSE),1),1)))")
        old36 = f"=IF({N}=\"No\",ROUND({X}33*{X}34,3),IF({N}=\"Yes\",ROUND({X}33*{X}34*{X}35,3)))"
        if str(w11.com_retry(lambda: bi.Cells(36, c).Formula)) != old36:
            raise Gate(f"BI {X}36 is not {old36!r}")
        setf(bi, 36, c, f"=IF(OR({N}<>\"Yes\",{M(bst)}=\"NONE\"),ROUND({X}33*{X}34,3),"
                        f"IF({M(bst)}=\"TX\",ROUND(ROUND({X}33*{X}35,3)*{X}34,3),"
                        f"IF({M(bst)}=\"FL\",ROUND(ROUND(ROUND({V(bst)}*{X}30,3)*{X}31,3)*{X}34,3),"
                        f"IF({M(bst)}=\"KS\",ROUND(ROUND(ROUND({V(bst)}*{X}30,3)*{X}32,3)*{X}34,3),"
                        f"ROUND(ROUND(ROUND({low}*{X}30,3)*{X}35,3)*{X}34,3)))))")
        # ---------------- Special Class item (schedule row 217+c)
        Vv = f"'IN - Schedule'!$V${217 + c}"
        sst = f"INDEX('IN - Schedule'!$C$5:$C$44,{X}$163)"
        sex_cw = f"AND({Vv}=\"Yes\",{M(sst)}=\"CW\")"
        edit(sc, 26, c, [(f"=IF({Vv}=\"Yes\",0,", f"=IF({sex_cw},0,")])
        edit(sc, 27, c, [(f"=IF({Vv}=\"No\",0,", f"=IF(NOT({sex_cw}),0,")])
        edit(sc, 29, c, [(f"IF({Vv}=\"Yes\",1,", f"IF({sex_cw},1,")])
        edit(sc, 30, c, [(f"=ROUND(({X}26+{X}27)*{X}28*{X}29,3)",
                          f"=IF(AND({Vv}=\"Yes\",{M(sst)}=\"FL\"),ROUND(ROUND({V(sst)}*{X}28,3)*{X}29,3),"
                          f"IF(AND({Vv}=\"Yes\",{M(sst)}=\"KS\"),ROUND({V(sst)}*{X}28,3),"
                          f"ROUND(({X}26+{X}27)*{X}28*{X}29,3)))")])
        old31 = str(w11.com_retry(lambda: sc.Cells(31, c).Formula))
        setf(sc, 31, c, f"=IF({Vv}<>\"Yes\",1,IF({M(sst)}=\"TX\",{V(sst)},IF({M(sst)}=\"CW\",{old31[1:]},1)))")
        edit(sc, 33, c, [(f"=ROUND({X}30*{X}31*{X}32,3)", f"=ROUND(ROUND({X}30*{X}31,3)*{X}32,3)")])
        # ---------------- SC Business Income (rows 109-116, own election N 260+c; item = X$168)
        ex = f"'IN - Schedule'!$N${260 + c}"
        qst = f"INDEX('IN - Schedule'!$C$5:$C$44,INDEX($C$163:$AP$163,1,{X}$168))"
        old115 = str(w11.com_retry(lambda: sc.Cells(115, c).Formula))
        if not old115.startswith(f"=IF({ex}=\"Yes\",IFERROR(VLOOKUP("):
            raise Gate(f"SC {X}115 is not the S-2 formula: {old115!r}")
        cwf = old115[len(f"=IF({ex}=\"Yes\","):-len(",1)")]
        setf(sc, 115, c, f"=IF({ex}<>\"Yes\",1,IF({M(qst)}=\"TX\",{V(qst)},IF({M(qst)}=\"CW\",{cwf},1)))")
        setf(sc, 116, c, f"=IF(OR({ex}<>\"Yes\",{M(qst)}=\"NONE\"),ROUND({X}113*{X}114,3),"
                         f"IF({M(qst)}=\"TX\",ROUND(ROUND({X}113*{X}115,3)*{X}114,3),"
                         f"IF({M(qst)}=\"FL\",ROUND(ROUND({V(qst)}*{X}111,3)*{X}112,3),"
                         f"IF({M(qst)}=\"KS\",ROUND({V(qst)}*{X}111,3),"
                         f"ROUND(ROUND({X}110*{X}111,3)*{X}115,3)))))")
        n += 20
    return (f"ED-WHX + W-4: {n} cells; TBL - WHExclMode (TX {tx}, FL {rows[6][2]}, KS {ks}; AR DC NY RI none)",
            {"CALC - Bldg Rating", "CALC - Contents Rating", "CALC - BI Rating", SCC})


def fix_whxnum(app, wb):
    """RC-2 ED-WHX follow-up (2026-09-24). CoreScratchpad row 68 (the Building's Group II numeric
    value) is forced to 1 when the BUILDING excludes wind/hail (row 60). Right for the CW lowest-rate
    path, which ignores it; wrong (a) for the Building's regular path in NONE / TX states, and (b)
    for BI, which ISO always rates with `../../BasicGroupIINumericValue` (FL probe: BI Group II
    3 vs ISO 11 -- ISO BasicGroupIIRate 0.329 = 0.129 x numeric 4 x BCEG x adj). Row 68 now forces 1
    only for an excluded CW-mode building; BI row 31 reads the numeric without the exclusion gate."""
    cs, bi = wb.Worksheets(w11.CS), wb.Worksheets("CALC - BI Rating")
    M = lambda st: f"IFERROR(VLOOKUP({st},'TBL - WHExclMode'!$A$2:$C$9,2,FALSE),\"CW\")"   # noqa: E731
    n = 0
    for c in COLS:
        X, b = colname(c), 45 + c
        old = f"=IF({X}60=\"Yes\",1,IF({X}63=\"Yes\",{X}65,IF('IN - Schedule'!$M${b}=\"Yes\",{X}67,1)))"
        f = str(w11.com_retry(lambda: cs.Cells(68, c).Formula))
        if f != old:
            raise Gate(f"CoreScratchpad {X}68 is not {old!r}: {f!r}")
        w11.com_retry(lambda: setattr(cs.Cells(68, c), "Formula",
                                      old.replace(f"=IF({X}60=\"Yes\",1,", f"=IF(AND({X}60=\"Yes\",{M(X + '$2')}=\"CW\"),1,")))
        old31 = f"=INDEX('CALC - Bldg Rating'!$C$39:$AP$39,1,{X}$81)"
        if str(w11.com_retry(lambda: bi.Cells(31, c).Formula)) != old31:
            raise Gate(f"BI {X}31 is not {old31!r}")
        I = lambda row: f"INDEX('CALC - CoreScratchpad'!$C${row}:$AP${row},1,{X}$81)"    # noqa: E731
        w11.com_retry(lambda: setattr(bi.Cells(31, c), "Formula",
                                      f"=IF({I(63)}=\"Yes\",{I(65)},IF(INDEX('IN - Schedule'!$M$48:$M$87,{X}$81)=\"Yes\","
                                      f"{I(67)},1))"))
        n += 2
    return f"ED-WHX numeric: {n} cells", {"CALC - BI Rating"}


def fix_whxnum2(app, wb):
    """RC-2 ED-WHX (2026-09-24), correcting WHXNUM's BI half. The AL probe (Building excludes, BI does
    not, CW state) showed ISO's BI uses numeric 1 there: ISO's own `SetBasicGroupIINumericValue` DOES
    force 1 for an excluded building in CW-mode states (AR DC FL KS NY RI override it and don't). So
    BI row 31 goes back to the Building's numeric (row 39 = CoreScratchpad 68, now mode-gated)."""
    bi = wb.Worksheets("CALC - BI Rating")
    for c in COLS:
        X = colname(c)
        f = str(w11.com_retry(lambda: bi.Cells(31, c).Formula))
        if not f.startswith(f"=IF(INDEX('CALC - CoreScratchpad'!$C$63:$AP$63,1,{X}$81)"):
            raise Gate(f"BI {X}31 is not the WHXNUM formula: {f!r}")
        w11.com_retry(lambda: setattr(bi.Cells(31, c), "Formula",
                                      f"=INDEX('CALC - Bldg Rating'!$C$39:$AP$39,1,{X}$81)"))
    return "ED-WHX numeric: BI row 31 back to the Building's (mode-gated) numeric", {"CALC - BI Rating"}


def fix_w3fin(app, wb):
    """RC-2 W-3 + final-rate rounding (2026-09-24), from the large-limit per-location probe
    (`scenarios/rc2/w3_perloc_large.json`, AK $20M building excluded, $10M contents).
    1. FINRND: ISO `SetFinal*Rate` (Structure, PersonalProperty, Special Class) is
       ROUND(ROUND(adjusted x per-location credit,3) x deductible [x multi-res],3); the rater's
       Building 22/52/76/102 and Contents 20/48/71/99 rounded once (Bldg BGI 7738 vs ISO 7936,
       Contents Special 3271 vs 3369).
    2. W-3: ISO's Group II per-location credit (`SetBGIIDeductibleByLocationFactor`) ignores every
       wind/hail exclusion; it needs the per-location record and `WindstormHailIndicator` = 0, i.e.
       NOT (1% and W/H total >= 100,000 / 2% >= 50,000 / 5% >= 20,000). W/H total = the building's limit
       unless it excludes W/H + its contents that don't. Bldg row 49 (Contents 46 reads it) gated on
       the Building's exclusion instead (ISO 0.995, rater 1.0)."""
    br, cr = wb.Worksheets(BR), wb.Worksheets("CALC - Contents Rating")
    fin = [(br, {22: (18, 19, [20, 21]), 52: (48, 49, [50, 51]), 76: (72, 73, [74, 75]), 102: (98, 99, [100, 101])}),
           (cr, {20: (17, 18, [19]), 48: (45, 46, [47]), 71: (67, 68, [69, 70]), 99: (95, 96, [97, 98])})]
    n = 0
    for c in COLS:
        X = colname(c)
        for sh, rows in fin:
            for r, (a, d, rest) in rows.items():
                old = "=ROUND(" + "*".join(f"{X}{k}" for k in [a, d] + rest) + ",3)"
                f = str(w11.com_retry(lambda: sh.Cells(r, c).Formula))
                if f != old:
                    raise Gate(f"{sh.Name}!{X}{r} is not {old!r}: {f!r}")
                new = f"=ROUND(ROUND({X}{a}*{X}{d},3)*" + "*".join(f"{X}{k}" for k in rest) + ",3)"
                w11.com_retry(lambda: setattr(sh.Cells(r, c), "Formula", new))
                n += 1
        b = 45 + c
        S = lambda k: f"'IN - Schedule'!${k}${b}"                               # noqa: E731
        old49 = (f"=IF(AND({S('AE')}=\"No\",INDEX('IN - Schedule'!$N$5:$N$44,'CALC - CoreScratchpad'!{X}$285)=\"Yes\"),"
                 f"IFERROR(VLOOKUP('CALC - CoreScratchpad'!{X}$2,'TBL - DeductibleByLocation'!$A$2:$B$46,2,FALSE),1),1)")
        f = str(w11.com_retry(lambda: br.Cells(49, c).Formula))
        if f != old49:
            raise Gate(f"Bldg {X}49 is not {old49!r}: {f!r}")
        tot = (f"(IF({S('AE')}<>\"Yes\",{S('N')},0)+SUMIFS('IN - Schedule'!$E$134:$E$173,'IN - Schedule'!$L$134:$L$173,"
               f"{S('A')},'IN - Schedule'!$C$134:$C$173,\"Yes\",'IN - Schedule'!$I$134:$I$173,\"No\"))")
        w = S("S")
        ind = (f"OR(AND(OR({w}=\"1%\",{w}=0.01),{tot}>=100000),AND(OR({w}=\"2%\",{w}=0.02),{tot}>=50000),"
               f"AND(OR({w}=\"5%\",{w}=0.05),{tot}>=20000))")
        new49 = (f"=IF(AND(INDEX('IN - Schedule'!$N$5:$N$44,'CALC - CoreScratchpad'!{X}$285)=\"Yes\",NOT({ind})),"
                 f"IFERROR(VLOOKUP('CALC - CoreScratchpad'!{X}$2,'TBL - DeductibleByLocation'!$A$2:$B$46,2,FALSE),1),1)")
        w11.com_retry(lambda: setattr(br.Cells(49, c), "Formula", new49))
        n += 1
    return f"W-3 + FINRND: {n} cells", {BR, "CALC - Contents Rating"}


w11.FIXES["W3FIN"] = fix_w3fin
w11.EXPECT_COLS["W3FIN"] = set()
w11.NO_MOVE.add("W3FIN")        # no baseline location elects per-location deductibles
w11.FIXES["WHXNUM2"] = fix_whxnum2
w11.EXPECT_COLS["WHXNUM2"] = set()
w11.NO_MOVE.add("WHXNUM2")
w11.FIXES["WHXNUM"] = fix_whxnum
w11.EXPECT_COLS["WHXNUM"] = set()
w11.NO_MOVE.add("WHXNUM")
w11.FIXES["WHX"] = fix_whx
w11.EXPECT_COLS["WHX"] = set()
w11.NO_MOVE.add("WHX")          # nothing on the baseline excludes wind/hail
w11.FIXES["S2"] = fix_s2
w11.EXPECT_COLS["S2"] = set()
w11.NO_MOVE.add("S2")           # baseline SC BI excludes nothing
w11.FIXES["W5"] = fix_w5
w11.EXPECT_COLS["W5"] = set()
w11.NO_MOVE.add("W5")           # Building and Contents coinsurance are both 80% on the baseline
w11.FIXES["SCGISTFL"] = fix_scgistfl
w11.EXPECT_COLS["SCGISTFL"] = set()
w11.NO_MOVE.add("SCGISTFL")
w11.FIXES["SCGIST"] = fix_scgist
w11.EXPECT_COLS["SCGIST"] = set()
w11.NO_MOVE.add("SCGIST")       # FL's Artificial Turf (FL Option9, PC 5) already equals ISO
w11.FIXES["W22"] = fix_w22
w11.EXPECT_COLS["W22"] = set()
w11.NO_MOVE.add("W22")          # IRPM / PM / MPD are 1.0 on the baseline
w11.FIXES["THDED"] = fix_thded
w11.EXPECT_COLS["THDED"] = set()
w11.NO_MOVE.add("THDED")        # every baseline building has TheftDed = Deductible
w11.FIXES["ROOFRND"] = fix_roofrnd
w11.EXPECT_COLS["ROOFRND"] = set()
w11.NO_MOVE.add("ROOFRND")      # ACV = 1 or Specific on all four baseline buildings
w11.FIXES["EDCASC"] = fix_edcasc
w11.EXPECT_COLS["EDCASC"] = set()
w11.NO_MOVE.add("EDCASC")       # FL's defaults are 2,500 / 2,500 and theft is excluded: same factors
w11.FIXES["SCTHEFT"] = fix_sctheft
w11.EXPECT_COLS["SCTHEFT"] = set()
w11.NO_MOVE.add("SCTHEFT")      # FL's factor is 0.88
w11.EXPECT_COLS["W26"] = set()
w11.NO_MOVE.add("W26")          # none of the 4 baseline states files a single-row table
w11.EXPECT_COLS["SCFIN"] = set()
w11.NO_MOVE.add("SCFIN")        # FL grants no per-location credit; proven by the scenario runs
w11.EXPECT_COLS["W25"] = set()
w11.NO_MOVE.add("W25")          # proven by the scenario runs; today's 4 risks round the same
w11.EXPECT_COLS["SCSPB"] = set()
w11.NO_MOVE.add("SCSPB")
w11.EXPECT_COLS["SCDED"] = set()
w11.NO_MOVE.add("SCDED")
w11.EXPECT_COLS["Z"] = set()
w11.NO_MOVE.add("Z")
w11.EXPECT_COLS["DV"] = set()
w11.NO_MOVE.add("DV")
w11.EXPECT_COLS["CYNY"] = {1}
w11.EXPECT_COLS["W24"] = set()
w11.NO_MOVE.add("W24")
w11.EXPECT_COLS.update(W16={0, 1, 2, 3}, W20={0}, W21={0, 1, 2, 3}, CY={0, 1}, AK=set(), NY={1})
w11.NO_MOVE.add("AK")

if __name__ == "__main__":
    raise SystemExit(w11.main())
