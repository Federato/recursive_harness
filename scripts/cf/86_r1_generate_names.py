"""R-1, part 1 -- derive a defined-name for every input cell in the rater.

Reads the Step 1 inventory (``CF_Payload_Excel_Input_Inventory.csv``) and emits a
name plan: one row per name, with the exact sheet and range it will point at.

**This script writes nothing to any workbook.** It produces a plan for
``87_r1_apply_names.py`` to apply, so the plan can be reviewed first.

Naming scheme
-------------
``IN_Pol_<Thing>``   a single cell on ``IN - Policy``
``IN_Loc_<Thing>``   the row range ``C:L`` on ``IN - Location`` (10 item columns)
``IN_SC_<Thing>``    the row range ``C:E`` on ``IN - Special Class`` (3 item columns)
``OUT_<Thing>``      a premium output cell

Item tabs get a **range per input row**, not a name per cell, because every
formula that reads them is an ``INDEX(range, 1, ordinal)`` -- naming the row is
what makes that formula stable when rows move.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
INVENTORY = REPO / "CF_Algorithm" / "CF_Payload_Excel_Input_Inventory.csv"
PLAN = REPO / "CF_Algorithm" / "CF_R1_Name_Plan.csv"

#: Item columns per sheet -- how wide the named row range is.
SPAN = {
    "IN - Policy": None,                 # scalar, single cell
    "IN - Location": ("C", "L"),         # 10 items
    "IN - Special Class": ("C", "E"),    # 3 items
}

PREFIX = {
    "IN - Policy": "IN_Pol_",
    "IN - Location": "IN_Loc_",
    "IN - Special Class": "IN_SC_",
}

#: Long phrases -> short tokens, so names stay readable at a glance.
SHORTEN = [
    ("Business Income", "BI"),
    ("Personal Property", "PP"),
    ("Special Class", "SC"),
    ("Windstorm or Hail", "WindHail"),
    ("Windstorm/Hail", "WindHail"),
    ("Sub Standard Condition", "SubStd"),
    ("Multi Residential Property Special Credits", "MultiResCredit"),
    ("Building Code Effectiveness Grade", "BCEG"),
    ("Additional Insurable Interest", "AddlInsurableInt"),
    ("Limitations on Coverage for Roof Surfacing", "RoofSurfacing"),
    ("Previous or Intended", "PrevIntended"),
    ("Type of Watchman Service", "WatchmanType"),
    ("Type of Burglary Alarm System", "BurglaryAlarmType"),
    ("Extra Expense Loss Payment Schedule", "ExtraExpenseSchedule"),
    ("Max Period of Indemnity", "MaxPeriodIndemnity"),
    ("Monthly Limit of Indemnity", "MonthlyLimitIndemnity"),
    ("Physical Condition & Housekeeping", "PhysCondition"),
    ("Heating and Cooking", "HeatingCooking"),
    ("Location of Heating Plant", "HeatingPlantLoc"),
    ("Coverage Type", "CovType"),
    ("Coverage Form", "CovForm"),
    ("Specific/Tentative Rate", "SpecificRate"),
    ("Class Description", "ClassDesc"),
    ("Item Description", "ItemDesc"),
    ("Protection Class", "ProtClass"),
    ("Construction", "Constr"),
    ("Deductible", "Ded"),
    ("Coinsurance", "Coins"),
    ("Territory", "Terr"),
    ("Exclusion", "Excl"),
    ("Excluded", "Excl"),
    ("Percentage", "Pct"),
    ("Number of", "Num"),
    ("Included", "Incl"),
]


#: (sheet, row) -> name, where the derived name reads badly. Hand-set, few.
OVERRIDES = {
    ("IN - Location", "4"): "IN_Loc_LocationNum",
    ("IN - Location", "5"): "IN_Loc_BuildingNum",
    ("IN - Location", "18"): "IN_Loc_District",
    ("IN - Location", "23"): "IN_Loc_BCEG",
    ("IN - Location", "61"): "IN_Loc_ConstrDesc",
    ("IN - Location", "93"): "IN_Loc_AddlInsurableIntDesc",
    ("IN - Special Class", "4"): "IN_SC_LocationNum",
    ("IN - Special Class", "5"): "IN_SC_ItemNum",
}

#: Outputs worth naming too -- the premium summary on `IN - Policy`.
#: Not in the inventory, which only captured the label/value input columns.
OUTPUTS = [
    ("OUT_Prem_Building", "IN - Policy", "I", "3", "Building Premium"),
    ("OUT_Prem_Contents", "IN - Policy", "I", "4", "Contents Premium"),
    ("OUT_Prem_BI", "IN - Policy", "I", "5", "Business Income Premium"),
    ("OUT_Prem_SCBuilding", "IN - Policy", "I", "6", "Special Class - Building Premium"),
    ("OUT_Prem_SCBI", "IN - Policy", "I", "7", "Special Class - BI Premium"),
    ("OUT_Prem_Total", "IN - Policy", "I", "9", "Total Premium"),
]


def to_name(label: str) -> str:
    """Rater label -> a legal, readable Excel defined-name fragment."""
    text = label.strip().rstrip(":").strip()
    for long, short in SHORTEN:
        text = re.sub(re.escape(long), short, text, flags=re.IGNORECASE)
    # Title-case whatever words are left, then strip to alphanumerics.
    words = re.split(r"[^A-Za-z0-9]+", text)
    out = "".join(w[:1].upper() + w[1:] if w and w[0].islower() else w
                  for w in words if w)
    return out or "Unnamed"


def main() -> int:
    rows = [r for r in csv.DictReader(INVENTORY.open(encoding="utf-8"))
            if r["Kind"] == "FIELD"]

    plan, used = [], {}
    for row in rows:
        sheet = row["Sheet"]
        name = OVERRIDES.get((sheet, row["Row"]))
        if name is None:
            name = PREFIX[sheet] + to_name(row["Label"])

        # Disambiguate collisions rather than silently dropping one.
        if name in used:
            n = 2
            while f"{name}{n}" in used:
                n += 1
            name = f"{name}{n}"
        used[name] = True

        excel_row = row["Row"]
        span = SPAN[sheet]
        if span is None:
            ref = f"'{sheet}'!${row['FirstValueCell'][0]}${excel_row}"
        else:
            lo, hi = span
            ref = f"'{sheet}'!${lo}${excel_row}:${hi}${excel_row}"

        plan.append({
            "Name": name,
            "RefersTo": "=" + ref,
            "Sheet": sheet,
            "Row": excel_row,
            "Kind": "cell" if span is None else "row range",
            "Label": row["Label"].strip().rstrip(":"),
            "Sample": row["SampleValue"],
        })

    for name, sheet, col, excel_row, label in OUTPUTS:
        plan.append({
            "Name": name,
            "RefersTo": f"='{sheet}'!${col}${excel_row}",
            "Sheet": sheet, "Row": excel_row, "Kind": "cell",
            "Label": label, "Sample": "",
        })

    with PLAN.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(plan[0]))
        w.writeheader()
        w.writerows(plan)

    by_sheet: dict[str, int] = {}
    for p in plan:
        by_sheet[p["Sheet"]] = by_sheet.get(p["Sheet"], 0) + 1

    print(f"wrote {PLAN.name} -- {len(plan)} names\n")
    for sheet, n in by_sheet.items():
        print(f"  {sheet:<24} {n:>3} names ({PREFIX[sheet]}*)")

    longest = max(len(p["Name"]) for p in plan)
    print(f"\n  longest name: {longest} chars (Excel limit 255)")
    bad = [p for p in plan if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.]*", p["Name"])]
    print(f"  illegal names: {len(bad)}")
    dupes = len(plan) - len({p["Name"] for p in plan})
    print(f"  duplicates after disambiguation: {dupes}")

    print("\n--- sample ---")
    for p in plan[:6] + plan[20:26]:
        print(f"  {p['Name']:<34} {p['RefersTo']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
