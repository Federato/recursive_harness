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


w11.FIXES.update(W16=fix_w16, W20=fix_w20, W21=fix_w21, CY=fix_cy, AK=fix_ak, NY=fix_ny)
w11.EXPECT_COLS.update(W16={0, 1, 2, 3}, W20={0}, W21={0, 1, 2, 3}, CY={0, 1}, AK=set(), NY={1})
w11.NO_MOVE.add("AK")

if __name__ == "__main__":
    raise SystemExit(w11.main())
