"""C14-20 (gate 6): the modifier fields are shared names -- the same field on the policy
and on every structure (and some coverage records), and the values may differ by
design (a building's own PackageModFactor beats the policy's; a vacant building takes
1.0). So each is compared BY PATH, on every record that carries it, against the 293
stored ISO responses. No ISO calls.

    python scripts/cf/165_chunk14_c14-20_shared_modifiers.py [--all]
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))

from gl_engine.interp.values import InterpretError

rep = import_module("157_chunk14_c14-02_total_replay")
cmp = rep.cmp
cmp.FIELD = re.compile(r"^(IRPMFactor|CPPIRPMFactor|PackageModFactor|MultiPremiumAndDispersionCreditFactor(User)?|"
                       r"StdPropPol\w*Factor|TotalRatingModificationRate|TotalModificationPct|MultiLocAvgRates|"
                       r"IRPMMaximum|IRPMMinimum)$")
cmp.REC = re.compile(r"(?!x)x")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    index = rep.fixture_index()
    n = ok = values = 0
    per_field = collections.Counter()
    recs = collections.defaultdict(set)
    diffs = collections.Counter()
    for rpath in sorted(rep.RES.glob("chunk13_fixture_*_response.json")):
        stem = rpath.name[len("chunk13_fixture_"):-len("_response.json")]
        if not a.all and stem not in rep.SAMPLE:
            continue
        fx = index.get(stem)
        if fx is None:
            continue
        d = json.loads(fx.read_text(encoding="utf-8-sig"))
        req = {"header": {}, "body": {"SchemeKeys": {"ProductName": d["SchemeKeys"]["ProductName"],
                                                     "EffectiveDateTime": "2026-09-17T00:00:00"},
                                      "CommercialProperty": d["CommercialProperty"]}}
        try:
            data, ip = cmp.rate(req)
        except InterpretError as exc:
            print(f"  {stem}: ENGINE RAISED {str(exc)[:90]}")
            continue
        iso, ours = cmp.iso_all(json.loads(rpath.read_text(encoding="utf-8"))), cmp.ours_all(data)
        n += 1
        values += len(iso)
        for k in iso:
            f = k.rsplit("/", 1)[-1]
            per_field[f] += 1
            recs[f].add(k.rsplit("/", 2)[-2].split("[")[0].replace("CommercialProperty", "") or "Policy")
        bad = [(k, v, ours.get(k)) for k, v in iso.items() if not cmp.same(v, ours.get(k))]
        ok += not bad
        for k, v, o in bad:
            diffs[(k.rsplit("/", 1)[-1], repr(v), repr(o))] += 1
    print(f"{'ALL' if a.all else 'SAMPLE'}: {n} stored ISO responses; {values} modifier values compared by path")
    for f, c in per_field.most_common():
        print(f"  {c:5d}  {f}  on {len(recs[f])} record type(s): {', '.join(sorted(recs[f]))[:110]}")
    print(f"  every modifier value equal to ISO: {ok} of {n}")
    for (f, v, o), c in diffs.most_common(15):
        print(f"    {c:4d}x  {f}  ISO {v} ours {o}")
    sys.exit(0 if ok == n and n else 1)


if __name__ == "__main__":
    main()
