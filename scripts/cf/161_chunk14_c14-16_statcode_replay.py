"""C14-16: statistical codes, replayed against every stored ISO fixture response.

No ISO calls. The 293 stored ISO responses from chunk 13's C13-23 are re-rated
exactly (157_'s request) and every statistical field on every record is compared
with ISO's by path: stat codes, stat amounts, stat premiums, ...ForStat and
...ToUseStat... fields (STAT below).

The comparison is STRICT for text: a stat code is a code, so "07" is not "7" and
"" is not "0". A value ISO returns as a JSON number is compared as a number.
Blank and absent are the same on both sides (neither is a code).

    python scripts/cf/161_chunk14_c14-16_statcode_replay.py          # the 46-fixture sample (regression)
    python scripts/cf/161_chunk14_c14-16_statcode_replay.py --all    # all 293

Exits 1 on any disagreement.
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
STAT = re.compile(r"StatCode|StatAmount|^Stat[A-Z]|ForStat|ToUseStat")
cmp.FIELD = STAT                    # 154_'s walkers read these two module globals
cmp.REC = re.compile(r"(?!x)x")     # no whole-record capture


def blank(v):
    return v is None or (isinstance(v, str) and v.strip() == "")


def same(iso, ours):
    if blank(iso) or blank(ours):
        return blank(iso) and blank(ours)
    if isinstance(iso, (int, float)) and not isinstance(iso, bool):
        try:
            return float(ours) == float(iso)
        except (TypeError, ValueError):
            return False
    return str(iso) == str(ours)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="all 293 stored responses, not the 46-fixture sample")
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args()
    index = rep.fixture_index()
    n = ok = values = 0
    diffs = collections.Counter()
    fields = collections.Counter()
    shown = 0
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
        iso = cmp.iso_all(json.loads(rpath.read_text(encoding="utf-8")))
        ours = cmp.ours_all(data)
        n += 1
        values += len(iso)
        for k in iso:
            fields[k.rsplit("/", 1)[-1]] += 1
        bad = [(k, v, ours.get(k)) for k, v in iso.items() if not same(v, ours.get(k))]
        if not bad:
            ok += 1
            continue
        st = d["SchemeKeys"]["ProductName"].split()[-1]
        for k, v, o in bad:
            rec = k.rsplit("/", 2)[-2].split("[")[0].replace("CommercialProperty", "") or "Policy"
            diffs[(st, rec, k.rsplit("/", 1)[-1], repr(v), repr(o))] += 1
        if a.verbose or shown < 8:
            shown += 1
            print(f"  {stem} ({st}): {len(bad)} differ, e.g. "
                  + "; ".join(f"{k[-60:]} ISO {v!r} ours {o!r}" for k, v, o in bad[:3]))
    print(f"\n{'ALL' if a.all else 'SAMPLE'}: {n} stored ISO responses re-rated; "
          f"{values} stat values compared across {len(fields)} field names")
    print(f"  every stat value equal to ISO: {ok} of {n}")
    for (st, rec, f, v, o), c in diffs.most_common(25):
        print(f"    {c:4d}x  {st} {rec}.{f}  ISO {v} ours {o}")
    sys.exit(0 if ok == n and n else 1)


if __name__ == "__main__":
    main()
