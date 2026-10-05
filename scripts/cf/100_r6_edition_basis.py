"""R-6 -- put the ISO edition and state basis on the face of the workbook.

Three parts:

**1. A source stamp on every `TBL -` sheet.** Written into the far-right empty
columns -- never by inserting rows, which would shift every absolute reference in
the workbook. The stamp says what the sheet holds, whether it varies by state,
which ISO package it came from, and when it was stamped.

*Why on the sheet and not in a central ledger.* A table **about** the data drifts
from the data -- someone refreshes rates for a new filing, forgets the ledger, and
the workbook then confidently reports a stale edition for current rates, which is
worse than saying nothing. This whole session has been about documents lagging
artefacts. Putting the stamp on the sheet makes refreshing the data and refreshing
its provenance the same edit.

*Where the source is genuinely unknown it says so.* Most `TBL -` sheets have no
recorded pull date. Writing "not recorded" is the point: it makes the refresh
checklist honest instead of inventing a provenance nobody verified.

**2. `TBL - Editions`** -- the per-state ledger, from `State_ERC_CW_Editions.csv`,
plus **explicit rows for the five jurisdictions with no filing anywhere**. An absent
state must be a row that says "NO FILING", not a silent gap -- a lookup that misses
is exactly how a state prices at zero unnoticed.

**3. A live section on `OUT - Diagnostics`** -- for each active location, its state's
edition, age in months against `TODAY()`, and the known quirks that apply to it.

Additive: no existing cell is touched, so no premium can move. Verified anyway.
"""
from __future__ import annotations

import csv
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LEDGER = REPO / "CF_Algorithm" / "dropdown tables" / "State_ERC_CW_Editions.csv"
TARGET = Path(r"F:\Spreadsheet_Rater\CF\CFRater1.02.xlsb")
FORBIDDEN = "cfrater1.01.xlsb"
EDITIONS = "TBL - Editions"
DIAG = "OUT - Diagnostics"

PREMIUMS = ["OUT_Prem_Building", "OUT_Prem_Contents", "OUT_Prem_BI",
            "OUT_Prem_SCBuilding", "OUT_Prem_SCBI", "OUT_Prem_Total"]

#: Jurisdictions with no CF filing in any of the eight snapshot batches.
NO_FILING = ["HI", "ID", "LA", "MS", "WA"]

#: What this project has established about particular states. Only claims with a
#: source behind them -- an empty flag means "nothing known", not "nothing to know".
STATE_FLAGS = {
    "AK": "District split (BasicGroupIDistrictI/II). ZIP mapping is a "
          "known-inaccurate shortcut - not production ready (D-1)",
    "CA": "District split, user-picked District field. No plain BasicGroupIRate "
          "table exists (D-1)",
    "NY": "District split (NYC). Special Class BGI base rate deviates from CW on "
          "84 values, swings over 400%. Built shortcut, known-inaccurate (D-1)",
    "FL": "NOT in the current snapshot batch. Own Residential/Non-Residential BGII "
          "rule. Files 11 SpecialClassDescription strings absent from CW",
    "MT": "NumericValue deviates from CW (construction code 3, four class codes)",
    "PR": "Out of scope. No RAaS entitlement - can never be confirmed against ISO",
}

