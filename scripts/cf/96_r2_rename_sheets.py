"""R-2 -- prefix every sheet by role, and group the tabs.

``IN``   you type in
``CALC`` never touch -- the rating chains
``TBL``  ISO's filed data, replaced wholesale at each edition
``OUT`` / ``SYS`` reserved for the summary and the payload machinery

**Two deliberate choices.**

*ASCII hyphens, not a middle dot.* The wireframe drew ``IN . Policy``. A non-ASCII
character in a sheet name has to survive every Python script, CSV and console that
touches it, and this session already hit cp1252 encoding failures. Not worth it for
a prettier tab.

*The distinctive word is kept.* ``CALC - CoreScratchpad`` becomes ``CALC - CoreScratchpad``,
not ``CALC - Core``. Docs, memory and scripts across this project grep for the
original words; keeping them means the rename does not invalidate every existing
reference.

Excel rewrites formulas, defined names and validation sources on rename. The
preflight confirmed no ``INDIRECT`` and no VBA, which are the two things it would
not fix. Sheet order does not affect any formula, so regrouping is free.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

TARGET = Path(r"C:\Projects\Spreadsheet_Rater\CF\CFRater1.02.xlsb")
FORBIDDEN = "cfrater1.01.xlsb"

PREMIUMS = ["OUT_Prem_Building", "OUT_Prem_Contents", "OUT_Prem_BI",
            "OUT_Prem_SCBuilding", "OUT_Prem_SCBI", "OUT_Prem_Total"]

#: old name -> new name, in the tab order they should end up in.
RENAME = [
    # NOTE: the left column is the PRE-RENAME name. A later bulk find/replace
    # across scripts/cf/ rewrote these to their new values, collapsing the map to
    # identity pairs and erasing the record of what was renamed. Restored by hand.
    # Exclude this file from any future sheet-name sweep -- it is the mapping,
    # not a consumer of it.
    ("Policy Inputs",             "IN - Policy"),
    ("Location Inputs",           "IN - Location"),
    ("Special Class Inputs",      "IN - Special Class"),

    ("Bldg Rating Worksheet",     "CALC - Bldg Rating"),
    ("Contents Rating Worksheet", "CALC - Contents Rating"),
    ("BI Rating Worksheet",       "CALC - BI Rating"),
    ("Special Class Worksheet",   "CALC - Special Class"),
    ("CoreScratchpad",            "CALC - CoreScratchpad"),

    ("BGIITerritory",             "TBL - BGIITerritory"),
    ("BGI Territories",           "TBL - BGI Territories"),
    ("BI Tables",                 "TBL - BI Tables"),
    ("Special Class",             "TBL - Special Class"),
    ("PolicyDropdowns",           "TBL - PolicyDropdowns"),
    ("ContentsTables",            "TBL - ContentsTables"),
    ("BldgSpecialRating",         "TBL - BldgSpecialRating"),
    ("BldgBGIRating",             "TBL - BldgBGIRating"),
    ("BldgBGIIRating",            "TBL - BldgBGIIRating"),
    ("BroadRating",               "TBL - BroadRating"),
    ("ClassCodes",                "TBL - ClassCodes"),
    ("ConstructionCodes",         "TBL - ConstructionCodes"),
    ("SubStdConditionCode",       "TBL - SubStdConditionCode"),
    ("Sprinkler",                 "TBL - Sprinkler"),
    ("ProtClass",                 "TBL - ProtClass"),
    ("ZipCityState",              "TBL - ZipCityState"),
    ("Derivations",               "TBL - Derivations"),
    ("LCM",                       "TBL - LCM"),
]


def main() -> int:
    n = subprocess.run(["powershell", "-NoProfile", "-Command",
                        "(Get-Process EXCEL -ErrorAction SilentlyContinue).Count"],
                       capture_output=True, text=True).stdout.strip()
    if n and n not in {"0", ""}:
        sys.exit(f"ABORT: {n} Excel process(es) running.")
    if TARGET.name.lower() == FORBIDDEN:
        sys.exit("ABORT: refusing to write to the live rater.")

    too_long = [nw for _, nw in RENAME if len(nw) > 31]
    if too_long:
        sys.exit(f"ABORT: over Excel's 31-char sheet-name limit: {too_long}")

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
        n_names = wb.Names.Count
        print("  baseline  " + "  ".join(f"{k.split('_')[-1]}={v}"
                                         for k, v in baseline.items()))

        # Some names never resolve to a range and never did -- Excel registers
        # `_xlfn.*` / `_xleta.*` shims for newer built-in functions. Baseline the
        # set BEFORE renaming, so the test is "did the rename break something
        # that previously worked", not "is every name range-resolvable".
        def unresolvable(book) -> set[str]:
            out = set()
            for nm in book.Names:
                try:
                    nm.RefersToRange.Address
                except Exception:                           # noqa: BLE001
                    out.add(nm.Name)
            return out

        broken_before = unresolvable(wb)
        print(f"  defined names before: {n_names} "
              f"({len(broken_before)} already non-range, e.g. _xlfn.* shims)\n")

        present = {ws.Name for ws in wb.Worksheets}
        missing = [o for o, _ in RENAME if o not in present]
        extra = present - {o for o, _ in RENAME}
        if missing:
            sys.exit(f"ABORT: expected sheets not found: {missing}")
        if extra:
            sys.exit(f"ABORT: sheets not in the plan: {sorted(extra)}")

        for old, new in RENAME:
            if old != new:
                wb.Worksheets(old).Name = new
        print(f"  renamed {sum(1 for o, nw in RENAME if o != nw)} sheets")

        # Sheet order is cosmetic -- no formula depends on it.
        for i, (_, new) in enumerate(RENAME, start=1):
            if wb.Worksheets(new).Index != i:
                wb.Worksheets(new).Move(Before=wb.Worksheets(i))
        print("  regrouped tabs: IN, then CALC, then TBL")

        app.CalculateFull()
        after = {p: wb.Names(p).RefersToRange.Value for p in PREMIUMS}
        print("\n  after     " + "  ".join(f"{k.split('_')[-1]}={v}"
                                           for k, v in after.items()))
        if after != baseline:
            sys.exit("ABORT: premiums changed -- NOT saving.")
        print("  -> premiums unchanged")

        # Only names that resolved BEFORE and do not now are a problem.
        broken_after = unresolvable(wb)
        newly_broken = sorted(broken_after - broken_before)
        print(f"  defined names after: {wb.Names.Count}, "
              f"non-range: {len(broken_after)} (was {len(broken_before)})")
        if newly_broken:
            for b in newly_broken[:10]:
                print(f"      ! {b}")
            sys.exit("ABORT: rename broke defined names -- NOT saving.")
        print("  -> nothing that worked before is broken now")

        app.Calculation = -4105
        app.CalculateFull()
        wb.Save()
        print("\n  saved.")
        for ws in wb.Worksheets:
            print(f"   {ws.Index:>3}. {ws.Name}")
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
