"""R-4 -- give IRPM, Package Mod and Multi-Premium/Dispersion a real input.

**The survey changed this job's scope.** R-4 was proposed as "every coverage tab
carries its own flat 1.0, point them all at one block". Half of that was already
wrong:

* ``LCM`` is **not** a flat 1.0 -- it is a genuine per-state lookup
  (``INDEX(LCM!$B$2:$B$47, MATCH(CALC - CoreScratchpad!C2, ...))``) that already resolves
  per item. Leave it alone.
* ``CyberExcl*`` is **already** single-sourced -- every cell gates off
  ``'IN - Policy'!$F$3/$F$4/$F$5``. Leave it alone. Its 0.997-vs-0.996 split
  between Broad and Special is **filed data, not duplication**; collapsing it
  would re-introduce the premium bug fixed in BUILD-LOG Entry 28.

What is genuinely broken is narrower and worse: **IRPM, PackageMod and
MultiPremiumDispersion are hard-coded ``1.0`` in 120 cells and have no input
anywhere in the workbook.** Applying an IRPM today means editing 40 cells by hand.

All 120 literals sit on ``CALC - Bldg Rating``; Contents and BI chain-reference
it, so repointing that one sheet fixes all three coverages.

Verification is two-sided: premiums must be **unchanged** with the new inputs at
1.0, and must **move** when one is set to 0.9 -- proving the wiring is live and not
merely harmless.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

TARGET = Path(r"F:\Spreadsheet_Rater\CF\CFRater1.02.xlsb")
FORBIDDEN = "cfrater1.01.xlsb"

PREMIUMS = ["OUT_Prem_Building", "OUT_Prem_Contents", "OUT_Prem_BI",
            "OUT_Prem_SCBuilding", "OUT_Prem_SCBI", "OUT_Prem_Total"]

#: New inputs on `IN - Policy`: (row, label, default, defined-name)
NEW_INPUTS = [
    (22, "IRPM Factor:", 1.0, "IN_Pol_IRPMFactor"),
    (23, "Package Mod Factor:", 1.0, "IN_Pol_PackageModFactor"),
    (24, "Multi-Premium & Dispersion Credit Factor:", 1.0,
     "IN_Pol_MultiPremiumDispersionFactor"),
]

#: Rows on `CALC - Bldg Rating` holding the literals, one per form
#: (Basic Group I, Basic Group II, Broad, Special) -> the name to point at.
REPOINT = {
    "IN_Pol_IRPMFactor": [23, 53, 77, 103],
    "IN_Pol_MultiPremiumDispersionFactor": [27, 57, 81, 107],
    "IN_Pol_PackageModFactor": [28, 58, 82, 108],
}
ITEM_COLS = range(3, 13)          # C..L


def preflight() -> None:
    n = subprocess.run(["powershell", "-NoProfile", "-Command",
                        "(Get-Process EXCEL -ErrorAction SilentlyContinue).Count"],
                       capture_output=True, text=True).stdout.strip()
    if n and n not in {"0", ""}:
        sys.exit(f"ABORT: {n} Excel process(es) running.")
    if TARGET.name.lower() == FORBIDDEN:
        sys.exit("ABORT: refusing to write to the live rater.")
    print(f"preflight OK -- target {TARGET.name}")


def read_premiums(wb) -> dict[str, float]:
    return {p: wb.Names(p).RefersToRange.Value for p in PREMIUMS}


def show(tag: str, prem: dict) -> None:
    print(f"  {tag:<26} " + "  ".join(f"{k.split('_')[-1]}={v}" for k, v in prem.items()))


def main() -> int:
    preflight()
    import win32com.client
    app = win32com.client.DispatchEx("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    app.EnableEvents = False
    wb = None
    try:
        wb = app.Workbooks.Open(str(TARGET), UpdateLinks=0)
        app.Calculation = -4135                             # manual
        pol = wb.Worksheets("IN - Policy")
        bldg = wb.Worksheets("CALC - Bldg Rating")

        app.CalculateFull()
        baseline = read_premiums(wb)
        show("baseline", baseline)

        # --- 1. add the three inputs -----------------------------------
        pol.Cells(21, 2).Value = "Policy Factors"
        for row, label, default, name in NEW_INPUTS:
            if pol.Cells(row, 2).Value not in (None, "", label):
                sys.exit(f"ABORT: 'IN - Policy'!B{row} is occupied "
                         f"({pol.Cells(row, 2).Value!r}) -- not overwriting.")
            pol.Cells(row, 2).Value = label
            pol.Cells(row, 3).Value = default
            ref = f"='IN - Policy'!$C${row}"
            try:
                wb.Names(name).RefersTo = ref
            except Exception:                               # noqa: BLE001
                wb.Names.Add(Name=name, RefersTo=ref)
        print(f"\n  added {len(NEW_INPUTS)} inputs + names on 'IN - Policy' rows 22-24")

        # --- 2. repoint the 120 literals -------------------------------
        repointed = 0
        for name, rows in REPOINT.items():
            for r in rows:
                for c in ITEM_COLS:
                    bldg.Cells(r, c).Formula = f"={name}"
                    repointed += 1
        print(f"  repointed {repointed} cells on 'CALC - Bldg Rating'")

        # --- 3. unchanged at 1.0? --------------------------------------
        app.CalculateFull()
        after = read_premiums(wb)
        show("after repoint (all 1.0)", after)
        if after != baseline:
            sys.exit("ABORT: premiums changed at 1.0 -- NOT saving.\n"
                     f"  baseline {baseline}\n  after    {after}")
        print("  -> unchanged, as required")

        # --- 4. responsive at 0.9? -------------------------------------
        pol.Cells(22, 3).Value = 0.9
        app.CalculateFull()
        moved = read_premiums(wb)
        show("IRPM = 0.9", moved)
        if moved == baseline:
            sys.exit("ABORT: premiums did NOT move when IRPM set to 0.9 -- "
                     "the wiring is inert. NOT saving.")
        print("  -> premiums moved, so the wiring is live")

        pol.Cells(22, 3).Value = 1.0
        app.CalculateFull()
        restored = read_premiums(wb)
        show("restored to 1.0", restored)
        if restored != baseline:
            sys.exit("ABORT: did not restore to baseline -- NOT saving.")
        print("  -> restored exactly")

        app.Calculation = -4105                             # automatic
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
    print("Instance closed. CFRater1.01.xlsb never opened.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
