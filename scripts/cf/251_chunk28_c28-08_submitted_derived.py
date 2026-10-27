#!/usr/bin/env python3
"""Chunk 28 C28-08 (set C): OI-125, does a submitted value stand in for a field the rules overwrite? No engine change.

OI-125 (chunk 26 K4c / K4d): `Structure.SetOccupantCounts` counts occupancies whose own `RatingType` is "Class"; that
field is copied from the building (`OccupClass.SetRatingType`, unguarded) only later in the run. Nothing submitted: the
count is 0 at ISO and ours. `RatingType` submitted "Class" on the occupancies: ours counts 2 and raises "Only one
Apartment without Mercantile Occupancy record is allowed per building"; ISO counts 0. Readings:
  now  a submitted value is read as is until a rule overwrites it (ours)
  R1   a submitted value for a field a rule later OVERWRITES is not read at all: ISO behaves as if it was never sent
       (a submitted value a rule never overwrites, e.g. one behind an IsNull guard, is read as today)
(The ordering reading, "ISO copies the rating type before counting", is already refuted: K4c would then count 2.)

R1 is measured exactly, in two passes per stored request ISO rated: pass 1 rates as today and records every submitted
leaf a rule write overwrites; pass 2 rates again with exactly those leaves hidden from reads until a rule writes them.
Each request's (level, message) multiset and premiums are compared with ISO's response. Predicted before the run
(2026-10-05): R1 turns K4d equal and breaks nothing; the requests it touches at all are few, and are the probes.

    python scripts/cf/251_chunk28_c28-08_submitted_derived.py [--only chunk26]
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
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

from gl_engine.interp import tree                                        # noqa: E402

c23 = import_module("221_chunk23_rc3")
rep, TAGGED, lvl, OUT = c23.rep, c23.TAGGED, c23.lvl, c23.gc.OUT

ORIG_WRITE, ORIG_READ = tree.write, tree.read
MODE = {"pass": None, "submitted": None, "over": set(), "strip": set(), "written": set()}


def path_of(n):
    parts = []
    while n is not None and n.parent is not None:
        same = [c for c in n.parent.children if c.tag == n.tag]
        parts.append(f"{n.tag}[{same.index(n)}]")
        n = n.parent
    return "/".join(reversed(parts))


def leaves(n):
    if not n.children:
        if n.text not in (None, ""):
            yield n
    for c in n.children:
        yield from leaves(c)


def write(path, context, value):
    n = tree.select_one(path, context)
    if n is not None:
        p = path_of(n)
        if MODE["pass"] == 1 and p in MODE["submitted"] and p not in MODE["written"] and n.text not in (None, ""):
            MODE["over"].add(p)                      # a submitted value a rule writes over (with any value)
        MODE["written"].add(p)
        return ORIG_WRITE(path, context, value)
    m = ORIG_WRITE(path, context, value)
    MODE["written"].add(path_of(m))
    return m


def read(path, context):
    if MODE["pass"] == 2:
        n = tree.select_one(path, context)
        if n is not None:
            p = path_of(n)
            if p in MODE["strip"] and p not in MODE["written"]:
                return None                           # R1: never sent
    return ORIG_READ(path, context)


tree.write, tree.read = write, read
_from_dict = tree.Node.from_dict


def from_dict(tag, d):
    root = _from_dict(tag, d)
    if MODE["pass"] in (1, 2):
        MODE["submitted"] = {path_of(x) for x in leaves(root)}
        MODE["written"] = set()
    return root


tree.Node.from_dict = staticmethod(from_dict)


def ours(req, p, strip=frozenset()):
    MODE.update({"pass": p, "over": set(), "strip": set(strip)})
    TAGGED.clear()
    try:
        data, ip = rep.cmp.rate(req)
        return collections.Counter((lvl(t), x) for t, x in TAGGED), rep.our_prem(data), set(MODE["over"])
    finally:
        MODE["pass"] = None


def progress(i, n, what):
    mm, s = divmod(int(time.monotonic() - T0), 60)
    print(f"[{i}/{n}  {mm}m{s:02d}s] {what}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only")
    a = ap.parse_args()
    reqs = sorted(f for f in glob.glob(str(OUT / "*_request.json"))
                  if Path(f[:-len("_request.json")] + "_response.json").exists() and (not a.only or a.only in Path(f).name))
    n_eq = collections.Counter()
    touched, fixed, broke, moved, raised, fields = [], [], [], [], [], collections.Counter()
    for i, f in enumerate(reqs, 1):
        name = Path(f).name[:-len("_request.json")]
        req = json.loads(Path(f).read_text(encoding="utf-8"))
        resp = json.loads(Path(f[:-len("_request.json")] + "_response.json").read_text(encoding="utf-8"))
        isos, ipr = collections.Counter(c23.iso_tagged(resp)), rep.iso_prem(resp)
        try:
            m1, p1, over = ours(req, 1)
        except Exception as exc:                      # noqa: BLE001
            raised.append((name, "now", f"{type(exc).__name__}: {str(exc)[:70]}"))
            continue
        n_eq["now"] += m1 == isos
        if not over:
            n_eq["R1"] += m1 == isos
            continue
        touched.append((name, sorted({p.rsplit("/", 1)[-1].split("[")[0] for p in over})))
        for p in over:
            fields[p.rsplit("/", 1)[-1].split("[")[0]] += 1
        try:
            m2, p2, _ = ours(req, 2, over)
        except Exception as exc:                      # noqa: BLE001
            raised.append((name, "R1", f"{type(exc).__name__}: {str(exc)[:70]}"))
            continue
        n_eq["R1"] += m2 == isos
        if m2 == isos and m1 != isos:
            fixed.append(name)
        if m1 == isos and m2 != isos:
            broke.append((name, sorted((m2 - isos).elements())[:2], sorted((isos - m2).elements())[:2]))
        dp = [k for k in ipr if not rep.cmp.same(p1.get(k), p2.get(k))]
        if dp:
            iso_side = sum(rep.cmp.same(ipr[k], p2.get(k)) for k in dp)
            moved.append((name, len(dp), f"{iso_side} of {len(dp)} moved TO ISO's figure"))
        if i % 200 == 0 or i == len(reqs):
            progress(i, len(reqs), f"touched {len(touched)}; equal now {n_eq['now']} R1 {n_eq['R1']}")
    print(f"\n{len(reqs)} stored requests ISO rated; {len(touched)} submit a value a rule later overwrites")
    print(f"  (level, message) equal to ISO: now {n_eq['now']}, R1 {n_eq['R1']}; fixed {len(fixed)}, broke {len(broke)}; "
          f"premiums moved on {len(moved)}; raised {len(raised)}")
    print("  overwritten submitted fields:", fields.most_common(25))
    for k, lst in (("fixed", fixed), ("broke", broke), ("moved", moved), ("touched", touched[:30]), ("raised", raised)):
        for x in lst:
            print(f"    {k:7s} {x}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
