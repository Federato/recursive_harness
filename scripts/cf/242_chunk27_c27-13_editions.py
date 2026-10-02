#!/usr/bin/env python3
"""Chunk 27 C27-13 (OI-105): which state package ISO serves on which date, against what our corpus resolves. Live ISO.

ISO names the package it rated with in the response header (`"Scheme": "CF CA 20251201 V01 Scheme"`), and in a refusal's
text ("Project: CF OR 20260601 V01"). So each state's portable policy (237_'s, the one all 46 states rated in chunk 26)
(or a single building, whose refusal also names the package) is sent at a ladder of dates and the named package compared with `book_for(j, date)`'s state package.

  dates   2026-09-17 (every comparison so far), 2026-11-01, 2027-01-01, 2027-04-01, 2027-07-01, 2027-10-01
  output  results/cf-raas/chunk27_c27-13_editions.json, and per state: the dates where ISO's package differs from ours

Predicted before the run: at 2026-09-17 ISO and the corpus name the same package in all 46 states (every live comparison
since chunk 11 agreed at that date); from 2027-01-01 at least OR differs (OI-105: ISO's 2027 Oregon base rate 0.125).

    python scripts/cf/242_chunk27_c27-13_editions.py [--states OR,CA] [--dates 2026-09-17,2027-01-01]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))
sys.stdout.reconfigure(line_buffering=True, encoding="utf-8")
T0 = time.monotonic()

c4 = import_module("237_chunk26_rc4")
r2 = import_module("239_chunk27_rc2")
r3m = import_module("240_chunk27_rc3")
t2, gc = c4.t2, c4.gc
from cf_engine.resolve import CFEditionResolver, book_for

DATES = ["2026-09-17", "2026-11-01", "2027-01-01", "2027-04-01", "2027-07-01", "2027-10-01"]
OUT = gc.OUT / "chunk27_c27-13_editions.json"
PKG = re.compile(r"CF ([A-Z]{2}) (\d{8}) (V\d\d)")


def progress(i, n, what):
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{i}/{n}  {mm}m{s:02d}s] {what}")


def ours(j, date, res):
    b = book_for(j, date.replace("-", ""), resolver=res)
    m = re.search(r"CF_([A-Z]{2})_(\d{8})_(V\d\d)", str(b))
    return f"CF {m.group(1)} {m.group(2)} {m.group(3)}" if m else str(b)


def iso(client, raas_mod, req):
    try:
        resp = r2.rate_retry(client, req)
        hdr = resp.get("Header") or resp.get("header") or {}
        m = PKG.search(str(hdr.get("Scheme", "")))
        return (m.group(0) if m else f"? {hdr}"), "rated"
    except raas_mod.RaaSError as exc:
        body = str(exc.body)
        m = re.search(r"Project: (CF [A-Z]{2} \d{8} V\d\d)", body) or PKG.search(body)
        return (m.group(1) if m and m.groups() else (m.group(0) if m else "?")), "refused: " + body[body.find("Message"):][:160]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--states")
    ap.add_argument("--dates")
    a = ap.parse_args()
    res = CFEditionResolver()
    states = a.states.split(",") if a.states else [j for j in sorted(res.jurisdictions) if j != "PR"]
    dates = a.dates.split(",") if a.dates else DATES
    import raas as raas_mod
    client = raas_mod.RaaS()
    rows = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    n, i = len(states) * len(dates), 0
    for j in states:
        # a single building (240_'s) first: ISO names its package even when it refuses that request (0.5 s against 14 s);
        # the full portable policy only when a refusal does not name this state's own package
        small = t2.state_req(t2.m20.payload(r3m.ll(j, legal=False)()), j)
        big = None
        for d in dates:
            i += 1
            req = json.loads(json.dumps(small))
            req["body"]["SchemeKeys"]["EffectiveDateTime"] = f"{d}T00:00:00"
            got, how = iso(client, raas_mod, req)
            if not got.startswith(f"CF {j} "):
                big = big or t2.state_req(t2.m20.payload(c4.state_policy(j)()), j)
                req = json.loads(json.dumps(big))
                req["body"]["SchemeKeys"]["EffectiveDateTime"] = f"{d}T00:00:00"
                got, how = iso(client, raas_mod, req)
            mine = ours(j, d, res)
            rows.setdefault(j, {})[d] = {"iso": got, "ours": mine, "how": how}
            progress(i, n, f"{j} {d}: ISO {got} ({how[:40]}); ours {mine}  {'same' if got == mine else 'DIFFERS'}")
        OUT.write_text(json.dumps(rows, indent=1), encoding="utf-8")
    print("\nWhere ISO's package differs from the corpus's:")
    diff = 0
    for j in sorted(rows):
        bad = [(d, v["iso"], v["ours"]) for d, v in sorted(rows[j].items()) if v["iso"] != v["ours"]]
        if bad:
            diff += 1
            print(f"  {j}: " + "; ".join(f"{d} ISO {x} / ours {y}" for d, x, y in bad))
    same0917 = sum(1 for j in rows if rows[j].get("2026-09-17", {}).get("iso") == rows[j].get("2026-09-17", {}).get("ours"))
    print(f"\nat 2026-09-17: {same0917} of {len(rows)} states name the same package; states differing on some date: {diff}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
