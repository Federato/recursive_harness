#!/usr/bin/env python3
"""Chunk 27 C27-14 and C27-15: the evidence for OI-106, OI-116 and OI-114, reproducible. (OI-112's probe is 243_.)

  --oi106   offline: which in-force states file their own `Form Pages/Pages.FormPage.csv` (our engine then uses it
            wholesale and misses every countrywide form row), and, on the saved ISO pairs of chunk 27 RC-3 / RC-4, how
            many `ErcFormName` ISO resolves against ours ("Value Not Found")
  --oi116   live: FC5 (chunk 21) re-sent with the special class's own `PolicyType` as sent / removed / "Standard Property
            Policy": does ISO keep the CP 17 96 special-class condo record? (2026-10-02: no, in all three)
  --oi114   offline: every state x month from 2019-12 to 2026-09 whose resolved book (state package or its countrywide
            parent) is one of the five packages carrying `<rul:Null/>`: the windows in force, per package

    python scripts/cf/244_chunk27_c27-14_15_evidence.py [--oi106] [--oi116] [--oi114]
"""
from __future__ import annotations

import argparse
import copy
import glob
import json
import re
import sys
from importlib import import_module
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "cf"))
sys.stdout.reconfigure(line_buffering=True, encoding="utf-8")

from cf_engine.resolve import CFEditionResolver, book_for
from gl_engine.errors import EngineError

NULL_PKGS = {"CF_CW_20191201_V01", "CF_CW_20201201_V01", "CF_FL_20191201_V01", "CF_NC_20230801_V01", "CF_NC_20240201_V01"}
SPP_REC = "CommercialPropertyChangesCommercialUnitsInResidentialCondosIncludingOptionForAddlCoveredPropertySPPSpecClass"


def walk(n):
    yield n
    for c in n.children:
        yield from walk(c)


def oi106():
    res = CFEditionResolver()
    own = {}
    for j in sorted(res.jurisdictions):
        b = book_for(j, "20260917", resolver=res)
        f = Path(b.state.package.content) / "Form Pages" / "Pages.FormPage.csv"
        cw = Path(b.parent.package.content) / "Form Pages" / "Pages.FormPage.csv"
        if f.exists():
            own[j] = (sum(1 for _ in open(f, encoding="utf-8-sig")) - 1, sum(1 for _ in open(cw, encoding="utf-8-sig")) - 1)
    print(f"OI-106: {len(own)} of {len(res.jurisdictions)} in-force states file their own Pages table "
          f"(rows {min(v[0] for v in own.values())}..{max(v[0] for v in own.values())} against countrywide's "
          f"{min(v[1] for v in own.values())}..{max(v[1] for v in own.values())})")
    r2 = import_module("239_chunk27_rc2")
    tot = [0, 0, 0, 0]
    for f in sorted(glob.glob(str(r2.gc.OUT / "chunk27_rc3_*_response.json")) + glob.glob(str(r2.gc.OUT / "chunk27_rc4_*_response.json"))):
        resp = json.load(open(f, encoding="utf-8"))
        req = json.load(open(f.replace("_response", "_request"), encoding="utf-8"))
        s = json.dumps(resp)
        data, ip = r2.rep.cmp.rate(req)
        ours = [n.text for n in walk(data) if n.tag == "ErcFormName"]
        tot[0] += 1
        tot[1] += len(re.findall(r'"ErcFormName":', s))
        tot[2] += s.count('"ErcFormName": "Value Not Found"')
        tot[3] += sum(1 for x in ours if x == "Value Not Found")
    print(f"  on {tot[0]} saved ISO responses: {tot[1]} form names, ISO 'Value Not Found' {tot[2]}, ours {tot[3]}")


def oi116():
    import raas
    r2 = import_module("239_chunk27_rc2")
    base = json.load(open(r2.gc.OUT / "chunk21_rc2_FC5_request.json", encoding="utf-8"))
    client = raas.RaaS()
    for name, fn in (("as sent", lambda sc: None), ("special class PolicyType removed", lambda sc: sc.pop("PolicyType", None)),
                     ("special class PolicyType SPP", lambda sc: sc.__setitem__("PolicyType", "Standard Property Policy"))):
        req = copy.deepcopy(base)
        cp = req["body"]["CommercialProperty"]
        for loc in (cp[0] if isinstance(cp, list) else cp)["CommercialPropertyLocation"]:
            for sc in loc.get("CommercialPropertySpecialClass", []):
                fn(sc)
        resp = r2.rate_retry(client, req)
        print(f"OI-116 {name}: record sent {SPP_REC in json.dumps(req)}, ISO keeps it {SPP_REC in json.dumps(resp)}")


def oi114():
    res = CFEditionResolver()
    hits = {}
    for y in range(2019, 2027):
        for mth in range(1, 13):
            d = f"{y}{mth:02d}01"
            if d < "20191201" or d > "20260901":
                continue
            for j in sorted(res.jurisdictions):
                try:
                    b = str(book_for(j, d, resolver=res))
                except EngineError:
                    continue
                for p in NULL_PKGS:
                    if p in b:
                        hits.setdefault(p, {}).setdefault(j, []).append(d)
    print("OI-114: where the <rul:Null/> packages are in force (state x first-of-month, 2019-12..2026-09):")
    for p in sorted(NULL_PKGS):
        st = hits.get(p, {})
        if not st:
            print(f"  {p}: never resolved")
            continue
        lo = min(min(v) for v in st.values())
        hi = max(max(v) for v in st.values())
        print(f"  {p}: {len(st)} state(s), {lo}..{hi}  ({', '.join(sorted(st))})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--oi106", action="store_true")
    ap.add_argument("--oi116", action="store_true")
    ap.add_argument("--oi114", action="store_true")
    a = ap.parse_args()
    if a.oi106:
        oi106()
    if a.oi116:
        oi116()
    if a.oi114:
        oi114()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
