#!/usr/bin/env python3
"""OI-134: which ISO-required inputs change the premium silently when left out? -> gl_engine/schema/rating_inputs.json

For every state's console request (`console.workbench.build`) at each date below, drop each ISO-required input
the request carries, one at a time, rate it, and classify the drop:

    silent  rated, the premium moved, nothing refused         -> a rating input: the engine must refuse
    stops   the engine refused                                -> already safe
    same    rated, premium unchanged                          -> informational: a warning at most

    python scripts/erc/57_rating_inputs.py            # measure and print
    python scripts/erc/57_rating_inputs.py --write    # also write gl_engine/schema/rating_inputs.json

Run it with the refusal off (`ERC_RATING_INPUTS=off`): with it on, every rating input already stops.
First run 2026-10-13: 2,241 drops at 2027-05-01, 551 silent across 14 fields (e.g. Subline left out: $0;
a premium basis left out: $6,783,982 in AK). No ISO calls.
"""
from __future__ import annotations

import argparse
import collections
import copy
import datetime as dt
import glob
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
OUT = ROOT / "gl_engine" / "schema" / "rating_inputs.json"
DATES = ("20260801", "20270501")       # the editions in force now, and past the 2027-04-01 cliff


def one(job):
    st, date = job
    os.environ["ERC_RATING_INPUTS"] = "off"
    sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
    from console import workbench as WB
    from gl_engine.rating import Kernel
    from gl_engine.resolve import ResolvedBook
    from gl_engine.schema import Schema
    req = WB.build("GL", st, {"effective_date": date})
    k = Kernel(mode="strict-erc")
    base = k.rate(copy.deepcopy(req))
    if not base.complete:
        return [(st, date, "-", "base-stopped", None, None)]
    sch = Schema.for_book(ResolvedBook(k.resolver.resolve(base.juris, base.asof)))
    req_fields = {(f.table, f.column) for f in sch if f.policy_required and f.is_input}

    def visit(obj, table, path):
        for key, val in list(obj.items()):
            if isinstance(val, list):
                for i, item in enumerate(val):
                    if isinstance(item, dict):
                        yield from visit(item, key, path + [key, i])
            elif isinstance(val, dict):
                yield from visit(val, f"{table}.{key}", path + [key])
            elif (table, key) in req_fields:
                yield path, key, f"{table}.{key}"

    out = []
    for path, col, name in visit(req["body"]["GeneralLiability"][0], "GeneralLiability", []):
        r2 = copy.deepcopy(req)
        d = r2["body"]["GeneralLiability"][0]
        for p in path:
            d = d[p]
        d.pop(col, None)
        try:
            r = k.rate(r2)
            cls = "stops" if not r.complete else ("silent" if r.premium != base.premium else "same")
            prem = str(r.premium) if r.complete else None
        except Exception as exc:                     # noqa: BLE001 - a refusal by another name
            cls, prem = "stops", type(exc).__name__
        out.append((st, date, name, cls, str(base.premium), prem))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--jobs", type=int, default=6)
    a = ap.parse_args()
    states = sorted(Path(p).parent.name for p in glob.glob(str(ROOT / "Engine_Payloads" / "*" / "submission.json")))
    rows = []
    with ProcessPoolExecutor(a.jobs) as ex:
        for res in ex.map(one, [(s, d) for d in DATES for s in states]):
            rows.extend(res)
    tally = collections.Counter(r[3] for r in rows)
    by = collections.defaultdict(lambda: {"silent": set(), "stops": 0, "same": 0, "example": ""})
    for st, date, name, cls, b, p in rows:
        if name == "-":
            continue
        e = by[name]
        if cls == "silent":
            e["silent"].add(f"{st}@{date}")
            e["example"] = e["example"] or f"{st} {date}: {b} -> {p}"
        elif cls in ("stops", "same"):
            e[cls] += 1
    silent = {n: e for n, e in by.items() if e["silent"]}
    print(f"{len(rows)} drops, {len(states)} states x {list(DATES)}: {dict(tally)}")
    for n, e in sorted(silent.items(), key=lambda x: -len(x[1]["silent"])):
        print(f"  {len(e['silent']):3} silent  {n:72} (stops {e['stops']}, same {e['same']})  e.g. {e['example']}")
    if a.write:
        OUT.write_text(json.dumps({
            "what": "ISO-required inputs whose absence changes the premium with no refusal (OI-134). "
                    "The engine refuses a rating that leaves one out where ISO's conditions require it.",
            "measured": str(dt.date.today()), "by": "scripts/erc/57_rating_inputs.py", "dates": list(DATES),
            "drops": dict(tally),
            "fields": sorted(silent),
            "evidence": {n: {"silent_in": len(e["silent"]), "example": e["example"]} for n, e in sorted(silent.items())},
        }, indent=1) + "\n", encoding="utf-8")
        print(f"wrote {OUT.relative_to(ROOT)}: {len(silent)} fields")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
