"""Chunk 13, C13-23: every ISO STC fixture that elects terrorism, engine against ISO live.

354 of ISO's 364 CF STC payloads set `TerrorismIndicator` Yes. Each is converted
to an engine submission (`to_engine`, with rule-addressed singletons unwrapped as
in C13-03), rated at 2026-09-17 (OI-105), and sent to ISO unchanged at the same
date. Every terrorism field on every record (154_'s comparer: premiums, rates,
factors, limits, stat codes; form names set aside as OI-106) and the message set
are compared. STC fixtures are 2019-2023 data rated at 2026, so ISO refuses some
on lookups that have since lost their rows; those are counted, not compared.

    python scripts/cf/155_chunk13_c13-23_fixtures.py [--limit N]
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
sys.path.insert(0, str(ROOT / "scripts"))

from gl_engine.interp.values import InterpretError

cmp = import_module("154_chunk13_rc5_fields_messages")
gc, rp = cmp.gc, cmp.rp
ISO_CF = Path("C:/Projects/ISO_ERC_Files/CF")
EFFECTIVE = "2026-09-17T00:00:00"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    import raas as raas_mod
    client = raas_mod.RaaS()
    fixtures = [p for p in sorted(ISO_CF.rglob("STC/*.json"))
                if re.search(r'"TerrorismIndicator"\s*:\s*"Yes"', p.read_text(encoding="utf-8-sig", errors="replace"))]
    if a.limit:
        fixtures = fixtures[:a.limit]
    t = collections.Counter()
    refusals = collections.Counter()
    diffs = collections.Counter()
    nonzero = 0
    for p in fixtures:
        d = json.loads(p.read_text(encoding="utf-8-sig"))
        req = {"header": {"quoteback": "", "authorization": {}},
               "body": {"SchemeKeys": {"ProductName": d["SchemeKeys"]["ProductName"], "EffectiveDateTime": EFFECTIVE},
                        "CommercialProperty": d["CommercialProperty"]}}
        try:
            data, ip = cmp.rate(req)
        except InterpretError as exc:
            t["engine refuses"] += 1
            continue
        try:
            resp = client.rate(req)
        except raas_mod.RaaSError as exc:
            body = str(exc.body)
            m = re.search(r"Matrix: (\w+)", body)
            refusals[m.group(1) if m else body[60:140]] += 1
            t["ISO refuses"] += 1
            continue
        (gc.OUT / f"chunk13_fixture_{p.stem}_response.json").write_text(json.dumps(resp), encoding="utf-8")
        ours, iso = cmp.ours_all(data), cmp.iso_all(resp)
        dd = [(k, v, ours.get(k)) for k, v in iso.items()
              if k.rsplit("/", 1)[-1] not in cmp.OI106 and not cmp.same(v, ours.get(k))]
        if any((rp.num(v) or 0) > 0 for k, v in iso.items() if k.endswith("TerrorismPremium")):
            nonzero += 1
        if dd:
            t["terrorism fields DIFFER"] += 1
            for k, v, o in dd[:3]:
                diffs[(k.rsplit("/", 1)[-1], str(v), str(o))] += 1
            print(f"  {p.name}: " + "; ".join(f"{k[-60:]} ISO {v} ours {o}" for k, v, o in dd[:3]))
        else:
            t["terrorism fields agree"] += 1
        mo, mi = set(ip.messages), cmp.iso_messages(resp)
        if mo == mi:
            t["messages identical"] += 1
        else:
            t["messages differ"] += 1
            print(f"  {p.name} ({d['SchemeKeys']['ProductName'].split()[-1]}) MESSAGES ours-only {sorted(mo - mi)} "
                  f"ISO-only {sorted(mi - mo)}")
    print(f"\n{len(fixtures)} fixtures electing terrorism: {dict(t)}")
    print(f"  ISO rated {t['terrorism fields agree'] + t['terrorism fields DIFFER']}; "
          f"{nonzero} of them carry a non-zero terrorism premium")
    print(f"  ISO refusals by lookup: {dict(refusals.most_common(8))}")
    for (f, v, o), c in diffs.most_common(10):
        print(f"    {c:4d}x {f}: ISO {v} ours {o}")
    sys.exit(1 if t["terrorism fields DIFFER"] or t["engine refuses"] else 0)


if __name__ == "__main__":
    main()
