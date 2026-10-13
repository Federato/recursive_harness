"""R-7 -- one page that says whether this quote can be trusted.

Three sections, and the split between them is the point:

**1. Factor checks** -- a live roll-up of R-3's Check/Source columns across the four
   rating worksheets, so nobody has to scroll four sheets to learn there is nothing
   wrong.

**2. Input traps** -- live formulas for the specific ways this workbook is known to
   produce a confident wrong answer. Each is a real documented defect, not a
   hypothetical: a construction code that fails to resolve and silently zeroes a
   chain; Legal Liability elected without an additional-insurable-interest option
   (backlog Z-1, drives the factor to 0.0 and the premium to zero); blanket elected
   when blanket rating is not built; a total that has drifted from its parts (T-1,
   which was live until today).

**3. Standing assumptions** -- accepted divergences, stated rather than discovered.
   These are *not* errors. The reason they sit on the same page is that "the rater
   assumes full value equals the limit" is exactly the kind of thing that is obvious
   to whoever chose it and invisible to whoever reads the number six months later.

Everything in sections 1-2 is a formula. The page re-evaluates itself on every
change; it is not a report that was true once.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

TARGET = Path(r"F:\Spreadsheet_Rater\CF\CFRater1.02.xlsb")
FORBIDDEN = "cfrater1.01.xlsb"
SHEET = "OUT - Diagnostics"

PREMIUMS = ["OUT_Prem_Building", "OUT_Prem_Contents", "OUT_Prem_BI",
            "OUT_Prem_SCBuilding", "OUT_Prem_SCBI", "OUT_Prem_Total"]

CALC_SHEETS = ["CALC - Bldg Rating", "CALC - Contents Rating",
               "CALC - BI Rating", "CALC - Special Class"]

ACTIVE = '(IN_Loc_State<>"State")'

#: (check text, formula, what to do about it)
TRAPS = [
    ("Construction code resolves for every active item",
     f'=IF(SUMPRODUCT({ACTIVE}*(IN_Loc_ConstrCode="Select"))=0,"ok",'
     f'"BLOCK - "&SUMPRODUCT({ACTIVE}*(IN_Loc_ConstrCode="Select"))'
     f'&" active item(s) have no construction code; the chain prices at 0")',
     "Pick a Construction Type from the dropdown on IN - Location"),

    ("Every active item with a limit has a class code",
     f'=IF(SUMPRODUCT({ACTIVE}*(IN_Loc_BuildingLimit>0)*(IN_Loc_BuildingClassCode="Select"))=0,'
     f'"ok","BLOCK - an item has a limit but no class code")',
     "Set Building Class Code on IN - Location"),

    ("Legal Liability items carry an additional-insurable-interest option",
     '=IF(SUMPRODUCT((IN_Loc_BuildingCovType="Legal Liability")'
     '*((IN_Loc_AddlInsurableIntOption="")+(IN_Loc_AddlInsurableIntOption="Not Applicable")))=0,'
     '"ok","BLOCK - blank option drives the factor to 0.0 and the premium to zero (Z-1)")',
     "Option4 = None = 1.00. Set it explicitly; blank is not the same as None"),

    ("Blanket not elected (blanket rating is not built in this workbook)",
     '=IF(COUNTIF(IN_SC_InclInBlanket,"Yes")=0,"ok",'
     '"WARN - blanket elected but blanket rating is unbuilt; the item rates as scheduled")',
     "Leave Included in Blanket = No until blanket rating is built"),

    ("Total premium equals the sum of its parts",
     '=IF(OUT_Prem_Total=OUT_Prem_Building+OUT_Prem_Contents+OUT_Prem_BI'
     '+OUT_Prem_SCBuilding+OUT_Prem_SCBI,"ok",'
     '"BLOCK - total has drifted from its components")',
     "Was live until 2026-09-22 (T-1): the total omitted both Special Class lines"),

    ("Policy factors",
     '=IF(AND(IN_Pol_IRPMFactor=1,IN_Pol_PackageModFactor=1,'
     'IN_Pol_MultiPremiumDispersionFactor=1),"ok - all neutral (1.00)",'
     '"INFO - a policy factor is applied; every coverage is adjusted")',
     "IRPM / Package Mod / Multi-Premium on IN - Policy rows 22-24"),
]

#: Flags already investigated, so the next reader does not repeat the work.
#: Same discipline as `Circular_Review_Tracking.md` -- record the verdict, not just
#: the finding. Retire a row by fixing the cause, not by deleting it.
ADJUDICATED = [
    ("CALC - Contents Rating", "row 66", "LOIFactor = 0 in 4 active items",
     "BENIGN - sits in the BROAD block, whose BaseRate is also 0 because this risk "
     "elects Special. A dormant block shows one factor flag. Reviewed 2026-09-22"),
    ("CALC - Contents Rating", "rows 70, 98",
     "MultiResidentialPropSpecialCreditFactor hard-coded =1",
     "BENIGN - ISO files this credit for Building ONLY. 40 refs in "
     "CommercialPropertyStructureRules.Rule.xml, zero in any PersonalProperty rules "
     "file. The constant is correct. Reviewed 2026-09-22"),
    ("CALC - Bldg / Contents", "several",
     'Label misspelled "MultiResidentialPropSepcialCreditFactor"',
     "COSMETIC - no premium impact; formulas address cells, not labels. Worth fixing "
     "because a label-based search finds one spelling and misses the other rows"),
]

ASSUMPTIONS = [
    ("D-1", "AK, CA and NY district-split base rates use shortcuts",
     "NY a built shortcut, AK a ZIP mapping. Known-inaccurate, not production-ready"),
    ("D-2", "Full insurable value is assumed equal to the limit",
     "The workbook has no value input. Any coinsurance test depending on true value is wrong"),
    ("S-1", "Vandalism exclusion shares one input across datadef groups",
     "ISO files a separate record per group; cannot exclude on BI but not the building"),
    ("S-2", "Windstorm/hail exclusion shares one input across datadef groups", "Same shape as S-1"),
    ("S-3", "Theft exclusion shares one input across datadef groups",
     "Same shape, and the factor tables genuinely differ (0.88 bldg vs 0.86 BI)"),
    ("--", "Blanket rating is not built", "Every Branch B is inert line-wide"),
    ("--", "Earthquake is not built", "Untraced on both the rater and the harness side"),
    ("--", "Specific/Tentative rating is built but never ISO-verified",
     "Rates produce numbers; no live ISO call has confirmed them"),
    ("--", "One ERC edition, resolved outside the workbook",
     "No edition-transition logic. FL's last filing is over a year stale. See R-6"),
]


def main() -> int:
    n = subprocess.run(["powershell", "-NoProfile", "-Command",
                        "(Get-Process EXCEL -ErrorAction SilentlyContinue).Count"],
                       capture_output=True, text=True).stdout.strip()
    if n and n not in {"0", ""}:
        sys.exit(f"ABORT: {n} Excel process(es) running.")
    if TARGET.name.lower() == FORBIDDEN:
        sys.exit("ABORT: refusing to write to the live rater.")

    import win32com.client
    app = win32com.client.DispatchEx("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    app.EnableEvents = False
    wb = None
    try:
        wb = app.Workbooks.Open(str(TARGET), UpdateLinks=0)
        app.Calculation = -4135
        app.CalculateFull()
        baseline = {p: wb.Names(p).RefersToRange.Value for p in PREMIUMS}
        print("  baseline  " + "  ".join(f"{k.split('_')[-1]}={v}"
                                         for k, v in baseline.items()))

        existing = [w.Name for w in wb.Worksheets]
        if SHEET in existing:
            wb.Worksheets(SHEET).Delete()                   # idempotent rebuild
            print(f"  removed existing '{SHEET}' to rebuild")

        ws = wb.Worksheets.Add(wb.Worksheets(4))            # single positional = Before
        ws.Name = SHEET

        r = 1
        ws.Cells(r, 1).Value = "DIAGNOSTICS"
        ws.Cells(r, 2).Value = ("Live - recalculates with the workbook. "
                                "BLOCK = do not quote. WARN = quote with care. "
                                "INFO = nothing wrong.")
        r += 2

        # --- 1. factor checks -------------------------------------------
        ws.Cells(r, 1).Value = "1. FACTOR CHECKS"
        ws.Cells(r, 2).Value = "rolled up from the Check / Source columns (R-3)"
        r += 1
        for h, c in zip(("Sheet", "Zero flags", "Hard-coded", "Status"), range(1, 5)):
            ws.Cells(r, c).Value = h
        r += 1
        first_data = r
        for s in CALC_SHEETS:
            ws.Cells(r, 1).Value = s
            ws.Cells(r, 2).Formula = f"=COUNTIF('{s}'!N:N,\"ZERO*\")"
            ws.Cells(r, 3).Formula = f"=COUNTIF('{s}'!M:M,\"CONSTANT*\")"
            ws.Cells(r, 4).Formula = (
                f'=IF(B{r}+C{r}=0,"ok","{"{0}"}"&B{r}+C{r}&" to review")'
                .replace("{0}", ""))
            r += 1
        ws.Cells(r, 1).Value = "TOTAL"
        ws.Cells(r, 2).Formula = f"=SUM(B{first_data}:B{r-1})"
        ws.Cells(r, 3).Formula = f"=SUM(C{first_data}:C{r-1})"
        ws.Cells(r, 4).Formula = (
            f'=IF(B{r}+C{r}=0,"clean","{""}"&B{r}+C{r}&" flag(s) - each needs a verdict")')
        r += 2

        # --- 2. input traps ---------------------------------------------
        ws.Cells(r, 1).Value = "2. INPUT TRAPS"
        ws.Cells(r, 2).Value = "live checks for known ways to get a confident wrong answer"
        r += 1
        for h, c in zip(("#", "Check", "Result", "What to do"), range(1, 5)):
            ws.Cells(r, c).Value = h
        r += 1
        for i, (text, formula, action) in enumerate(TRAPS, 1):
            ws.Cells(r, 1).Value = i
            ws.Cells(r, 2).Value = text
            ws.Cells(r, 3).Formula = formula
            ws.Cells(r, 4).Value = action
            r += 1
        r += 1

        # --- 3. adjudicated flags ---------------------------------------
        ws.Cells(r, 1).Value = "3. ADJUDICATED"
        ws.Cells(r, 2).Value = ("flags from section 1 that have been investigated - "
                                "do not re-review these")
        r += 1
        for h, c in zip(("Sheet", "Where", "Flag", "Verdict"), range(1, 5)):
            ws.Cells(r, c).Value = h
        r += 1
        for sh, where, flag, verdict in ADJUDICATED:
            ws.Cells(r, 1).Value = sh
            ws.Cells(r, 2).Value = where
            ws.Cells(r, 3).Value = flag
            ws.Cells(r, 4).Value = verdict
            r += 1
        r += 1

        # --- 4. standing assumptions ------------------------------------
        ws.Cells(r, 1).Value = "4. STANDING ASSUMPTIONS"
        ws.Cells(r, 2).Value = ("accepted divergences - NOT errors. Stated here so they "
                                "are not rediscovered as surprises")
        r += 1
        for h, c in zip(("ID", "Assumption", "Consequence"), range(1, 4)):
            ws.Cells(r, c).Value = h
        r += 1
        for tag, what, why in ASSUMPTIONS:
            ws.Cells(r, 1).Value = tag
            ws.Cells(r, 2).Value = what
            ws.Cells(r, 3).Value = why
            r += 1

        ws.Columns(1).ColumnWidth = 24
        ws.Columns(2).ColumnWidth = 62
        ws.Columns(3).ColumnWidth = 58
        ws.Columns(4).ColumnWidth = 58

        app.CalculateFull()
        after = {p: wb.Names(p).RefersToRange.Value for p in PREMIUMS}
        if after != baseline:
            sys.exit("ABORT: premiums changed -- NOT saving.")
        print("  -> premiums unchanged")

        print(f"\n  '{SHEET}' built at position {ws.Index}\n")
        print("--- what it says right now ---")
        for rr in range(1, r + 1):
            a = ws.Cells(rr, 1).Value
            b = ws.Cells(rr, 2).Value
            c = ws.Cells(rr, 3).Value
            if a is None and b is None:
                continue
            line = f"  {str(a or '')[:22]:<22} {str(b or '')[:58]:<58} {str(c or '')[:56]}"
            print(line.rstrip())

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
    print("Instance closed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
