"""R-8 Phase 2b, survey -- what does `CALC - Contents Rating` actually depend on?

Before repointing anything, establish three things:

1. **Which of its rows read the input sheets**, and which read building-level values
   rather than contents-level ones. A contents record inherits its building's
   deductible, protection class, territory and construction -- so after the split
   each contents column has to resolve its parent, not just its own row.
2. **What CoreScratchpad supplies**, since that is the shared machinery the
   migration has to re-key.
3. **How the premium rolls up**, because that is the gate.

Read-only. Writes a census to CSV so the migration works from a list rather than a
search.
"""
from __future__ import annotations

import csv
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TARGET = Path(r"C:\Projects\Spreadsheet_Rater\CF\CFRater1.02.xlsb")
OUT = REPO / "CF_Algorithm" / "CF_R8_Contents_Dependency_Census.csv"
SHEET = "CALC - Contents Rating"

#: Input rows that describe the BUILDING, not the contents record. After the
#: split these must be resolved via the contents record's parent building.
BUILDING_LEVEL = {
    22: "ProtClass", 17: "BGITerr", 19: "BGIITerr", 20: "SpecialTerr",
    26: "BuildingClassCode", 60: "ConstrCode", 62: "ConstrType",
    64: "ConstrSymbol", 63: "NumStories", 23: "BCEG", 52: "Deductible",
    53: "WindHailDed", 54: "TheftDed", 50: "CauseOfLoss", 13: "ZipCode",
    14: "City", 15: "State", 85: "Vacancy", 72: "SprinklerSystem",
    65: "OpenSides", 57: "MultiResCredit", 55: "PerLocationDed",
    18: "District", 24: "RoofSurfacing", 28: "RatingType",
}
#: Input rows that genuinely belong to the contents record itself.
CONTENTS_LEVEL = {
    9: "PP CovType", 45: "Contents Limit", 46: "Contents SpecificRate",
    69: "Contents Coinsurance", 27: "TenantsClassCode", 32: "OccupCategory",
    33: "OccupSeverity", 34: "ContentsGroup", 10: "PP CovForm",
    67: "Valuation", 97: "WindHailExcl-Contents", 100: "VandalismExcl-Contents",
    103: "TheftExcl-Contents", 30: "YardProperty",
}


def main() -> int:
    n = subprocess.run(["powershell", "-NoProfile", "-Command",
                        "(Get-Process EXCEL -ErrorAction SilentlyContinue).Count"],
                       capture_output=True, text=True).stdout.strip()
    if n and n not in {"0", ""}:
        sys.exit(f"ABORT: {n} Excel process(es) running.")

    import win32com.client
    app = win32com.client.DispatchEx("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    app.EnableEvents = False
    wb = None
    rows = []
    try:
        wb = app.Workbooks.Open(str(TARGET), UpdateLinks=0, ReadOnly=True)
        app.Calculation = -4135
        ws = wb.Worksheets(SHEET)
        used = ws.UsedRange
        last = used.Row + used.Rows.Count - 1
        print(f"{SHEET}: rows to {last}")

        loc_rows, cs_rows, other = {}, set(), set()
        for r in range(1, last + 1):
            lab = ws.Cells(r, 2).Value
            f = str(ws.Cells(r, 3).Formula)
            if not f.startswith("="):
                continue
            hits_loc = [int(m) for m in
                        re.findall(r"'IN - Location'!\$?[A-L]\$?(\d+)", f)]
            hits_cs = [int(m) for m in
                       re.findall(r"'CALC - CoreScratchpad'!\$?[A-L]\$?(\d+)", f)]
            hits_sched = re.findall(r"'IN - Schedule'", f)
            for h in hits_loc:
                loc_rows.setdefault(h, []).append(r)
            cs_rows.update(hits_cs)
            for m in re.findall(r"'([^']+)'!", f):
                if m not in ("IN - Location", "CALC - CoreScratchpad"):
                    other.add(m)
            rows.append({
                "Row": r, "Label": str(lab or ""),
                "ReadsLocationRows": " ".join(str(x) for x in sorted(set(hits_loc))),
                "ReadsCoreScratchpad": " ".join(str(x) for x in sorted(set(hits_cs))),
                "AlreadySchedule": "yes" if hits_sched else "",
                "Formula": f[:180],
            })

        print(f"\n  rows with formulas: {len(rows)}")
        print(f"  distinct 'IN - Location' rows read: {len(loc_rows)}")
        print(f"  distinct CoreScratchpad rows read : {len(cs_rows)}")
        print(f"  other sheets referenced           : {sorted(other)}")

        print("\n--- IN - Location rows read, classified ---")
        b = c = u = 0
        for lr in sorted(loc_rows):
            if lr in BUILDING_LEVEL:
                kind, name = "BUILDING", BUILDING_LEVEL[lr]
                b += 1
            elif lr in CONTENTS_LEVEL:
                kind, name = "contents", CONTENTS_LEVEL[lr]
                c += 1
            else:
                kind, name = "UNCLASSIFIED", "?"
                u += 1
            print(f"   row {lr:>4} {kind:<13} {name:<26} "
                  f"used by {len(loc_rows[lr])} calc row(s)")
        print(f"\n  building-level {b}   contents-level {c}   unclassified {u}")

        print("\n--- premium roll-up ---")
        for r in range(1, last + 1):
            lab = ws.Cells(r, 2).Value
            if isinstance(lab, str) and "PREMIUM" in lab.upper():
                print(f"   row {r:>4} {lab[:34]:<34} {str(ws.Cells(r,3).Formula)[:60]}")
        print(f"   OUT_Prem_Contents = "
              f"{wb.Names('OUT_Prem_Contents').RefersToRange.Formula}")

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

    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"\nwrote {OUT.name} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
