"""RC-4: build "more states" scenarios for `137_scenario_three_way.py`.

The four Schedule locations are four risk shapes (1 FL Legal Liability + Special Class,
2 NY building, 3 AK Extra Expense, 4 CA). Each scenario moves them to four new states, with
inputs taken from the rater's OWN lists, so nothing is invented: the state's first ZIP in
`TBL - ZipCityState`, and the first entry of its `<ST>_bgiterr` / `<ST>_bgiiterr` /
`<ST>_Special` dropdown lists. Location states already compared (FL, NY, AK, CA) and PR
(no RAaS entitlement) are skipped. Column H (District) gets the standard formula, because
row 8 holds CA's typed district.

Read-only. Writes scenarios/cf_states/states_NN.json.

    python scripts/cf/138_make_state_scenarios.py
"""
from __future__ import annotations

import json
import sys
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
p4a = import_module("112_r8_phase4a_building")

OUT = Path(__file__).resolve().parents[2] / "scenarios" / "cf_states"
SKIP = {"FL", "NY", "AK", "CA", "PR"}
ROWS = (5, 6, 7, 8)                          # the four location slots


def first(wb, name):
    try:
        v = wb.Names(name).RefersToRange.Value
    except Exception:                                         # noqa: BLE001
        return None
    cells = [r[0] for r in v] if isinstance(v, tuple) else [v]
    return next((c for c in cells if c not in (None, "")), None)


def main() -> int:
    pre = p4a.excel_pids()
    if pre:
        sys.exit(f"ABORT: Excel running {pre}")
    import win32com.client
    app = win32com.client.DispatchEx("Excel.Application")
    app.Visible, app.DisplayAlerts = False, False
    wb = None
    plan, problems = [], []
    try:
        wb = app.Workbooks.Open(str(p4a.TARGET), UpdateLinks=0, ReadOnly=True)
        states = [r[0] for r in wb.Worksheets("TBL - LCM").Range("A2:A47").Value if r[0] and r[0] not in SKIP]
        z = wb.Worksheets("TBL - ZipCityState").UsedRange.Value
        zips = {}
        for row in z[1:]:
            if row[2] and row[2] not in zips and row[0]:
                zips[row[2]] = int(row[0])
        h_r1c1 = wb.Worksheets("IN - Schedule").Range("H5").FormulaR1C1
        for st in states:
            vals = {"zip": zips.get(st), "g": first(wb, f"{st}_bgiterr"),
                    "i": first(wb, f"{st}_bgiiterr"), "j": first(wb, f"{st}_Special")}
            missing = [k for k, v in vals.items() if v is None]
            if missing:
                problems.append(f"{st}: no {missing} in the rater's own lists -- skipped")
                continue
            plan.append((st, vals))
    finally:
        if wb is not None:
            wb.Close(SaveChanges=False)
        app.Quit()
        del app
        p4a.reap_orphans(set(pre))
    OUT.mkdir(parents=True, exist_ok=True)
    for f in OUT.glob("states_*.json"):
        f.unlink()
    for n in range(0, len(plan), len(ROWS)):
        batch = plan[n:n + len(ROWS)]
        edits = []
        for r, (st, v) in zip(ROWS, batch):
            S = "IN - Schedule"
            edits += [{"sheet": S, "cell": f"C{r}", "value": st},
                      {"sheet": S, "cell": f"D{r}", "value": v["zip"]},
                      {"sheet": S, "cell": f"G{r}", "value": v["g"]},
                      {"sheet": S, "cell": f"I{r}", "value": v["i"]},
                      {"sheet": S, "cell": f"J{r}", "value": v["j"]},
                      {"sheet": S, "cell": f"H{r}", "r1c1": h_r1c1},
                      {"sheet": S, "cell": f"O{r}", "value": "Not Applicable"},
                      {"sheet": S, "cell": f"P{r}", "value": "Not Applicable"},
                      {"sheet": S, "cell": f"Q{r}", "value": "Not Applicable"}]
        name = f"states_{n // len(ROWS) + 1:02d}"
        (OUT / f"{name}.json").write_text(json.dumps(
            {"name": name, "states": [s for s, _ in batch], "edits": edits}, indent=1), encoding="utf-8")
        print(f"{name}: {', '.join(s for s, _ in batch)}")
    for p in problems:
        print("  NOTE", p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