#: sheet -> (what it holds, does it vary by state, where it came from)
TBL_INFO = {
    "TBL - BGIITerritory":       ("Basic Group II territory by ZIP", True, "per-state ERC"),
    "TBL - ProtClass":           ("Protection class factors", False, "CW package"),
    "TBL - Sprinkler":           ("Sprinkler system / leakage options", False, "CW package"),
    "TBL - SubStdConditionCode": ("Sub-standard condition A-E labels", False,
                                  "CW Form Fields, not a rate table"),
    "TBL - BroadRating":         ("Broad form base rates", True, "per-state ERC"),
    "TBL - BldgBGIIRating":      ("Building Basic Group II rates", True, "per-state ERC"),
    "TBL - BldgBGIRating":       ("Building Basic Group I rates", True, "per-state ERC"),
    "TBL - BGI Territories":     ("Basic Group I territories and factors", True, "per-state ERC"),
    "TBL - BI Tables":           ("Business Income factors and enums", True, "per-state ERC"),
    "TBL - Special Class":       ("Special Class descriptions and codes", False,
                                  "CW package; FL files 11 extra descriptions - see TBL - Editions"),
    "TBL - PolicyDropdowns":     ("Policy-level dropdown domains", False, "CW Domain Tables"),
    "TBL - ContentsTables":      ("Personal Property rates and factors", True, "per-state ERC"),
    "TBL - BldgSpecialRating":   ("Special form building rates", True, "per-state ERC"),
    "TBL - ClassCodes":          ("Class codes and descriptions", False, "CW DomainClassDesc"),
    "TBL - ConstructionCodes":   ("The six construction types", False, "CW ConstructionCode"),
    "TBL - ZipCityState":        ("ZIP to city/state lookup", True, "reference data, not ISO"),
    "TBL - Derivations":         ("Symbol and variant derivations", True, "per-state ERC"),
    "TBL - LCM":                 ("Loss cost multiplier by state", True, "carrier input, not ISO"),
    "TBL - Editions":            ("Per-state ERC edition ledger", True,
                                  "State_ERC_CW_Editions.csv (CF_Algorithm/dropdown tables)"),
}


def clear_stamps(ws) -> int:
    """Remove every existing stamp block on a sheet. Returns how many it found."""
    used = ws.UsedRange
    last = used.Column + used.Columns.Count + 4
    found = [c for c in range(1, last)
             if ws.Cells(1, c).Value == "-- SOURCE STAMP --"]
    for c in found:
        ws.Range(ws.Cells(1, c), ws.Cells(8, c + 1)).ClearContents()
    return len(found)


def effective_from(edition: str) -> str:
    m = re.search(r"(\d{4})(\d{2})(\d{2})", edition or "")
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else ""


