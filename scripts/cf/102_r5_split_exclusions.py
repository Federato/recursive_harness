"""R-5 -- one exclusion input per coverage group, defaulting to the master.

ISO files **five** exclusion records per peril -- Structure, PrsnlProp, BusnIncome,
SpecialClass, SpclClassBusnIncome -- so 15 records. The workbook drives them from 6
inputs, which means a risk cannot exclude a peril on Business Income but keep it on
the building. Backlog S-1/S-2/S-3, which described only two of the five.

**Design, per the user's instruction "default all coverages to yes if the record
exists":** each new per-group cell is a formula pointing at its master
(``=C75``). Electing an exclusion therefore turns it on for every group exactly as
today; a single group is split off by typing ``No`` over one cell.

**Rows are appended, never inserted.** Inserting mid-sheet would shift every
documented row number in this project's docs. The new blocks start below the
existing content, so nothing moves.

**Not every consumer is rewired, and that is deliberate.** Seven of the 23 read the
input through shared ``CALC - CoreScratchpad`` helpers that serve more than one
coverage, or -- in one case -- cross sheets in a way that looks like a defect. Those
are left on the master and reported, rather than being assigned to a group on a
guess. Splitting them needs a trace of who consumes each helper.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

TARGET = Path(r"C:\Projects\Spreadsheet_Rater\CF\CFRater1.02.xlsb")
FORBIDDEN = "cfrater1.01.xlsb"

PREMIUMS = ["OUT_Prem_Building", "OUT_Prem_Contents", "OUT_Prem_BI",
            "OUT_Prem_SCBuilding", "OUT_Prem_SCBI", "OUT_Prem_Total"]
ITEM_COLS = range(3, 13)

#: sheet -> (header row, section title, [(row, label, master row, defined name)])
NEW_INPUTS = {
    "IN - Location": (95, "Exclusions by Coverage  (defaults to the election above "
                          "- type No over one cell to split a single coverage)", [
        (96, "Windstorm or Hail - Building:", 75, "IN_Loc_WindHailExcl_Bldg"),
        (97, "Windstorm or Hail - Contents:", 75, "IN_Loc_WindHailExcl_Contents"),
        (98, "Windstorm or Hail - Business Income:", 75, "IN_Loc_WindHailExcl_BI"),
        (99, "Vandalism - Building:", 76, "IN_Loc_VandalismExcl_Bldg"),
        (100, "Vandalism - Contents:", 76, "IN_Loc_VandalismExcl_Contents"),
        (101, "Vandalism - Business Income:", 76, "IN_Loc_VandalismExcl_BI"),
        (102, "Theft - Building:", 77, "IN_Loc_TheftExcl_Bldg"),
        (103, "Theft - Contents:", 77, "IN_Loc_TheftExcl_Contents"),
        (104, "Theft - Business Income:", 77, "IN_Loc_TheftExcl_BI"),
    ]),
    "IN - Special Class": (48, "Exclusions by Coverage  (defaults to the election "
                               "above)", [
        (49, "Vandalism - Special Class:", 28, "IN_SC_VandalismExcl_SC"),
        (50, "Vandalism - SC Business Income:", 28, "IN_SC_VandalismExcl_SCBI"),
        (51, "Windstorm or Hail - Special Class:", 32, "IN_SC_WindHailExcl_SC"),
        (52, "Windstorm or Hail - SC Business Income:", 32, "IN_SC_WindHailExcl_SCBI"),
        (53, "Theft - Special Class:", 35, "IN_SC_TheftExcl_SC"),
        (54, "Theft - SC Business Income:", 35, "IN_SC_TheftExcl_SCBI"),
    ]),
}

#: (calc sheet, row) -> (input sheet, old master row, new group row)
#: Only consumers that unambiguously belong to ONE coverage group.
REWIRE = {
    ("CALC - Bldg Rating", 36):      ("IN - Location", 75, 96),
    ("CALC - Bldg Rating", 37):      ("IN - Location", 75, 96),
    ("CALC - Bldg Rating", 42):      ("IN - Location", 75, 96),
    ("CALC - Bldg Rating", 49):      ("IN - Location", 75, 96),
    ("CALC - Contents Rating", 34):  ("IN - Location", 75, 97),
    ("CALC - Contents Rating", 35):  ("IN - Location", 75, 97),
    ("CALC - Contents Rating", 39):  ("IN - Location", 75, 97),
    ("CALC - BI Rating", 36):        ("IN - Location", 75, 98),
    ("CALC - Bldg Rating", 93):      ("IN - Location", 77, 102),
    ("CALC - BI Rating", 66):        ("IN - Location", 77, 104),
    ("CALC - Special Class", 7):     ("IN - Special Class", 28, 49),
    ("CALC - Special Class", 27):    ("IN - Special Class", 32, 51),
    ("CALC - Special Class", 29):    ("IN - Special Class", 32, 51),
    ("CALC - Special Class", 31):    ("IN - Special Class", 32, 51),
    ("CALC - Special Class", 72):    ("IN - Special Class", 35, 53),
    ("CALC - Special Class", 147):   ("IN - Special Class", 35, 54),
    ("CALC - CoreScratchpad", 249):  ("IN - Special Class", 28, 50),
}

#: Left on the master on purpose -- reported, not silently assigned.
NOT_REWIRED = [
    ("CALC - Special Class", 26, "reads 'IN - Location'!C75 (the LOCATION wind/hail "
     "input) for the Special Class BGII base rate, while rows 27/29/31 in the same "
     "block read the SPECIAL CLASS input. Looks like a defect; confirming needs ISO's "
     "rules, and changing it is a behaviour change, not a split"),
    ("CALC - CoreScratchpad", 26, "Vandalism lookup key -- shared helper, consumers "
     "untraced"),
    ("CALC - CoreScratchpad", 60, "Windstorm copy -- shared helper"),
    ("CALC - CoreScratchpad", 175, "Theft lookup key -- shared helper"),
    ("CALC - CoreScratchpad", 182, "Final deductible factor -- shared helper"),
    ("CALC - CoreScratchpad", 205, "Wstormexclusion key -- shared helper"),
]


def show(tag, prem):
    print(f"  {tag:<30} " + "  ".join(f"{k.split('_')[-1]}={v}" for k, v in prem.items()))


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
        show("baseline", baseline)

        # --- 1. append the per-group inputs ----------------------------
        added = 0
        for sheet, (hdr_row, title, rows) in NEW_INPUTS.items():
            ws = wb.Worksheets(sheet)
            for r, label, master, name in rows:
                if ws.Cells(r, 2).Value not in (None, "", label):
                    sys.exit(f"ABORT: {sheet}!B{r} occupied "
                             f"({ws.Cells(r, 2).Value!r}) -- not overwriting.")
            ws.Cells(hdr_row, 2).Value = title
            # Mirror the master across the FULL C:L range on both sheets.
            # `IN - Special Class` shows only three item slots in its header, but
            # its exclusion rows are populated to column H and `CALC - Special
            # Class` reads C:L. Writing the new rows C:E left F:L pointing at empty
            # cells, which took the Special Class premium to #VALUE!. Mirror the
            # master's full width and the behaviour is identical by construction.
            span, hi = "L", 12
            for r, label, master, name in rows:
                ws.Cells(r, 2).Value = label
                for c in range(3, hi + 1):
                    col = chr(ord("A") + c - 1)
                    ws.Cells(r, c).Formula = f"={col}{master}"
                ref = f"='{sheet}'!$C${r}:${span}${r}"
                try:
                    wb.Names(name).RefersTo = ref
                except Exception:                           # noqa: BLE001
                    wb.Names.Add(Name=name, RefersTo=ref)
                added += 1
            print(f"  {sheet}: {len(rows)} per-group inputs appended from row {rows[0][0]}")
        print(f"  {added} new inputs, all defaulting to their master")

        # --- 2. rewire the unambiguous consumers -----------------------
        rewired = 0
        for (sheet, row), (in_sheet, old, new) in REWIRE.items():
            ws = wb.Worksheets(sheet)
            pat = re.compile(rf"('{re.escape(in_sheet)}'!\$?[A-L]\$?){old}\b")
            for c in ITEM_COLS:
                f = str(ws.Cells(row, c).Formula)
                if not f.startswith("="):
                    continue
                new_f, k = pat.subn(rf"\g<1>{new}", f)
                if k:
                    ws.Cells(row, c).Formula = new_f
                    rewired += 1
        print(f"  rewired {rewired} cells across {len(REWIRE)} consumer rows")
        print(f"  left on the master on purpose: {len(NOT_REWIRED)} rows (see record)")

        # --- 3. unchanged at defaults ----------------------------------
        app.CalculateFull()
        after = {p: wb.Names(p).RefersToRange.Value for p in PREMIUMS}
        show("after (all defaulted)", after)
        if after != baseline:
            sys.exit("ABORT: premiums changed while everything still defaults "
                     "to its master -- NOT saving.")
        print("  -> unchanged, as required")

        # --- 4. a split must move ONE coverage only --------------------
        # Split Theft-Building across EVERY item, not just item 1. Item 1 is a
        # Legal Liability risk, and Legal Liability picks the rate up three steps
        # earlier in the chain -- so it drops the theft exclusion factor entirely
        # (harness chunk 8). Testing on item 1 alone showed the factor moving
        # 0.88 -> 1.0 while the premium stayed put, which looks exactly like an
        # inert split and is not one.
        loc = wb.Worksheets("IN - Location")
        before_theft = [str(loc.Cells(102, c).Formula) for c in ITEM_COLS]
        for c in ITEM_COLS:
            loc.Cells(102, c).Value = "No"      # Theft - Building only
        app.CalculateFull()
        split = {p: wb.Names(p).RefersToRange.Value for p in PREMIUMS}
        show("Theft-Building = No", split)
        if split["OUT_Prem_Building"] == baseline["OUT_Prem_Building"]:
            sys.exit("ABORT: Building did not move -- the split is inert. NOT saving.")
        if split["OUT_Prem_Contents"] != baseline["OUT_Prem_Contents"]:
            sys.exit("ABORT: Contents moved too -- the split is not isolated. NOT saving.")
        print("  -> Building moved, Contents did not: the split is real and isolated")

        for c, f in zip(ITEM_COLS, before_theft):
            loc.Cells(102, c).Formula = f
        app.CalculateFull()
        restored = {p: wb.Names(p).RefersToRange.Value for p in PREMIUMS}
        show("restored", restored)
        if restored != baseline:
            sys.exit("ABORT: did not restore -- NOT saving.")

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
