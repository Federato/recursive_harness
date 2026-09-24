"""RC-4: summarise the "more states" scenario runs (latest run of each states_NN batch).

For every state: lines that match (Excel = ISO = engine), ISO refusals with their message, and
every mismatch, tagged by who disagrees:
  RATER   Excel differs from ISO, engine agrees with ISO   -> rater defect or rater assumption
  ENGINE  engine differs from ISO, Excel agrees             -> engine defect
  BOTH    Excel and engine both differ from ISO
Writes CF_Algorithm/CF_RC4_State_Results.csv.
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ROOT = REPO / "results" / "cf-scenarios"


def main() -> int:
    rows, refused, summary = [], {}, {}
    for batch in sorted(ROOT.glob("states_*")):
        runs = sorted(p for p in batch.iterdir() if (p / "comparison.json").exists())
        if not runs:
            continue
        run = runs[-1]
        for f in run.glob("*_refusal.txt"):
            t = f.read_text(errors="ignore")
            m = re.search(r'"Message":"([^"]*)"', t)
            refused[f.name[:2]] = (m.group(1) if m else t)[:260]
        for r in json.loads((run / "comparison.json").read_text()):
            st = r["state"]
            s = summary.setdefault(st, {"match": 0, "lines": 0})
            s["lines"] += 1
            e, i, n = r["excel"], r["iso"], r["engine"]
            if i is None:
                continue
            if e == i and n == i:
                s["match"] += 1
                continue
            who = "RATER" if n == i else ("ENGINE" if e == i else "BOTH")
            rows.append({"state": st, "coverage": r["coverage"], "form": r["form"], "excel": e, "iso": i,
                         "engine": n, "excel_minus_iso": None if e is None else round(e - i, 2), "who": who,
                         "batch": batch.name})
    out = REPO / "CF_Algorithm" / "CF_RC4_State_Results.csv"
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["state", "coverage", "form", "excel", "iso", "engine",
                                            "excel_minus_iso", "who", "batch"])
        w.writeheader()
        w.writerows(rows)
    clean = sorted(s for s, v in summary.items() if v["match"] == v["lines"] and s not in refused)
    print(f"States run: {len(summary)}   all lines match: {len(clean)}   refused: {len(refused)}")
    print("  clean:", ", ".join(clean))
    for st, msg in sorted(refused.items()):
        print(f"  REFUSED {st}: {msg}")
    for st in sorted({r["state"] for r in rows}):
        rs = [r for r in rows if r["state"] == st]
        print(f"  {st}: " + "; ".join(f"{r['coverage']} {r['form']} {r['excel_minus_iso']:+g} [{r['who']}]" for r in rs))
    print(f"\n{len(rows)} mismatched lines -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