def main() -> int:
    n = subprocess.run(["powershell", "-NoProfile", "-Command",
                        "(Get-Process EXCEL -ErrorAction SilentlyContinue).Count"],
                       capture_output=True, text=True).stdout.strip()
    if n and n not in {"0", ""}:
        sys.exit(f"ABORT: {n} Excel process(es) running.")
    if TARGET.name.lower() == FORBIDDEN:
        sys.exit("ABORT: refusing to write to the live rater.")

    ledger = list(csv.DictReader(LEDGER.open(encoding="utf-8-sig")))
    print(f"  ledger: {len(ledger)} states + {len(NO_FILING)} with no filing")

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

        # ---- 1. TBL - Editions ----------------------------------------
        if EDITIONS in [w.Name for w in wb.Worksheets]:
            wb.Worksheets(EDITIONS).Delete()
        ed = wb.Worksheets.Add(wb.Worksheets(wb.Worksheets.Count))
        ed.Name = EDITIONS
        for c, h in enumerate(("State", "ERC Edition", "Effective", "Batch",
                               "CW Edition", "Known flags"), start=1):
            ed.Cells(1, c).Value = h
        r = 2
        for row in sorted(ledger, key=lambda x: x["State"]):
            st = row["State"]
            ed.Cells(r, 1).Value = st
            ed.Cells(r, 2).Value = row["ERC Edition"]
            ed.Cells(r, 3).Value = effective_from(row["ERC Edition"])
            ed.Cells(r, 4).Value = row["SnapshotBatch"]
            ed.Cells(r, 5).Value = row["CW Edition"]
            ed.Cells(r, 6).Value = STATE_FLAGS.get(st, "")
            r += 1
        for st in NO_FILING:
            ed.Cells(r, 1).Value = st
            ed.Cells(r, 2).Value = "NO FILING"
            ed.Cells(r, 3).Value = ""
            ed.Cells(r, 4).Value = ""
            ed.Cells(r, 5).Value = ""
            ed.Cells(r, 6).Value = ("No CF filing in ANY of the eight snapshot "
                                    "batches. Cannot be rated from this corpus")
            r += 1
        last_ed = r - 1
        for w, c in ((8, 1), (24, 2), (12, 3), (14, 4), (20, 5), (90, 6)):
            ed.Columns(c).ColumnWidth = w
        print(f"  '{EDITIONS}' built: {last_ed - 1} rows")

        # ---- 2. stamp every TBL sheet ---------------------------------
        stamped = dupes = 0
        for name, (holds, by_state, source) in TBL_INFO.items():
            ws = wb.Worksheets(name)
            # Clear any prior stamp FIRST, then place one. Computing the column
            # from UsedRange without clearing walks the stamp further right on
            # every run, because the previous stamp is itself now part of the used
            # range -- a second run left two copies on all 18 sheets.
            dupes += clear_stamps(ws)
            used = ws.UsedRange
            col = used.Column + used.Columns.Count + 1     # two clear of the data
            rows = [
                ("-- SOURCE STAMP --", ""),
                ("Holds", holds),
                ("Varies by state", "Yes" if by_state else "No (countrywide)"),
                ("Source", source),
                ("Edition basis", "see TBL - Editions" if by_state
                                  else "CFCW20260601V01"),
                ("Pull date", "not recorded"),
                ("Stamped", "2026-09-22"),
                ("On refresh", "update the rows AND this stamp in the same edit"),
            ]
            for i, (k, v) in enumerate(rows):
                ws.Cells(1 + i, col).Value = k
                ws.Cells(1 + i, col + 1).Value = v
            stamped += 1
        print(f"  stamped {stamped} TBL sheets (cleared {dupes} prior stamp block(s))")

        # ---- 3. live section on OUT - Diagnostics ---------------------
        dg = wb.Worksheets(DIAG)
        used = dg.UsedRange
        r = used.Row + used.Rows.Count + 1
        dg.Cells(r, 1).Value = "5. EDITION AND STATE BASIS"
        dg.Cells(r, 2).Value = ("which ISO filing each active location is priced "
                                "from, and what is known about it")
        r += 1
        for c, h in enumerate(("Loc", "State", "ERC Edition", "Months old",
                               "Known flags"), start=1):
            dg.Cells(r, c).Value = h
        r += 1
        for i in range(1, 11):
            dg.Cells(r, 1).Value = i
            dg.Cells(r, 2).Formula = (
                f'=IF(INDEX(IN_Loc_State,1,{i})="State","",INDEX(IN_Loc_State,1,{i}))')
            dg.Cells(r, 3).Formula = (
                f'=IF($B{r}="","",IFERROR(VLOOKUP($B{r},\'{EDITIONS}\'!$A:$F,2,FALSE),'
                f'"STATE NOT IN LEDGER"))')
            # Excel silently coerces an ISO date string to a serial on write, so
            # the Effective column may be text OR a number depending on how it
            # landed. DATEVALUE on a number errors -- hence the ISNUMBER branch.
            eff = f"VLOOKUP($B{r},'{EDITIONS}'!$A:$F,3,FALSE)"
            dg.Cells(r, 4).Formula = (
                f'=IF(OR($B{r}="",$C{r}="NO FILING",$C{r}="STATE NOT IN LEDGER"),"",'
                f'IFERROR(DATEDIF(IF(ISNUMBER({eff}),{eff},DATEVALUE({eff})),'
                f'TODAY(),"m"),"?"))')
            dg.Cells(r, 5).Formula = (
                f'=IF($B{r}="","",IF($C{r}="NO FILING","CANNOT RATE - no filing",'
                f'IF(AND(ISNUMBER($D{r}),$D{r}>12),"STALE - "&$D{r}&" months. ","")'
                f'&IFERROR(VLOOKUP($B{r},\'{EDITIONS}\'!$A:$F,6,FALSE),"")))')
            r += 1
        dg.Columns(5).ColumnWidth = 90

        app.CalculateFull()
        after = {p: wb.Names(p).RefersToRange.Value for p in PREMIUMS}
        if after != baseline:
            sys.exit("ABORT: premiums changed -- NOT saving.")
        print("  -> premiums unchanged")

        print("\n--- section 5 as it reads now ---")
        for rr in range(r - 10, r):
            vals = [dg.Cells(rr, c).Value for c in range(1, 6)]
            if vals[1]:
                print(f"  Loc {vals[0]}  {vals[1]:<4} {str(vals[2])[:24]:<24} "
                      f"{str(vals[3] or ''):>4}mo  {str(vals[4] or '')[:78]}")

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
